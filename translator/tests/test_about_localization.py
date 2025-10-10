from django.test import TestCase


class AboutLocalizationTests(TestCase):
    def test_about_page_shows_english_by_default_with_en_prefix(self):
        resp = self.client.get('/en/about/')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        # key English phrases we added to the template
        self.assertIn('Abuelita.ai was created in honor of my grandmother', content)
        self.assertIn('Born in Nochistlán, Zacatecas, México', content)
        self.assertIn('To make learning languages feel like sitting at your grandmother', content)

    def test_about_page_shows_spanish_with_es_prefix(self):
        resp = self.client.get('/es/about/')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        # key Spanish phrases we added to the template
        self.assertIn('Abuelita.ai fue creado en honor a mi abuela', content)
        self.assertIn('Nacida en Nochistlán, Zacatecas, México', content)
        self.assertIn('Hacer que aprender idiomas se sienta como sentarse en la mesa de tu abuela', content)
