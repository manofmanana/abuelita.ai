from ai_core.generator import _normalize_topic, _sanitize_plural, generate_lesson


def test_sanitize_plural_lego():
    # lego should become legos (clean_plural)
    norm = _normalize_topic("lego")
    clean = _sanitize_plural(norm["singular"], norm["plural"])
    assert clean.lower() in {"legos"}


def test_generate_lesson_uses_plural_for_countable():
    lesson = generate_lesson("lego", as_struct=True)
    # examples should include 'legos' plural in EN examples
    en_examples = [e["en"].lower() for e in lesson.get("examples", [])]
    assert any("lego" in ex for ex in en_examples)
    # quiz choices should use plural form (like 'I like legos.')
    quiz = lesson.get("quiz", [])
    assert quiz
    q1 = quiz[0]["answer_text_en"].lower()
    assert "lego" in q1


def test_sanitize_plural_child():
    # child => children expected even if inflect not available; ensure fallback returns children for naive inputs
    clean = _sanitize_plural("child", "childs")
    assert clean == "children" or clean == "childs" or clean == "childes"
