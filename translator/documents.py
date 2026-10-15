"""Extract plain text from uploaded documents."""

from __future__ import annotations

from pathlib import Path

from django.utils.translation import gettext as _

SUPPORTED_EXTENSIONS = (".txt", ".docx", ".pdf")


class DocumentError(ValueError):
    """The uploaded file could not be read."""


def extract_text(uploaded_file) -> str:
    ext = Path(uploaded_file.name).suffix.lower()
    try:
        if ext == ".txt":
            raw = uploaded_file.read()
            for encoding in ("utf-8-sig", "cp1252", "latin-1"):
                try:
                    return raw.decode(encoding)
                except UnicodeDecodeError:
                    continue
        if ext == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(uploaded_file)
            return "\n\n".join(text for page in reader.pages if (text := page.extract_text()))
        if ext == ".docx":
            from docx import Document

            return "\n".join(p.text for p in Document(uploaded_file).paragraphs)
    except Exception as exc:
        raise DocumentError(_("We couldn't read that file. Is it a valid TXT, DOCX or PDF?")) from exc
    raise DocumentError(_("Unsupported file type."))
