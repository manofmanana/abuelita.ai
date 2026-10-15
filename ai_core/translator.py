"""Translation helpers (Google Translate).

* The primary backend is Google's public ``translate_a/single`` JSON endpoint,
  called with the standard library. deep-translator's scraped web endpoint is
  kept as a fallback; Google often answers it with a CAPTCHA/429.
* ``translate(text, source, target)`` handles any length of text by splitting
  it into chunks under Google's ~5000 character limit, on paragraph/sentence
  boundaries where possible.
* Results for short strings are memoised, so lesson generation does not
  repeat network calls for identical phrases.
* Setting ``ABUELITA_OFFLINE=1`` (used by the test suite) skips the network
  entirely and returns a deterministic marker such as ``[es] Hello``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.parse
import urllib.request
from functools import lru_cache

logger = logging.getLogger(__name__)

try:
    from deep_translator import GoogleTranslator
except Exception:  # pragma: no cover - optional dependency
    GoogleTranslator = None

MAX_CHUNK_CHARS = 4500
GOOGLE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"
REQUEST_TIMEOUT = 15
SUPPORTED_LANGS = {"en", "es", "auto"}


class TranslationError(RuntimeError):
    """Raised when the translation backend fails."""


def offline_mode() -> bool:
    return os.getenv("ABUELITA_OFFLINE", "").strip().lower() in {"1", "true", "yes"}


def split_into_chunks(text: str, limit: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split ``text`` into pieces no longer than ``limit`` characters.

    Paragraphs are kept intact when they fit, then sentences, and only as a
    last resort is a very long sentence cut at whitespace.
    """
    if len(text) <= limit:
        return [text]

    pieces: list[str] = []
    for paragraph in re.split(r"(\n\s*\n)", text):
        if len(paragraph) <= limit:
            pieces.append(paragraph)
            continue
        for sentence in re.split(r"(?<=[.!?¿¡])\s+", paragraph):
            while len(sentence) > limit:
                cut = sentence.rfind(" ", 0, limit)
                cut = cut if cut > 0 else limit
                pieces.append(sentence[:cut])
                sentence = sentence[cut:]
            pieces.append(sentence + " ")

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if current and len(current) + len(piece) > limit:
            chunks.append(current)
            current = ""
        current += piece
    if current.strip():
        chunks.append(current)
    return chunks


def _google_translate(chunk: str, source: str, target: str) -> str:
    query = urllib.parse.urlencode({"client": "gtx", "sl": source, "tl": target, "dt": "t"})
    body = urllib.parse.urlencode({"q": chunk}).encode()
    request = urllib.request.Request(f"{GOOGLE_ENDPOINT}?{query}", data=body)
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    # data[0] is a list of [translated, original, ...] segments.
    return "".join(segment[0] for segment in data[0] or [] if segment and segment[0])


@lru_cache(maxsize=2048)
def _translate_chunk(chunk: str, source: str, target: str) -> str:
    if offline_mode():
        return "\n".join(f"[{target}] {line}" if line.strip() else line for line in chunk.split("\n"))
    try:
        return _google_translate(chunk, source, target)
    except Exception as exc:
        if GoogleTranslator is None:
            raise
        logger.info("Primary translator failed (%s); trying deep-translator", exc)
        result = GoogleTranslator(source=source, target=target).translate(chunk)
        return result if result is not None else ""


def translate(text: str, source: str = "auto", target: str = "es") -> str:
    """Translate ``text`` from ``source`` to ``target``.

    Raises ``TranslationError`` if the backend fails, so callers can show a
    friendly message instead of a stack trace.
    """
    if source not in SUPPORTED_LANGS or target not in SUPPORTED_LANGS - {"auto"}:
        raise ValueError(f"Unsupported language pair: {source} -> {target}")
    if not text or not text.strip():
        return ""
    try:
        return "".join(_translate_chunk(chunk, source, target) for chunk in split_into_chunks(text, MAX_CHUNK_CHARS))
    except Exception as exc:
        logger.warning("Translation failed (%s -> %s): %s", source, target, exc)
        raise TranslationError(str(exc)) from exc


def translate_to_spanish(text: str) -> str:
    """English -> Spanish for lesson content. Never raises.

    Falls back to a visible ``[es]`` marker so a lesson still renders when the
    translation service is unreachable.
    """
    try:
        return translate(text, source="en", target="es")
    except TranslationError:
        return f"[es] {text}"
