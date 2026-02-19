"""
OCR Service - Phase 3: Real World Vision
Tesseract-based OCR for scanned documents and images.
Supports: scanned PDFs, PNG, JPG/JPEG, TIFF
"""
import logging
from io import BytesIO
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import OCR libraries
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("pytesseract/Pillow not available. OCR disabled.")

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("pdf2image not available. Scanned PDF OCR disabled.")


class OCRResult:
    """Result of an OCR operation."""

    def __init__(self, text: str, confidence: float, ocr_used: bool, pages_processed: int = 0):
        self.text = text
        self.confidence = confidence
        self.ocr_used = ocr_used
        self.pages_processed = pages_processed

    def to_dict(self) -> dict:
        return {
            "ocr_used": self.ocr_used,
            "ocr_confidence": round(self.confidence, 1),
            "pages_processed": self.pages_processed,
        }


class OCRService:
    """Service for Optical Character Recognition using Tesseract."""

    def __init__(
        self,
        languages: str = "deu+eng",
        min_text_threshold: int = 50,
        ocr_enabled: bool = True,
    ):
        """
        Args:
            languages: Tesseract language codes (e.g. 'deu+eng')
            min_text_threshold: Min characters per page to consider non-scanned
            ocr_enabled: Master switch to enable/disable OCR
        """
        self.languages = languages
        self.min_text_threshold = min_text_threshold
        self.ocr_enabled = ocr_enabled and OCR_AVAILABLE

        if self.ocr_enabled:
            # Verify Tesseract is reachable
            try:
                version = pytesseract.get_tesseract_version()
                logger.info(f"✅ OCR Service ready – Tesseract {version}, Sprachen: {languages}")
            except Exception as e:
                logger.error(f"❌ Tesseract nicht erreichbar: {e}")
                self.ocr_enabled = False
        else:
            logger.warning("⚠️ OCR Service deaktiviert")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_scanned_pdf(self, extracted_text: str, page_count: int) -> bool:
        """
        Determine if a PDF is scanned based on extracted text density.

        A PDF is considered 'scanned' if the average characters per page
        falls below min_text_threshold.
        """
        if page_count == 0:
            return True
        avg_chars = len(extracted_text.strip()) / page_count
        is_scanned = avg_chars < self.min_text_threshold
        if is_scanned:
            logger.info(
                f"📄 PDF als gescannt erkannt: {avg_chars:.0f} Zeichen/Seite "
                f"(Schwelle: {self.min_text_threshold})"
            )
        return is_scanned

    def ocr_pdf(self, content: bytes) -> OCRResult:
        """
        Perform OCR on a scanned PDF by converting pages to images first.

        Requires pdf2image (poppler-utils).
        """
        if not self.ocr_enabled:
            return OCRResult(text="", confidence=0.0, ocr_used=False)

        if not PDF2IMAGE_AVAILABLE:
            logger.error("pdf2image nicht verfügbar – poppler-utils installiert?")
            return OCRResult(text="", confidence=0.0, ocr_used=False)

        try:
            images = convert_from_bytes(content, dpi=300)
            logger.info(f"📸 PDF → {len(images)} Seiten konvertiert")

            all_text = []
            all_confidences = []

            for i, image in enumerate(images):
                processed = self._preprocess_image(image)
                page_text, page_conf = self._ocr_single_image(processed)
                all_text.append(page_text)
                all_confidences.append(page_conf)
                logger.debug(f"  Seite {i + 1}: {len(page_text)} Zeichen, Konfidenz: {page_conf:.1f}%")

            combined_text = "\n\n".join(all_text)
            avg_confidence = (
                sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            )

            logger.info(
                f"✅ PDF-OCR abgeschlossen: {len(combined_text)} Zeichen, "
                f"Konfidenz: {avg_confidence:.1f}%, {len(images)} Seiten"
            )

            return OCRResult(
                text=combined_text,
                confidence=avg_confidence,
                ocr_used=True,
                pages_processed=len(images),
            )

        except Exception as e:
            logger.error(f"❌ PDF-OCR Fehler: {e}")
            return OCRResult(text="", confidence=0.0, ocr_used=True)

    def ocr_image(self, content: bytes) -> OCRResult:
        """Perform OCR on a single image file (PNG, JPG, TIFF)."""
        if not self.ocr_enabled:
            return OCRResult(text="", confidence=0.0, ocr_used=False)

        try:
            image = Image.open(BytesIO(content))
            processed = self._preprocess_image(image)
            text, confidence = self._ocr_single_image(processed)

            logger.info(
                f"✅ Bild-OCR abgeschlossen: {len(text)} Zeichen, Konfidenz: {confidence:.1f}%"
            )

            return OCRResult(
                text=text,
                confidence=confidence,
                ocr_used=True,
                pages_processed=1,
            )

        except Exception as e:
            logger.error(f"❌ Bild-OCR Fehler: {e}")
            return OCRResult(text="", confidence=0.0, ocr_used=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _preprocess_image(self, image: "Image.Image") -> "Image.Image":
        """
        Pre-process image for better OCR accuracy.
        Steps: convert to grayscale → sharpen → enhance contrast.
        """
        # Convert to grayscale
        if image.mode != "L":
            image = image.convert("L")

        # Sharpen to improve text edges
        image = image.filter(ImageFilter.SHARPEN)

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)

        # Apply light threshold to clean up noise
        image = image.point(lambda x: 0 if x < 140 else 255, "1")

        return image

    def _ocr_single_image(self, image: "Image.Image") -> tuple[str, float]:
        """
        Run Tesseract on a single (pre-processed) image.

        Returns:
            Tuple of (extracted_text, confidence_percentage)
        """
        # Get detailed data for confidence calculation
        data = pytesseract.image_to_data(
            image, lang=self.languages, output_type=pytesseract.Output.DICT
        )

        # Extract text
        text = pytesseract.image_to_string(image, lang=self.languages)
        text = text.strip()

        # Calculate average confidence (ignoring -1 values = non-text regions)
        confidences = [
            int(c) for c in data["conf"] if str(c).lstrip("-").isdigit() and int(c) >= 0
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return text, avg_confidence
