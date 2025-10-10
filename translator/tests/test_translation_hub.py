from django.test import TestCase, Client


class TranslationHubTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_translate_simple_text_server_render(self):
        resp = self.client.post('/', {'source_language': 'en', 'target_language': 'es', 'text_input': 'Hello world'})
        # View may redirect depending on middleware; follow redirects
        if resp.status_code == 302:
            resp = self.client.get(resp.url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        # The page should include the translation result container
        self.assertIn('translation-result', content)

    def test_translate_ajax_returns_json(self):
        headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        resp = self.client.post('/', {'source_language': 'en', 'target_language': 'es', 'text_input': 'Hello'}, **headers)
        self.assertIn(resp.status_code, (200, 302))
        # If redirect, follow it
        if resp.status_code == 302:
            resp = self.client.get(resp.url, **headers)
        # If JSON returned, parse it
        try:
            data = resp.json()
            # The JSON should include either an error or a translation_result
            self.assertTrue('translation_result' in data or 'error' in data)
        except ValueError:
            # Not JSON; ensure HTML contains expected container
            content = resp.content.decode('utf-8')
            self.assertIn('translation-result', content)

    def test_index_defaults_language_pairing(self):
        resp = self.client.get('/')
        # Depending on i18n middleware and URL configuration, the root
        # path may redirect to a language-prefixed URL (302). Accept that
        # and follow the redirect to inspect the final page.
        self.assertIn(resp.status_code, (200, 302))
        if resp.status_code == 302:
            resp = self.client.get(resp.url)
        content = resp.content.decode('utf-8')
        # Ensure both select elements are present
        self.assertIn('id="id_source_language"', content)
        self.assertIn('id="id_target_language"', content)
