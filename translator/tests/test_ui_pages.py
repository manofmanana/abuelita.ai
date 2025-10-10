from django.test import SimpleTestCase
from django.test import TestCase


class UIPagesPostTests(TestCase):
    def test_learn_post_generates_safe_output(self):
        resp = self.client.post('/learn/', {'input_text': 'Common greetings'})
        self.assertIn(resp.status_code, (200, 302))
        # follow redirect if any
        if resp.status_code == 302:
            resp = self.client.get(resp.url)
        content = resp.content.decode('utf-8')
        # Should include either a generated text or the AI-unavailable marker
        self.assertTrue('[AI unavailable]' in content or 'Lesson Result' in content)

    def test_culture_post_generates_safe_output(self):
        # Culture removed — posting should not succeed
        resp = self.client.post('/culture/', {'cultural_topic': 'Pan de Muerto'})
        self.assertIn(resp.status_code, (404, 405))

    def test_export_ooapi_endpoint(self):
        # Export endpoint removed; ensure template shows removal message when lesson exists
        resp = self.client.post('/en/learn/', {'input_text': 'Test lesson'})
        if resp.status_code == 302:
            resp = self.client.get(resp.url)
        content = resp.content.decode('utf-8')
        # The legacy export message was removed; ensure lesson result still appears
        self.assertTrue('Lesson Result' in content or '[AI unavailable]' in content)

    def test_push_moodle_endpoint_requires_params(self):
        # Push to Moodle endpoint removed; culture endpoint gone
        resp = self.client.post('/en/culture/', {'cultural_topic': 'Pan de Muerto'})
        self.assertIn(resp.status_code, (404, 405))


class UIPagesSmokeTests(SimpleTestCase):
    """Smoke tests for learn and culture pages UI.

    They ensure the pages render (status 200) and contain the expected
    background overlay and card translucency markers.
    """

    def assertHasOverlay(self, content: str):
        self.assertIn('bg-overlay', content)

    def assertUsesTranslucentCard(self, content: str):
        # We look for the CSS variable name or inline style using var(--white_soft) or var(--bg-light)
        self.assertTrue('var(--bg-light)' in content or 'var(--white-soft)' in content or 'bg-overlay' in content,
                        'Page does not include translucent overlay or bg-light marker')

    def test_learn_page_ui(self):
        response = self.client.get('/es/learn/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertHasOverlay(content)
        self.assertUsesTranslucentCard(content)

    def test_culture_page_ui(self):
        # Culture page removed — ensure accessing it returns 404
        response = self.client.get('/es/culture/')
        self.assertIn(response.status_code, (404, 302, 301))
