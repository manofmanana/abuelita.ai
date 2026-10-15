from django.test import SimpleTestCase


class FooterI18nTests(SimpleTestCase):
    def test_footer_translations_on_learn_and_culture(self):
        client = self.client

        # Learn page in Spanish
        from django.utils import translation

        with translation.override("es"):
            response = client.get("/es/learn/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("Texto a voz", content)
        self.assertIn("Desarrollado con Django e IA", content)
