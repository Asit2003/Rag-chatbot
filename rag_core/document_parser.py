from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


class DocumentParseError(Exception):
    pass


def parse_document_bytes(ext: str, content: bytes) -> str:
    ext = ext.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise DocumentParseError(f"Unsupported file type: {ext}")

    try:
        if ext == ".pdf":
            reader = PdfReader(BytesIO(content))
            text_parts = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(text_parts).strip()

        if ext == ".docx":
            doc = DocxDocument(BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs).strip()

        return content.decode("utf-8", errors="ignore").strip()
    except Exception as exc:  # pragma: no cover
        raise DocumentParseError(str(exc)) from exc


def parse_document(path: Path) -> str:
    return parse_document_bytes(path.suffix.lower(), path.read_bytes())

