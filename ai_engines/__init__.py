"""Local AI engines facade for Abuelita.ai v2.

Expose small, sandbox-safe utilities for local generation and translation.
The implementations are intentionally defensive: missing heavy deps return
deterministic fallback strings so the Django app and tests never crash.
"""
from .local_generator import generate_text
from .translator import translate_to_spanish
from .fallbacks import simple_translate

__all__ = ["generate_text", "translate_to_spanish", "simple_translate"]
