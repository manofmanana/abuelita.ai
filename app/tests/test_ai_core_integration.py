from django.test import TestCase

from ai_core import generate_lesson, translate_to_spanish, grade_answer, recommend_similar, summarize_progress


class TestAICore(TestCase):
    def test_generate_lesson_returns_text(self):
        out = generate_lesson("greetings")
        assert isinstance(out, str)
        assert len(out) > 0

    def test_translate_to_spanish_returns_text(self):
        out = translate_to_spanish("Good morning")
        assert isinstance(out, str)

    def test_grade_answer_basic(self):
        ref = "Hola, buenos días"
        usr = "Hola buenos dias"
        score = grade_answer(ref, usr)
        assert isinstance(score, float)

    def test_recommend_similar_empty(self):
        recs = recommend_similar("hola", corpus_texts=["hola amigo", "buenos dias"])
        assert isinstance(recs, list)

    def test_summarize_progress(self):
        stats = summarize_progress([{"score": 0.8, "completed": True}, {"score": 0.6, "completed": False}])
        assert "avg" in stats and "completed_pct" in stats
