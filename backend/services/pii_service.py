"""
PII Service - Personal Identifiable Information Detection and Masking
Uses spaCy for NER and regex patterns for German-specific PII
"""
import re
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Try to import spaCy, but provide fallback
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Using regex-only PII detection.")


@dataclass
class PIIMatch:
    """Represents a detected PII match."""
    type: str
    value: str
    start: int
    end: int
    masked_value: str


@dataclass
class PIIResult:
    """Result of PII detection on a text."""
    original_text: str
    masked_text: str
    pii_detected: bool
    matches: list[PIIMatch] = field(default_factory=list)
    
    @property
    def summary(self) -> str:
        """Generate a summary of detected PII types."""
        if not self.matches:
            return "Keine PII erkannt"
        
        type_counts = {}
        for match in self.matches:
            type_counts[match.type] = type_counts.get(match.type, 0) + 1
        
        parts = [f"{count}x {pii_type}" for pii_type, count in type_counts.items()]
        return ", ".join(parts)


class PIIService:
    """Service for detecting and masking personally identifiable information."""
    
    # German-specific regex patterns
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone_de": r'\b(?:\+49|0049|0)[\s\-]?(?:\d{2,4})[\s\-]?(?:\d{3,})[\s\-]?(?:\d{2,})\b',
        "iban": r'\b[A-Z]{2}\d{2}[\s]?(?:\d{4}[\s]?){4,7}\d{0,2}\b',
        "bic": r'\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b',
        "plz_de": r'\b\d{5}\b',  # German postal code
        "date_de": r'\b(?:\d{1,2}[./]\d{1,2}[./]\d{2,4})\b',
        "steuer_id": r'\b\d{2}[\s]?\d{3}[\s]?\d{3}[\s]?\d{3}\b',  # German tax ID
        "sozialversicherung": r'\b\d{2}[\s]?\d{6}[\s]?[A-Z][\s]?\d{3}\b',  # German social security
        "kreditkarte": r'\b(?:\d{4}[\s\-]?){3}\d{4}\b',  # Credit card
        "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }
    
    # Mask patterns for different PII types
    MASK_PATTERNS = {
        "email": "[EMAIL]",
        "phone_de": "[TELEFON]",
        "iban": "[IBAN]",
        "bic": "[BIC]",
        "plz_de": "[PLZ]",
        "date_de": "[DATUM]",
        "steuer_id": "[STEUER-ID]",
        "sozialversicherung": "[SOZVERS-NR]",
        "kreditkarte": "[KREDITKARTE]",
        "ip_address": "[IP-ADRESSE]",
        "PERSON": "[PERSON]",
        "ORG": "[ORGANISATION]",
        "LOC": "[ORT]",
        "GPE": "[ORT]",
    }
    
    def __init__(self, spacy_model: str = "de_core_news_lg", enabled: bool = True):
        self.enabled = enabled
        self.nlp = None
        
        if SPACY_AVAILABLE and enabled:
            try:
                self.nlp = spacy.load(spacy_model)
                logger.info(f"Loaded spaCy model: {spacy_model}")
            except OSError:
                logger.warning(f"spaCy model '{spacy_model}' not found. "
                             f"Run: python -m spacy download {spacy_model}")
                # Try smaller model as fallback
                try:
                    self.nlp = spacy.load("de_core_news_sm")
                    logger.info("Loaded fallback model: de_core_news_sm")
                except OSError:
                    logger.warning("No German spaCy model available. Using regex only.")
    
    def detect_pii(self, text: str, mask: bool = True) -> PIIResult:
        """
        Detect and optionally mask PII in text.
        
        Args:
            text: Input text to analyze
            mask: Whether to mask detected PII
            
        Returns:
            PIIResult with detection details
        """
        if not self.enabled:
            return PIIResult(
                original_text=text,
                masked_text=text,
                pii_detected=False,
                matches=[]
            )
        
        matches: list[PIIMatch] = []
        masked_text = text
        
        # 1. Regex-based detection
        for pii_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                mask_value = self.MASK_PATTERNS.get(pii_type, "[REDACTED]")
                matches.append(PIIMatch(
                    type=pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    masked_value=mask_value
                ))
        
        # 2. spaCy NER-based detection
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["PER", "PERSON", "ORG", "LOC", "GPE"]:
                    mask_value = self.MASK_PATTERNS.get(ent.label_, "[REDACTED]")
                    matches.append(PIIMatch(
                        type=ent.label_,
                        value=ent.text,
                        start=ent.start_char,
                        end=ent.end_char,
                        masked_value=mask_value
                    ))
        
        # 3. Apply masking (sort by position to handle overlaps)
        if mask and matches:
            # Sort by start position (descending) to replace from end
            sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)
            
            # Track replaced spans to avoid double-masking
            replaced_spans = set()
            
            for match in sorted_matches:
                span_key = (match.start, match.end)
                if span_key not in replaced_spans:
                    masked_text = (
                        masked_text[:match.start] + 
                        match.masked_value + 
                        masked_text[match.end:]
                    )
                    replaced_spans.add(span_key)
        
        return PIIResult(
            original_text=text,
            masked_text=masked_text,
            pii_detected=len(matches) > 0,
            matches=matches
        )
    
    def detect_in_chunks(self, chunks: list[str], mask: bool = True) -> list[PIIResult]:
        """Detect PII in multiple text chunks."""
        return [self.detect_pii(chunk, mask) for chunk in chunks]
    
    def get_pii_stats(self, results: list[PIIResult]) -> dict:
        """Get statistics from multiple PII results."""
        total_matches = 0
        type_counts = {}
        documents_with_pii = 0
        
        for result in results:
            if result.pii_detected:
                documents_with_pii += 1
            
            for match in result.matches:
                total_matches += 1
                type_counts[match.type] = type_counts.get(match.type, 0) + 1
        
        return {
            "total_matches": total_matches,
            "documents_with_pii": documents_with_pii,
            "type_distribution": type_counts
        }
    
    def is_available(self) -> bool:
        """Check if PII detection is fully available."""
        return self.enabled and (self.nlp is not None or True)  # Regex always works
