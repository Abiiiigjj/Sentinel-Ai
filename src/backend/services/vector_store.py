"""
Vector Store Service - ChromaDB Integration
Local persistent vector database for RAG with metadata filtering
"""
import logging
from typing import Optional
from pathlib import Path
import chromadb  # type: ignore[import]
from chromadb.config import Settings as ChromaSettings  # type: ignore[import]

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
        query_embedding: Optional[list[float]] = None,
        k: int = 5,
        filter_metadata: Optional[dict] = None
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
    
    def calculate_cosine_similarity(
        self, 
        embedding1: list[float], 
        embedding2: list[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        if len(embedding1) != len(embedding2):
            logger.warning("Embedding dimensions don't match")
            return 0.0
        
        # Calculate dot product and magnitudes
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        similarity = dot_product / (magnitude1 * magnitude2)
        # Clamp to valid range
        return max(0.0, min(1.0, similarity))
    
    def distance_to_similarity(self, distance: float) -> float:
        """
        Convert ChromaDB distance (cosine) to similarity score.
        ChromaDB returns distance where 0 = identical, 2 = opposite.
        
        Args:
            distance: Cosine distance from ChromaDB
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Cosine distance = 1 - cosine similarity
        # So similarity = 1 - distance (for normalized case)
        return max(0.0, min(1.0, 1.0 - distance))
    
    async def get_search_quality_metrics(
        self, 
        results: list[dict]
    ) -> dict:
        """
        Calculate quality metrics for search results.
        
        Args:
            results: Search results with 'distance' field
            
        Returns:
            Quality metrics dict
        """
        if not results:
            return {
                "result_count": 0,
                "avg_similarity": 0.0,
                "max_similarity": 0.0,
                "min_similarity": 0.0,
                "quality_score": 0.0,
                "relevance_distribution": []
            }
        
        similarities = [
            self.distance_to_similarity(r.get("distance", 1.0)) 
            for r in results
        ]
        
        avg_similarity = sum(similarities) / len(similarities)
        max_similarity = max(similarities)
        min_similarity = min(similarities)
        
        # Quality score: weighted average favoring top results
        weights = [1.0 / (i + 1) for i in range(len(similarities))]
        weighted_sum = sum(s * w for s, w in zip(similarities, weights))
        quality_score = weighted_sum / sum(weights)
        
        # Categorize results by relevance
        relevance_distribution = {
            "high": sum(1 for s in similarities if s >= 0.7),
            "medium": sum(1 for s in similarities if 0.4 <= s < 0.7),
            "low": sum(1 for s in similarities if s < 0.4)
        }
        
        return {
            "result_count": len(results),
            "avg_similarity": round(float(avg_similarity), 4),  # type: ignore[call-overload]
            "max_similarity": round(float(max_similarity), 4),  # type: ignore[call-overload]
            "min_similarity": round(float(min_similarity), 4),  # type: ignore[call-overload]
            "quality_score": round(float(quality_score), 4),  # type: ignore[call-overload]
            "relevance_distribution": relevance_distribution
        }
    
    async def find_similar_documents(
        self, 
        document_id: str, 
        k: int = 5
    ) -> list[dict]:
        """
        Find documents similar to a given document.
        Uses average embedding of document chunks.
        
        Args:
            document_id: Source document ID
            k: Number of similar documents to return
            
        Returns:
            List of similar documents with similarity scores
        """
        try:
            # Get all chunks for the source document
            results = self.collection.get(
                where={"document_id": document_id},
                include=["embeddings", "metadatas"]
            )
            
            if not results["embeddings"]:
                logger.warning(f"No embeddings found for document {document_id}")
                return []
            
            # Calculate average embedding (centroid)
            embeddings = results["embeddings"]
            num_dims = len(embeddings[0])
            avg_embedding = [
                sum(emb[i] for emb in embeddings) / len(embeddings)
                for i in range(num_dims)
            ]
            
            # Search for similar chunks
            search_results = self.collection.query(
                query_embeddings=[avg_embedding],
                n_results=k * 3,  # Get more to filter duplicates
                include=["metadatas", "distances"]
            )
            
            # Group by document and calculate avg similarity
            doc_similarities = {}
            if search_results["ids"] and search_results["ids"][0]:
                for i, chunk_id in enumerate(search_results["ids"][0]):
                    metadata = search_results["metadatas"][0][i]
                    doc_id = metadata.get("document_id")
                    
                    # Skip source document
                    if doc_id == document_id:
                        continue
                    
                    distance = search_results["distances"][0][i]
                    similarity = self.distance_to_similarity(distance)
                    
                    if doc_id not in doc_similarities:
                        doc_similarities[doc_id] = {
                            "document_id": doc_id,
                            "filename": metadata.get("filename", "Unknown"),
                            "similarities": []
                        }
                    
                    doc_similarities[doc_id]["similarities"].append(similarity)
            
            # Calculate average similarity per document
            similar_docs = []
            for doc_id, data in doc_similarities.items():
                avg_sim = sum(data["similarities"]) / len(data["similarities"])
                similar_docs.append({
                    "document_id": data["document_id"],
                    "filename": data["filename"],
                    "similarity": round(float(avg_sim), 4),  # type: ignore[call-overload]
                    "matching_chunks": len(data["similarities"])
                })
            
            # Sort by similarity descending
            similar_docs.sort(key=lambda x: x["similarity"], reverse=True)
            
            result_docs: list[dict] = similar_docs[:k]  # type: ignore[index]
            return result_docs
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            return []
    
    async def get_embedding_for_document(
        self, 
        document_id: str
    ) -> Optional[list[float]]:
        """
        Get the centroid embedding for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Average embedding vector or None
        """
        try:
            results = self.collection.get(
                where={"document_id": document_id},
                include=["embeddings"]
            )
            
            if not results["embeddings"]:
                return None
            
            embeddings = results["embeddings"]
            num_dims = len(embeddings[0])
            
            return [
                sum(emb[i] for emb in embeddings) / len(embeddings)
                for i in range(num_dims)
            ]
            
        except Exception as e:
            logger.error(f"Error getting document embedding: {e}")
            return None

