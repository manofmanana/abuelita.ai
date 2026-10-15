from django.test import SimpleTestCase
from django.utils import translation


class PagesI18nTests(SimpleTestCase):
    def assertSpanishFooter(self, content: str):
        self.assertIn("Texto a voz", content)
        self.assertIn("Desarrollado con Django e IA", content)

    def test_index_in_spanish(self):
        with translation.override("es"):
            response = self.client.get("/es/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        # Page-specific translated fragment
        self.assertIn("Centro de Traducción", content)
        self.assertSpanishFooter(content)

    def test_learn_in_spanish(self):
        with translation.override("es"):
            response = self.client.get("/es/learn/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("Centro de aprendizaje de idiomas", content)
        self.assertSpanishFooter(content)

    def test_culture_in_spanish(self):
        # Culture page was removed; expect 404
        with translation.override("es"):
            response = self.client.get("/es/culture/")
        self.assertEqual(response.status_code, 404)

    def test_about_in_spanish(self):
        with translation.override("es"):
            response = self.client.get("/es/about/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        # Dedication line appears in Spanish
        self.assertIn("Para que nunca más una abuela tenga que esperar a entender el mundo.", content)
        self.assertSpanishFooter(content)
