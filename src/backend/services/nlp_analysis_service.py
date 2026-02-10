"""
NLP Analysis Service - Keyword Extraction & Topic Modeling
Uses local LLM for offline text analysis with structured output
"""
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of NLP analysis on text."""
    keywords: list[str] = field(default_factory=list)
    topics: list[dict] = field(default_factory=list)
    summary: str = ""
    language: str = "de"
    raw_text_length: int = 0


class NLPAnalysisService:
    """Service for advanced NLP analysis using local LLM."""
    
    # Prompt templates
    KEYWORD_PROMPT = """Analysiere den folgenden Text und extrahiere die {max_keywords} wichtigsten Schlüsselwörter.

Regeln:
- Nur substantielle Begriffe (keine Stoppwörter)
- Fachbegriffe und spezifische Konzepte bevorzugen
- Zusammengesetzte Begriffe sind erlaubt (z.B. "Datenschutz-Grundverordnung")

Antworte NUR im JSON-Format:
{{"keywords": ["keyword1", "keyword2", ...]}}

Text:
{text}"""

    TOPIC_PROMPT = """Analysiere den folgenden Text und identifiziere die {max_topics} Hauptthemen.

Für jedes Thema gib an:
- name: Kurzer Themenname (2-4 Wörter)
- confidence: Konfidenz von 0.0 bis 1.0
- description: Ein Satz Beschreibung

Antworte NUR im JSON-Format:
{{"topics": [{{"name": "...", "confidence": 0.9, "description": "..."}}]}}

Text:
{text}"""

    COMBINED_PROMPT = """Analysiere den folgenden Text und extrahiere:
1. Die {max_keywords} wichtigsten Schlüsselwörter
2. Die {max_topics} Hauptthemen mit Konfidenz-Score (0.0-1.0)
3. Eine kurze Zusammenfassung (max 2 Sätze)

Antworte NUR im JSON-Format:
{{
  "keywords": ["keyword1", "keyword2", ...],
  "topics": [{{"name": "Themenname", "confidence": 0.9, "description": "Kurze Beschreibung"}}],
  "summary": "Zusammenfassung des Textes."
}}

