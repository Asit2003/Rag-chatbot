from __future__ import annotations

from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


class DocumentParseError(Exception):
    pass


def parse_document(path: Path) -> str:
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise DocumentParseError(f"Unsupported file type: {ext}")

    try:
        if ext == ".pdf":
            reader = PdfReader(str(path))
            text_parts = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(text_parts).strip()

        if ext == ".docx":
            doc = DocxDocument(str(path))
            return "\n".join(p.text for p in doc.paragraphs).strip()

        return path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception as exc:  # pragma: no cover
        raise DocumentParseError(str(exc)) from exc
