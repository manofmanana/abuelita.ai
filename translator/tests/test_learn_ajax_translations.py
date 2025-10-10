from django.test import TestCase
from django.urls import reverse
import json


class LearnAjaxTranslationsTests(TestCase):
    def test_learn_ajax_returns_spanish_for_phrases_and_examples(self):
        url = reverse('translator:learn')
        data = {'input_text': 'love'}
        resp = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        js = resp.json()
        self.assertIn('lesson_struct', js)
        ls = js['lesson_struct']
        self.assertIn('phrases', ls)
        self.assertIn('examples', ls)

        # Every phrase and example should include a non-empty Spanish string
        for p in ls.get('phrases', []):
            self.assertIn('en', p)
            self.assertIn('es', p)
            self.assertTrue(str(p.get('es') or '').strip(), msg=f"Missing ES for phrase: {p}")

        for e in ls.get('examples', []):
            self.assertIn('en', e)
            self.assertIn('es', e)
            self.assertTrue(str(e.get('es') or '').strip(), msg=f"Missing ES for example: {e}")
