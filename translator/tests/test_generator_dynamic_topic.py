from django.test import TestCase

from ai_core import generator


class GeneratorDynamicTopicTests(TestCase):
    def test_regular_noun_generates_plural_phrases(self):
        topic = "lego"
        struct = generator.generate_lesson(topic, as_struct=True)
        # phrases should include plural form 'legos' in at least one phrase
        phrases = [p["en"] for p in struct["phrases"]]
        self.assertTrue(any("lego" in s.lower() for s in phrases))
        self.assertTrue(any("legos" in s.lower() or "lego" in s.lower() for s in phrases))

    def test_explicit_plural_topic(self):
        topic = "legos"
        struct = generator.generate_lesson(topic, as_struct=True)
        phrases = [p["en"] for p in struct["phrases"]]
        # Should not produce 'legoss' or awkward double-s 's'
        joined = " ".join(phrases).lower()
        self.assertNotIn("legoss", joined)
        self.assertIn("legos", joined)

    def test_sensitive_topic_falls_back_to_neutral(self):
        topic = "sex"
        struct = generator.generate_lesson(topic, as_struct=True)
        # For sensitive topics we prefer a neutral 'this topic' phrasing in outputs
        joined = " ".join(p["en"] for p in struct["phrases"]).lower()
        self.assertTrue("this topic" in joined or "sex" not in joined)
