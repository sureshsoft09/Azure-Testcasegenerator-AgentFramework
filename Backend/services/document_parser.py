import io
import logging
from typing import Tuple

import fitz  # PyMuPDF
from docx import Document

logger = logging.getLogger(__name__)


def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"PDF parsing error: {e}")
        raise


def parse_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes."""
    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        logger.error(f"DOCX parsing error: {e}")
        raise


def parse_document(file_bytes: bytes, filename: str) -> Tuple[str, str]:
    """Auto-detect format and parse. Returns (text, mime_type)."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return parse_pdf(file_bytes), "application/pdf"
    elif lower.endswith(".docx"):
        return parse_docx(file_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif lower.endswith(".doc"):
        # Fallback – treat as plain text (limited support without libreoffice)
        return file_bytes.decode("utf-8", errors="ignore"), "application/msword"
    else:
        return file_bytes.decode("utf-8", errors="ignore"), "text/plain"
