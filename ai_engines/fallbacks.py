"""Fallback utilities used when heavy AI libs aren't present.
"""
def simple_translate(text: str) -> str:
    """Very small deterministic translator used when Opus-MT isn't installed.

    This is intentionally naive: substitutes a few common greetings to make
    tests deterministic without external dependencies.
    """
    if not isinstance(text, str):
        return ""
    lower = text.strip().lower()
    if "good evening" in lower or "goodnight" in lower:
        return "Buenas noches"
    if "good morning" in lower or "good day" in lower:
        return "Buenos días"
    if "hello" in lower or "hi" in lower:
        return "Hola"
    # default short echo indicating translation not available
    return f"[translated] {text}"