Text:
{text}"""

    def __init__(self, llm_service):
        """
        Initialize NLP Analysis Service.
        
        Args:
            llm_service: LLM service instance for text generation
        """
        self.llm_service = llm_service
        logger.info("NLP Analysis Service initialized")
    
    async def extract_keywords(
        self, 
        text: str, 
        max_keywords: int = 10
    ) -> list[str]:
        """
        Extract keywords from text using LLM.
        
        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short for keyword extraction")
            return []
        
        # Truncate very long texts to fit context window
        text = self._truncate_text(text, max_chars=6000)
        
        prompt = self.KEYWORD_PROMPT.format(
            max_keywords=max_keywords,
            text=text
        )
        
        try:
            response = await self.llm_service.chat([
                {"role": "system", "content": "Du bist ein präziser Textanalyse-Assistent. Antworte immer nur im angeforderten JSON-Format."},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            result = self._parse_json_response(response)
            keywords = result.get("keywords", [])
            
            # Validate and clean keywords
            keywords = [k.strip() for k in keywords if isinstance(k, str) and k.strip()]
            
            logger.info(f"Extracted {len(keywords)} keywords")
            result_keywords: list[str] = keywords[:max_keywords]
            return result_keywords
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []
    
    async def extract_topics(
        self, 
        text: str, 
        max_topics: int = 5
    ) -> list[dict]:
        """
        Extract topics with confidence scores from text.
        
        Args:
            text: Text to analyze
            max_topics: Maximum number of topics to extract
            
        Returns:
            List of topic dicts with name, confidence, description
        """
        if not text or len(text.strip()) < 100:
            logger.warning("Text too short for topic extraction")
            return []
        
        text = self._truncate_text(text, max_chars=6000)
        
        prompt = self.TOPIC_PROMPT.format(
            max_topics=max_topics,
            text=text
        )
        
        try:
            response = await self.llm_service.chat([
                {"role": "system", "content": "Du bist ein präziser Textanalyse-Assistent. Antworte immer nur im angeforderten JSON-Format."},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            result = self._parse_json_response(response)
            topics = result.get("topics", [])
            
            # Validate topics
            validated_topics = []
            for topic in topics:
                if isinstance(topic, dict) and "name" in topic:
                    validated_topics.append({
                        "name": str(topic.get("name", "")).strip(),
                        "confidence": float(topic.get("confidence", 0.5)),
                        "description": str(topic.get("description", "")).strip()
                    })
            
            logger.info(f"Extracted {len(validated_topics)} topics")
            result_topics: list[dict] = validated_topics[:max_topics]  # type: ignore[index]
            return result_topics
            
        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
            return []
    
    async def analyze_text(
        self,
        text: str,
        max_keywords: int = 10,
        max_topics: int = 5
    ) -> AnalysisResult:
        """
        Perform combined analysis (keywords, topics, summary).
        
        Args:
            text: Text to analyze
            max_keywords: Maximum keywords
            max_topics: Maximum topics
            
        Returns:
            AnalysisResult with all extracted information
        """
        if not text or len(text.strip()) < 50:
            return AnalysisResult(raw_text_length=len(text) if text else 0)
        
        text_truncated = self._truncate_text(text, max_chars=6000)
        
        prompt = self.COMBINED_PROMPT.format(
            max_keywords=max_keywords,
            max_topics=max_topics,
            text=text_truncated
        )
        
        try:
            response = await self.llm_service.chat([
                {"role": "system", "content": "Du bist ein präziser Textanalyse-Assistent. Antworte immer nur im angeforderten JSON-Format."},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            result = self._parse_json_response(response)
            
            # Extract and validate keywords
            keywords = result.get("keywords", [])
            keywords = [k.strip() for k in keywords if isinstance(k, str) and k.strip()]
            
            # Extract and validate topics
            topics = []
            for topic in result.get("topics", []):
                if isinstance(topic, dict) and "name" in topic:
                    topics.append({
                        "name": str(topic.get("name", "")).strip(),
                        "confidence": float(topic.get("confidence", 0.5)),
                        "description": str(topic.get("description", "")).strip()
                    })
            
            final_keywords: list[str] = keywords[:max_keywords]
            final_topics: list[dict] = topics[:max_topics]  # type: ignore[index]
            return AnalysisResult(
                keywords=final_keywords,
                topics=final_topics,
                summary=str(result.get("summary", "")).strip(),
                raw_text_length=len(text)
            )
            
        except Exception as e:
            logger.error(f"Combined analysis failed: {e}")
            return AnalysisResult(raw_text_length=len(text))
    
    async def analyze_document_chunks(
        self,
        chunks: list[str],
        max_keywords: int = 15,
        max_topics: int = 5
    ) -> AnalysisResult:
        """
        Analyze a document by processing its chunks.
        Combines chunks and performs analysis on representative sample.
        
        Args:
            chunks: List of document text chunks
            max_keywords: Maximum keywords for entire document
            max_topics: Maximum topics
            
        Returns:
            AnalysisResult for the document
        """
        if not chunks:
            return AnalysisResult()
        
        # Combine chunks intelligently (first, middle, last for representative sample)
        combined_text = self._sample_chunks(chunks)
        
        logger.info(f"Analyzing {len(chunks)} chunks ({len(combined_text)} chars sampled)")
        
        return await self.analyze_text(
            combined_text,
            max_keywords=max_keywords,
            max_topics=max_topics
        )
    
    def _truncate_text(self, text: str, max_chars: int = 6000) -> str:
        """Truncate text to fit LLM context, preserving sentence boundaries."""
        if len(text) <= max_chars:
            return text
        
        # Try to cut at sentence boundary
        truncated: str = text[0:max_chars]
        last_period: int = truncated.rfind('. ')
        threshold: float = max_chars * 0.7
        
        if last_period > threshold:
            end_pos: int = last_period + 1
            return truncated[0:end_pos]
        
        return truncated + "..."
    
    def _sample_chunks(self, chunks: list[str], max_total_chars: int = 6000) -> str:
        """Sample representative chunks from document."""
        if not chunks:
            return ""
        
        if len(chunks) == 1:
            return chunks[0]
        
        # Take first, last, and evenly distributed middle chunks
        sample_indices = [0]  # First chunk
        
        if len(chunks) > 2:
            # Add middle chunks
            step = max(1, len(chunks) // 4)
            for i in range(step, len(chunks) - 1, step):
                sample_indices.append(i)
        
        sample_indices.append(len(chunks) - 1)  # Last chunk
        
        # Remove duplicates and sort
        sample_indices = sorted(set(sample_indices))
        
        # Combine sampled chunks
        combined: list[str] = []
        current_length: int = 0
        
        for idx in sample_indices:
            chunk: str = chunks[idx]
            chunk_len: int = len(chunk)
            total: int = int(current_length) + int(chunk_len)
            if total > max_total_chars:
                remaining: int = int(max_total_chars) - int(current_length)
                if remaining > 200:
                    partial: str = chunk[0:remaining]
                    combined.append(partial)
                break
            combined.append(chunk)
            current_length = int(total) + 2  # type: ignore[assignment]  # +2 for separator
        
        return "\n\n".join(combined)
    
    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        if not response:
            return {}
        
        # Remove markdown code blocks if present
        response = response.strip()
        
        # Handle ```json ... ``` format
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)
        
        # Try to find JSON object
        try:
            # Find first { and last }
            start: int = response.find('{')
            end: int = response.rfind('}')
            
            if start != -1 and end != -1 and end > start:
                end_inclusive: int = end + 1
                json_str: str = response[start:end_inclusive]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
        
        return {}
