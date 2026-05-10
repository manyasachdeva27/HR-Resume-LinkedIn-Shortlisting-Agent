"""
tools/pdf_reader.py
───────────────────
Document text extraction utilities.

Supports PDF (via pdfplumber) and DOCX (via python-docx) formats.
Falls back to reading plain-text for .txt files.
"""

from __future__ import annotations

import os
from typing import Optional


def extract_text_from_file(file_path: str) -> str:
    """
    Extract raw text from a PDF, DOCX, or TXT file.

    Args:
        file_path: Absolute or relative path to the document.

    Returns:
        Extracted text as a single string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is unsupported.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _extract_pdf(file_path)
    elif ext == ".docx":
        return _extract_docx(file_path)
    elif ext in (".txt", ".json"):
        return _extract_txt(file_path)
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. Accepted: .pdf, .docx, .txt, .json"
        )


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from in-memory file bytes (used by Streamlit uploads).

    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename: Original filename (used to determine format).

    Returns:
        Extracted text as a single string.
    """
    import tempfile

    ext = os.path.splitext(filename)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        return extract_text_from_file(tmp_path)
    finally:
        os.unlink(tmp_path)


# ── Private helpers ─────────────────────────────────────────────────


def _extract_pdf(file_path: str) -> str:
    """Extract text from a PDF file using pdfplumber."""
    import pdfplumber

    pages: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text: Optional[str] = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def _extract_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_txt(file_path: str) -> str:
    """Read a plain-text file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()
