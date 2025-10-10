from django.test import TestCase, Client


class LearnCultureAjaxTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_learn_ajax_returns_json(self):
        resp = self.client.post('/en/learn/', {'input_text': 'legos'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json')
        data = resp.json()
        self.assertIn('lesson_struct', data)
        self.assertIn('lesson_output', data)

    def test_culture_ajax_returns_json(self):
        # Culture endpoint removed; should return 404
        resp = self.client.post('/en/culture/', {'cultural_topic': 'Pan de Muerto'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertIn(resp.status_code, (404, 405))

    def test_learn_non_ajax_renders_removed_message(self):
        resp = self.client.post('/en/learn/', {'input_text': 'Test lesson'})
        if resp.status_code == 302:
            resp = self.client.get(resp.url)
        content = resp.content.decode('utf-8')
        # The page should render the lesson result card
        self.assertIn('Lesson Result', content)

    def test_culture_non_ajax_renders_removed_message(self):
        resp = self.client.post('/en/culture/', {'cultural_topic': 'Pan de Muerto'})
        # Expect 404 or similar since the endpoint was removed
        self.assertIn(resp.status_code, (404, 405))
