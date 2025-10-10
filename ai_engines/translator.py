"""Translator wrapper using Opus-MT if available.
"""
import logging
import os

try:
    from transformers import pipeline
except Exception:  # pragma: no cover
    pipeline = None

from .fallbacks import simple_translate

logger = logging.getLogger(__name__)

_LOCAL_AI_ENABLED = os.getenv("ABUELITA_ENABLE_LOCAL_AI", "1") == "1"
_translator = None


def _init_translator():
    global _translator
    if _translator is not None:
        return _translator
    if not _LOCAL_AI_ENABLED:
        return None
    if pipeline is None:
        return None
    try:
        _translator = pipeline("translation", model="Helsinki-NLP/opus-mt-en-es")
    except Exception as e:  # pragma: no cover
        logger.warning("Local translator init failed: %s", e)
        _translator = None
    return _translator


def translate_to_spanish(text: str) -> str:
    trans = _init_translator()
    if not trans:
        return simple_translate(text)
    try:
        out = trans(text, max_length=256)
        return out[0].get("translation_text") or out[0].get("generated_text") or ""
    except Exception as e:
        logger.error("translate_to_spanish error: %s", e)
        return simple_translate(text)
