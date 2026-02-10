"""
LLM Service - Ollama Integration for Mistral NeMo 12B
Handles chat, streaming, and embeddings with full offline capability
"""
import logging
from typing import AsyncGenerator, Optional
import httpx
import ollama
from ollama import AsyncClient

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with local LLM via Ollama."""
    
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model_name: str = "mistral-nemo:12b-instruct-2407-q4_K_M",
        embedding_model: str = "nomic-embed-text"
    ):
        self.ollama_host = ollama_host
        self.model_name = model_name
        self.embedding_model = embedding_model
        self.client = AsyncClient(host=ollama_host)
        
    async def health_check(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            # Check connection
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_host}/api/tags")
                if response.status_code != 200:
                    return False
                
                # Check if our model is available
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                # Check for model (with or without tag)
                model_base = self.model_name.split(":")[0]
                model_found = any(model_base in name for name in model_names)
                
                if not model_found:
                    logger.warning(f"Model {self.model_name} not found. Available: {model_names}")
                    logger.info(f"Run: ollama pull {self.model_name}")
                    return False
                    
                return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        """
        Send a chat request to the LLM and return the complete response.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Generation temperature (0.0-1.0)
            
        Returns:
            Complete response text
        """
        try:
            response = await self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_ctx": 8192,  # Context window
                    "num_predict": 2048,  # Max tokens
                }
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise RuntimeError(f"LLM chat failed: {e}")
    
    async def chat_stream(
        self, 
        messages: list[dict], 
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat responses for real-time UI updates.
        
        Args:
            messages: List of message dicts
            temperature: Generation temperature
            
        Yields:
            Response text chunks
        """
        try:
            stream = await self.client.chat(
                model=self.model_name,
                messages=messages,
                stream=True,
                options={
                    "temperature": temperature,
                    "num_ctx": 8192,
                    "num_predict": 2048,
                }
            )
            
            async for chunk in stream:
                if chunk and "message" in chunk:
                    content = chunk["message"].get("content", "")
                    if content:
                        yield content
                        
        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            yield f"\n[Error: {str(e)}]"
    
    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for text using local embedding model.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            response = await self.client.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            return response["embedding"]
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}")
    
    async def generate_embeddings_batch(
        self, 
        texts: list[str], 
        batch_size: int = 10
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for text in batch:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)
        return embeddings
    
    async def analyze_document(self, text: str, instruction: str = None) -> str:
        """
        Analyze a document with the LLM.
        
        Args:
            text: Document text to analyze
            instruction: Optional specific instruction
            
        Returns:
            Analysis result
        """
        default_instruction = """Analysiere den folgenden Text und extrahiere:
1. Hauptthemen und Schlüsselpunkte
2. Wichtige Fakten und Daten
3. Handlungsrelevante Informationen

Fasse die Ergebnisse strukturiert zusammen."""

        messages = [
            {
                "role": "system",
                "content": instruction or default_instruction
            },
            {
                "role": "user",
                "content": f"Dokument:\n\n{text}"
            }
        ]
        
        return await self.chat(messages)
    
    def get_model_info(self) -> dict:
        """Get information about the current model configuration."""
        return {
            "model": self.model_name,
            "embedding_model": self.embedding_model,
            "host": self.ollama_host
        }
