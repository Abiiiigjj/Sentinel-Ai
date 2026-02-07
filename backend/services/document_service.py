"""
Document Service - Document Processing Pipeline
Handles document upload, parsing, chunking, PII detection, and vector storage
"""
import hashlib
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from io import BytesIO
import uuid

logger = logging.getLogger(__name__)

# Try to import document processing libraries
try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("pypdf not available. PDF processing disabled.")

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available. DOCX processing disabled.")


class DocumentService:
    """Service for document processing and management."""
    
    def __init__(
        self,
        vector_store,
        pii_service,
        llm_service,
        audit_service,
        documents_dir: str | Path = "./data/documents",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        self.vector_store = vector_store
        self.pii_service = pii_service
        self.llm_service = llm_service
        self.audit_service = audit_service
        
        self.documents_dir = Path(documents_dir)
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Document metadata storage (SQLite or JSON file)
        self.metadata_file = self.documents_dir / "documents.json"
        self.documents_metadata = self._load_metadata()
        
        logger.info(f"Document service initialized. {len(self.documents_metadata)} documents indexed.")
    
    def _load_metadata(self) -> dict:
        """Load document metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save document metadata to file."""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.documents_metadata, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    async def process_document(
        self,
        filename: str,
        content: bytes,
        file_type: str,
        user_id: str = "system"
    ) -> dict:
        """
        Process an uploaded document through the full pipeline.
        
        Args:
            filename: Original filename
            content: File content as bytes
            file_type: File extension (e.g., '.pdf')
            user_id: ID of uploading user
            
        Returns:
            Processing result with document ID and stats
        """
        document_id = str(uuid.uuid4())
        
        logger.info(f"Processing document: {filename} (ID: {document_id})")
        
        # 1. Extract text from document
        text = await self._extract_text(content, file_type)
        if not text:
            raise ValueError(f"Could not extract text from {filename}")
        
        logger.info(f"Extracted {len(text)} characters from {filename}")
        
        # 2. Split into chunks
        chunks = self._chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks")
        
        # 3. PII detection and masking
        pii_detected = False
        pii_summary = None
        masked_chunks = []
        
        for chunk in chunks:
            pii_result = self.pii_service.detect_pii(chunk, mask=True)
            masked_chunks.append(pii_result.masked_text)
            if pii_result.pii_detected:
                pii_detected = True
        
        if pii_detected:
            pii_results = self.pii_service.detect_in_chunks(chunks)
            pii_stats = self.pii_service.get_pii_stats(pii_results)
            pii_summary = f"Gefunden: {json.dumps(pii_stats['type_distribution'], ensure_ascii=False)}"
            logger.info(f"PII detected in {filename}: {pii_summary}")
        
        # 4. Generate embeddings for masked chunks
        embeddings = await self.llm_service.generate_embeddings_batch(masked_chunks)
        
        # 5. Store in vector database
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(masked_chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": i,
                "total_chunks": len(masked_chunks),
                "pii_masked": pii_detected,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            for i in range(len(masked_chunks))
        ]
        
        await self.vector_store.add_documents(
            documents=masked_chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=chunk_ids
        )
        
        # 6. Save document metadata
        self.documents_metadata[document_id] = {
            "id": document_id,
            "filename": filename,
            "file_type": file_type,
            "uploaded_at": datetime.utcnow().isoformat(),
            "chunk_count": len(chunks),
            "character_count": len(text),
            "pii_detected": pii_detected,
            "pii_summary": pii_summary,
            "user_id": user_id
        }
        self._save_metadata()
        
        # 7. Audit log
        await self.audit_service.log(
            user_id=user_id,
            action="document_processed",
            details=f"Document '{filename}' processed: {len(chunks)} chunks, PII: {pii_detected}",
            metadata={
                "document_id": document_id,
                "chunks": len(chunks),
                "pii_detected": pii_detected
            }
        )
        
        return {
            "id": document_id,
            "filename": filename,
            "chunk_count": len(chunks),
            "pii_detected": pii_detected,
            "pii_summary": pii_summary
        }
    
    async def _extract_text(self, content: bytes, file_type: str) -> Optional[str]:
        """Extract text from document based on file type."""
        file_type = file_type.lower()
        
        if file_type == ".pdf":
            return self._extract_pdf(content)
        elif file_type in [".docx", ".doc"]:
            return self._extract_docx(content)
        elif file_type in [".txt", ".md"]:
            return content.decode("utf-8", errors="ignore")
        else:
            logger.warning(f"Unsupported file type: {file_type}")
            return None
    
    def _extract_pdf(self, content: bytes) -> Optional[str]:
        """Extract text from PDF."""
        if not PDF_AVAILABLE:
            logger.error("PDF extraction not available")
            return None
        
        try:
            reader = PdfReader(BytesIO(content))
            text_parts = []
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return None
    
    def _extract_docx(self, content: bytes) -> Optional[str]:
        """Extract text from DOCX."""
        if not DOCX_AVAILABLE:
            logger.error("DOCX extraction not available")
            return None
        
        try:
            doc = DocxDocument(BytesIO(content))
            text_parts = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            return None
    
    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into overlapping chunks.
        Uses sentence-aware splitting for better semantic coherence.
        """
        # Normalize whitespace
        text = " ".join(text.split())
        
        # Simple sentence-aware chunking
        sentences = text.replace(". ", ".\n").replace("? ", "?\n").replace("! ", "!\n").split("\n")
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(" ".join(current_chunk))
                
                # Start new chunk with overlap
                overlap_text = " ".join(current_chunk)
                if len(overlap_text) > self.chunk_overlap:
                    # Keep last part for overlap
                    words = overlap_text.split()
                    overlap_words = []
                    overlap_len = 0
                    for word in reversed(words):
                        if overlap_len + len(word) < self.chunk_overlap:
                            overlap_words.insert(0, word)
                            overlap_len += len(word) + 1
                        else:
                            break
                    current_chunk = overlap_words
                    current_length = overlap_len
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    async def list_documents(self) -> list[dict]:
        """List all processed documents."""
        return [
            {
                "id": doc_id,
                "filename": meta["filename"],
                "uploaded_at": datetime.fromisoformat(meta["uploaded_at"]),
                "chunk_count": meta["chunk_count"],
                "pii_detected": meta["pii_detected"],
                "pii_summary": meta.get("pii_summary")
            }
            for doc_id, meta in self.documents_metadata.items()
        ]
    
    async def get_document(self, document_id: str) -> Optional[dict]:
        """Get document metadata by ID."""
        return self.documents_metadata.get(document_id)
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its chunks (DSGVO: Right to erasure).
        """
        if document_id not in self.documents_metadata:
            return False
        
        # Delete from vector store
        await self.vector_store.delete_by_document_id(document_id)
        
        # Delete metadata
        del self.documents_metadata[document_id]
        self._save_metadata()
        
        logger.info(f"Deleted document: {document_id}")
        return True
    
    async def get_stats(self) -> dict:
        """Get document statistics."""
        total_documents = len(self.documents_metadata)
        total_chunks = sum(
            meta.get("chunk_count", 0) 
            for meta in self.documents_metadata.values()
        )
        pii_documents = sum(
            1 for meta in self.documents_metadata.values() 
            if meta.get("pii_detected", False)
        )
        
        return {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "pii_documents": pii_documents
        }
    
    async def search_documents(self, query: str, k: int = 5) -> list[dict]:
        """Search across all documents."""
        return await self.vector_store.search(query, k=k)
