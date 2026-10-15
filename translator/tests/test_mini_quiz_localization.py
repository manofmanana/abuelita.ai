from django.test import Client, TestCase

from ai_core import generator


class MiniQuizLocalizationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_generator_struct_includes_localized_labels(self):
        """Generator should include both English and Spanish mini-quiz labels."""
        struct = generator.generate_lesson("lego", as_struct=True)
        # Keys must be present
        self.assertIn("mini_quiz_en", struct)
        self.assertIn("mini_quiz_es", struct)
        # Values should be sensible defaults
        self.assertTrue(struct["mini_quiz_en"])
        self.assertTrue(struct["mini_quiz_es"])
        # Expect the English default and the Spanish requested label
        self.assertIn("Mini-quiz", struct["mini_quiz_en"])
        self.assertIn("Mini-prueba", struct["mini_quiz_es"])

    def test_learn_page_shows_localized_mini_quiz_label(self):
        """The learn page should render the Spanish label when served under /es/ and English under /en/."""
        # English page
        resp_en = self.client.post("/en/learn/", {"input_text": "lego"})
        if resp_en.status_code == 302:
            resp_en = self.client.get(resp_en.url)
        content_en = resp_en.content.decode("utf-8")
        self.assertIn("Mini-quiz", content_en)

        # Spanish page
        resp_es = self.client.post("/es/learn/", {"input_text": "lego"})
        if resp_es.status_code == 302:
            resp_es = self.client.get(resp_es.url)
        content_es = resp_es.content.decode("utf-8")
        # Spanish localized label should appear
        self.assertIn("Mini-prueba", content_es)

    def test_generator_enhancements_paraphrase_and_difficulty(self):
        """Generator should attach paraphrases and difficulty buckets; cloze items removed."""
        struct = generator.generate_lesson("lego", as_struct=True)
        # phrases should be a list of dicts with difficulty and optionally paraphrases
        self.assertIsInstance(struct.get("phrases"), list)
        self.assertIsInstance(struct.get("examples"), list)
        # Spot-check first phrase and example
        if struct["phrases"]:
            p0 = struct["phrases"][0]
            self.assertIn("difficulty", p0)
            # difficulty should be one of the expected buckets
            self.assertIn(p0["difficulty"], ["easy", "medium", "hard"])
        if struct["examples"]:
            e0 = struct["examples"][0]
            self.assertIn("difficulty", e0)
            # cloze items were removed from generator output; ensure keys are absent
            self.assertNotIn("cloze_en", e0)
            # paraphrases are optional; when present they should be list-like
            if "paraphrases_en" in struct["phrases"][0]:
                self.assertIsInstance(struct["phrases"][0]["paraphrases_en"], list)

    def test_generator_labels_and_progression_groups(self):
        struct = generator.generate_lesson("lego", as_struct=True)
        self.assertIn("labels", struct)
        labels = struct["labels"]
        self.assertIn("paraphrases_en", labels)
        self.assertIn("paraphrases_es", labels)
        self.assertIn("phrases_by_difficulty", struct)
        self.assertIn("examples_by_difficulty", struct)
        # Each difficulty bucket should exist
        for b in ("easy", "medium", "hard"):
            self.assertIn(b, struct["phrases_by_difficulty"])
            self.assertIn(b, struct["examples_by_difficulty"])
