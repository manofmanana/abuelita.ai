"""Simple translator wrapper using deep_translator with fallback."""
import logging

logger = logging.getLogger(__name__)

try:
    from deep_translator import GoogleTranslator
except Exception:  # pragma: no cover - optional dependency
    GoogleTranslator = None

from functools import lru_cache

# Create a single GoogleTranslator instance and cache individual translations
_translator_instance = None

def _get_translator():
    global _translator_instance
    if GoogleTranslator is None:
        return None
    if _translator_instance is None:
        try:
            _translator_instance = GoogleTranslator(source="en", target="es")
        except Exception as e:
            logger.warning("Could not instantiate GoogleTranslator: %s", e)
            _translator_instance = None
    return _translator_instance


@lru_cache(maxsize=2048)
def translate_to_spanish(text: str) -> str:
    """Translate to Spanish using a cached translator and memoize results.

    The LRU cache avoids repeated network calls for identical strings and the
    single translator instance reduces per-call overhead.
    """
    if GoogleTranslator is None:
        # Very small deterministic fallback: append a marker
        return f"[es] {text}"
    try:
        tr = _get_translator()
        if tr is None:
            return f"[es] {text}"
        return tr.translate(text)
    except Exception as e:
        logger.warning("translate_to_spanish failed: %s", e)
        return f"[es] {text}"
