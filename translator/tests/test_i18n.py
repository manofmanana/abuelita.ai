from django.test import SimpleTestCase, Client
from django.urls import reverse


class I18NTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_set_language_and_render_about_in_spanish(self):
        """Post to the set_language view and confirm About page renders in Spanish."""
        # Resolve the set_language url (provided by django.conf.urls.i18n)
        set_lang_url = reverse("set_language")

        # Post to set language to Spanish and follow redirects
        resp = self.client.post(set_lang_url, {"language": "es", "next": "/about/"}, follow=True)
        self.assertIn(resp.status_code, (200, 302))

        # Now request the about page and expect Spanish translation text
        about_url = reverse("translator:about")
        resp2 = self.client.get(about_url)
        content = resp2.content.decode("utf-8")

        # Key Spanish fragment from about.html
        self.assertIn("Para mi Abuelita", content)
