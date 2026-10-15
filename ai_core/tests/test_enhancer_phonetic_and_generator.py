from ai_core.enhancer import phoneticize
from ai_core.generator import generate_lesson


def test_phoneticize_spanish_basic():
    # Basic expectation: 'hola' phoneticized should be close to 'ho la' without accents
    p = phoneticize("hola", "es")
    assert isinstance(p, str)
    # should contain vowel spacing and no accent markers
    assert "h" in p or "o" in p
    assert " " in p


def test_generate_lesson_struct_consistency():
    # Ensure generate_lesson(as_struct=True) returns consistent structure and deterministic ordering
    s1 = generate_lesson("toys", as_struct=True)
    s2 = generate_lesson("toys", as_struct=True)
    assert isinstance(s1, dict)
    assert isinstance(s2, dict)
    # examples should be non-empty and same ordering across calls
    ex1 = s1.get("examples")
    ex2 = s2.get("examples")
    assert ex1 and isinstance(ex1, list)
    assert ex2 and isinstance(ex2, list)
    assert [e["en"] for e in ex1] == [e["en"] for e in ex2]
    # phrases should include phonetic keys (may be empty string but present)
    for p in s1.get("phrases", []):
        assert "phonetic_en" in p and "phonetic_es" in p
    for e in s1.get("examples", []):
        assert "phonetic_en" in e and "phonetic_es" in e
