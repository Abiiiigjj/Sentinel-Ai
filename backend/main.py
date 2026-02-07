"""
SentinelAI Backend - DSGVO-Compliant Local LLM System
Main FastAPI Application
"""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.llm_service import LLMService
from services.document_service import DocumentService
from services.vector_store import VectorStoreService
from services.pii_service import PIIService
from services.audit_service import AuditService
from utils.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
llm_service: Optional[LLMService] = None
document_service: Optional[DocumentService] = None
vector_store: Optional[VectorStoreService] = None
pii_service: Optional[PIIService] = None
audit_service: Optional[AuditService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - initialize and cleanup services."""
    global llm_service, document_service, vector_store, pii_service, audit_service
    
    logger.info("🚀 Initializing SentinelAI Backend...")
    
    # Initialize services
    audit_service = AuditService(data_dir=settings.DATA_DIR)
    await audit_service.log("system", "startup", "SentinelAI Backend starting")
    
    pii_service = PIIService()
    vector_store = VectorStoreService(persist_dir=settings.VECTOR_STORE_DIR)
    llm_service = LLMService(
        ollama_host=settings.OLLAMA_HOST,
        model_name=settings.LLM_MODEL,
        embedding_model=settings.EMBEDDING_MODEL
    )
    document_service = DocumentService(
        vector_store=vector_store,
        pii_service=pii_service,
        llm_service=llm_service,
        audit_service=audit_service
    )
    
    # Check Ollama connection
    if await llm_service.health_check():
        logger.info(f"✅ Connected to Ollama ({settings.LLM_MODEL})")
    else:
        logger.warning("⚠️ Ollama not available - LLM features disabled")
    
    logger.info("✅ SentinelAI Backend ready")
    
    yield
    
    # Cleanup
    await audit_service.log("system", "shutdown", "SentinelAI Backend stopping")
    logger.info("👋 SentinelAI Backend shutdown complete")


app = FastAPI(
    title="SentinelAI",
    description="DSGVO-compliant Local LLM System with RAG",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== MODELS ==============

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    use_rag: bool = True
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: list[dict] = []
    metadata: dict = {}


class DocumentResponse(BaseModel):
    id: str
    filename: str
    uploaded_at: datetime
    chunk_count: int
    pii_detected: bool
    pii_summary: Optional[str] = None


class ComplianceStats(BaseModel):
    total_documents: int
    total_chunks: int
    pii_documents: int
    audit_entries: int
    last_activity: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    model_loaded: bool
    vector_store_ready: bool
    timestamp: datetime


# ============== ENDPOINTS ==============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    ollama_ok = await llm_service.health_check() if llm_service else False
    
    return HealthResponse(
        status="healthy" if ollama_ok else "degraded",
        ollama_connected=ollama_ok,
        model_loaded=ollama_ok,
        vector_store_ready=vector_store is not None,
        timestamp=datetime.utcnow()
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with optional RAG augmentation."""
    if not llm_service:
        raise HTTPException(503, "LLM service not available")
    
    await audit_service.log(
        user_id=request.session_id or "anonymous",
        action="chat",
        details=f"Query: {request.messages[-1].content[:100]}..."
    )
    
    # Get context from vector store if RAG enabled
    context_docs = []
    if request.use_rag and vector_store:
        query = request.messages[-1].content
        context_docs = await vector_store.search(query, k=5)
    
    # Build context-augmented prompt
    messages = [msg.model_dump() for msg in request.messages]
    
    if context_docs:
        context_text = "\n\n".join([
            f"[Dokument: {doc['metadata'].get('filename', 'unbekannt')}]\n{doc['content']}"
            for doc in context_docs
        ])
        system_msg = {
            "role": "system",
            "content": f"""Du bist Sentinell, ein sicherer, datenschutzkonformer KI-Assistent.
Nutze folgende Dokumente als Kontext für deine Antwort:

{context_text}

Antworte präzise und professionell auf Deutsch. Verweise auf die Quellen wenn relevant."""
        }
        messages.insert(0, system_msg)
    
    # Generate response
    response = await llm_service.chat(messages)
    
    return ChatResponse(
        response=response,
        sources=[{"filename": doc["metadata"].get("filename"), "chunk_id": doc["id"]} 
                 for doc in context_docs],
        metadata={
            "model": settings.LLM_MODEL,
            "rag_enabled": request.use_rag,
            "context_chunks": len(context_docs)
        }
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint for real-time responses."""
    if not llm_service:
        raise HTTPException(503, "LLM service not available")
    
    await audit_service.log(
        user_id=request.session_id or "anonymous",
        action="chat_stream",
        details=f"Query: {request.messages[-1].content[:100]}..."
    )
    
    # Get context
    context_docs = []
    if request.use_rag and vector_store:
        query = request.messages[-1].content
        context_docs = await vector_store.search(query, k=5)
    
    messages = [msg.model_dump() for msg in request.messages]
    
    if context_docs:
        context_text = "\n\n".join([
            f"[Dokument: {doc['metadata'].get('filename', 'unbekannt')}]\n{doc['content']}"
            for doc in context_docs
        ])
        system_msg = {
            "role": "system",
            "content": f"""Du bist Sentinell, ein sicherer, datenschutzkonformer KI-Assistent.
Nutze folgende Dokumente als Kontext:

{context_text}

Antworte präzise und professionell auf Deutsch."""
        }
        messages.insert(0, system_msg)
    
    async def generate():
        async for chunk in llm_service.chat_stream(messages):
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload and process a document."""
    if not document_service:
        raise HTTPException(503, "Document service not available")
    
    # Validate file type
    allowed_types = {".pdf", ".docx", ".doc", ".txt", ".md"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(400, f"Unsupported file type. Allowed: {allowed_types}")
    
    # Process document
    content = await file.read()
    result = await document_service.process_document(
        filename=file.filename,
        content=content,
        file_type=file_ext
    )
    
    await audit_service.log(
        user_id="system",
        action="document_upload",
        details=f"Uploaded: {file.filename}, Chunks: {result['chunk_count']}, PII: {result['pii_detected']}"
    )
    
    return DocumentResponse(
        id=result["id"],
        filename=file.filename,
        uploaded_at=datetime.utcnow(),
        chunk_count=result["chunk_count"],
        pii_detected=result["pii_detected"],
        pii_summary=result.get("pii_summary")
    )


@app.get("/documents", response_model=list[DocumentResponse])
async def list_documents():
    """List all processed documents."""
    if not document_service:
        raise HTTPException(503, "Document service not available")
    
    docs = await document_service.list_documents()
    return [DocumentResponse(**doc) for doc in docs]


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks (DSGVO: Right to erasure)."""
    if not document_service:
        raise HTTPException(503, "Document service not available")
    
    success = await document_service.delete_document(document_id)
    if not success:
        raise HTTPException(404, "Document not found")
    
    await audit_service.log(
        user_id="system",
        action="document_delete",
        details=f"Deleted document: {document_id}"
    )
    
    return {"status": "deleted", "document_id": document_id}


@app.get("/compliance/stats", response_model=ComplianceStats)
async def get_compliance_stats():
    """Get compliance statistics for dashboard."""
    doc_stats = await document_service.get_stats() if document_service else {}
    audit_stats = await audit_service.get_stats() if audit_service else {}
    
    return ComplianceStats(
        total_documents=doc_stats.get("total_documents", 0),
        total_chunks=doc_stats.get("total_chunks", 0),
        pii_documents=doc_stats.get("pii_documents", 0),
        audit_entries=audit_stats.get("total_entries", 0),
        last_activity=audit_stats.get("last_activity")
    )


@app.get("/compliance/audit")
async def get_audit_log(limit: int = 100, offset: int = 0):
    """Get audit log entries for compliance review."""
    if not audit_service:
        raise HTTPException(503, "Audit service not available")
    
    entries = await audit_service.get_entries(limit=limit, offset=offset)
    return {"entries": entries, "limit": limit, "offset": offset}


@app.delete("/compliance/user-data/{user_id}")
async def delete_user_data(user_id: str):
    """Delete all data associated with a user (DSGVO: Right to erasure)."""
    await audit_service.log(
        user_id="admin",
        action="gdpr_erasure",
        details=f"Initiating data deletion for user: {user_id}"
    )
    
    # In a real implementation, this would delete all user-associated data
    # For now, we log the request
    
    return {"status": "deletion_initiated", "user_id": user_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
