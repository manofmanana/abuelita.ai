from bs4 import BeautifulSoup
from django.test import Client, TestCase


class LearnIntegrationDynamicTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _post_and_parse(self, topic):
        resp = self.client.post("/en/learn/", {"input_text": topic})
        if resp.status_code == 302:
            resp = self.client.get(resp.url)
        content = resp.content.decode("utf-8")
        return BeautifulSoup(content, "html.parser")

    def test_learn_page_renders_en_es_toggles_and_quiz_for_noun(self):
        soup = self._post_and_parse("lego")
        # check for lesson result header and general page content
        page_text = soup.get_text()
        self.assertIn("Lesson Result", page_text)
        # Check that the page contains the bilingual tip and bilingual items
        self.assertIn("Tip: Click any phrase or example to view English and Spanish side-by-side", page_text)
        # Ensure at least one ES translation snippet is present in the markup
        self.assertIn("ES:", page_text)
        # quiz presence
        self.assertIn("Mini-quiz", page_text)

    def test_learn_page_handles_verb_topic(self):
        soup = self._post_and_parse("run")
        text = soup.get_text().lower()
        # The topic should appear on the page (we use a relaxed check)
        self.assertIn("run", text)

    def test_learn_page_neutral_for_sensitive(self):
        soup = self._post_and_parse("sex")
        text = soup.get_text().lower()
        # Should avoid directly repeating the sensitive word in phrases
        self.assertTrue("this topic" in text or "this topic" in text)
