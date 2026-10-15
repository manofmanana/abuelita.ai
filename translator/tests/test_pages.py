from django.test import TestCase
from django.urls import reverse


class BasicPageTests(TestCase):
    def test_about_page_renders(self):
        """Ensure about page renders with explicit host to avoid Bad Request host issues."""
        url = reverse("translator:about")
        resp = self.client.get(url, HTTP_HOST="127.0.0.1")
        self.assertEqual(resp.status_code, 200, f"About page failed: body snippet={resp.content[:120]}")

    def test_health_endpoint(self):
        url = reverse("translator:health")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(resp.content, {"ok": True, "view": "health", "about_url": "/about/"})
