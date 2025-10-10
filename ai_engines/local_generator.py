"""Small local generator wrapper.

Uses transformers pipeline if available, otherwise returns a safe fallback.
"""
import logging
import os

try:
    from transformers import pipeline
except Exception:  # pragma: no cover - optional heavy dependency
    pipeline = None

logger = logging.getLogger(__name__)

# Only initialize heavy local models when the environment explicitly enables them.
_LOCAL_AI_ENABLED = os.getenv("ABUELITA_ENABLE_LOCAL_AI", "1") == "1"
_generator = None


def _init_generator():
    global _generator
    if _generator is not None:
        return _generator
    if not _LOCAL_AI_ENABLED:
        return None
    if pipeline is None:
        return None
    try:
        _generator = pipeline("text2text-generation", model="declare-lab/flan-alpaca-base")
    except Exception as e:  # pragma: no cover
        logger.warning("Local generator init failed: %s", e)
        _generator = None
    return _generator


def generate_text(prompt: str) -> str:
    """Generate lesson text locally; fallback-safe.

    The actual model is initialized lazily only when ABUELITA_ENABLE_LOCAL_AI=1.
    """
    gen = _init_generator()
    if not gen:
        return "[AI unavailable]"
    try:
        result = gen(prompt, max_length=256, do_sample=True)
        return result[0].get("generated_text", "[AI returned unexpected format]")
    except Exception as e:
        logger.error("generate_text error: %s", e)
        return "[AI generation error]"
