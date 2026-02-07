"""
Vector Store Service - ChromaDB Integration
Local persistent vector database for RAG with metadata filtering
"""
import logging
from typing import Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector embeddings with ChromaDB."""
    
    def __init__(self, persist_dir: str | Path = "./data/vectorstore"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,  # Privacy: no telemetry
                allow_reset=True
            )
        )
        
        # Get or create main collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={
                "description": "SentinelAI document chunks",
                "hnsw:space": "cosine"  # Cosine similarity
            }
        )
        
        logger.info(f"Vector store initialized at {self.persist_dir}")
        logger.info(f"Collection 'documents' has {self.collection.count()} entries")
    
    async def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        ids: list[str]
    ) -> int:
        """
        Add documents with their embeddings to the vector store.
        
        Args:
            documents: List of text chunks
            embeddings: Corresponding embedding vectors
            metadatas: Metadata dicts for each document
            ids: Unique IDs for each document
            
        Returns:
            Number of documents added
        """
        try:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to vector store")
            return len(documents)
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    async def search(
        self,
        query: str,
        query_embedding: list[float] = None,
        k: int = 5,
        filter_metadata: dict = None
    ) -> list[dict]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text (used if no embedding provided)
            query_embedding: Pre-computed query embedding
            k: Number of results to return
            filter_metadata: Optional metadata filter (ChromaDB where clause)
            
        Returns:
            List of matching documents with metadata
        """
        try:
            # Perform search
            if query_embedding:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k,
                    where=filter_metadata,
                    include=["documents", "metadatas", "distances"]
                )
            else:
                # Text-based search (requires embedding function in collection)
                results = self.collection.query(
                    query_texts=[query],
                    n_results=k,
                    where=filter_metadata,
                    include=["documents", "metadatas", "distances"]
                )
            
            # Format results
            formatted = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    formatted.append({
                        "id": doc_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0
                    })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def delete_by_document_id(self, document_id: str) -> bool:
        """
        Delete all chunks belonging to a document (DSGVO compliance).
        
        Args:
            document_id: The parent document ID
            
        Returns:
            True if deletion was successful
        """
        try:
            # Find all chunks with this document_id
            results = self.collection.get(
                where={"document_id": document_id},
                include=["metadatas"]
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False
    
    async def get_document_chunks(self, document_id: str) -> list[dict]:
        """Get all chunks for a specific document."""
        try:
            results = self.collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"]
            )
            
            chunks = []
            if results["ids"]:
                for i, chunk_id in enumerate(results["ids"]):
                    chunks.append({
                        "id": chunk_id,
                        "content": results["documents"][i] if results["documents"] else "",
                        "metadata": results["metadatas"][i] if results["metadatas"] else {}
                    })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error getting chunks: {e}")
            return []
    
    async def get_all_document_ids(self) -> list[str]:
        """Get list of unique document IDs in the store."""
        try:
            # Get all metadata
            results = self.collection.get(include=["metadatas"])
            
            if not results["metadatas"]:
                return []
            
            # Extract unique document IDs
            doc_ids = set()
            for metadata in results["metadatas"]:
                if metadata and "document_id" in metadata:
                    doc_ids.add(metadata["document_id"])
            
            return list(doc_ids)
            
        except Exception as e:
            logger.error(f"Error getting document IDs: {e}")
            return []
    
    async def get_stats(self) -> dict:
        """Get vector store statistics."""
        try:
            count = self.collection.count()
            doc_ids = await self.get_all_document_ids()
            
            return {
                "total_chunks": count,
                "total_documents": len(doc_ids),
                "collection_name": self.collection.name,
                "persist_dir": str(self.persist_dir)
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total_chunks": 0, "total_documents": 0}
    
    async def reset(self) -> bool:
        """Reset the entire vector store (use with caution)."""
        try:
            self.client.delete_collection("documents")
            self.collection = self.client.create_collection(
                name="documents",
                metadata={"description": "SentinelAI document chunks"}
            )
            logger.warning("Vector store has been reset")
            return True
        except Exception as e:
            logger.error(f"Reset error: {e}")
            return False
