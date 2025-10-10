"""Integration-style tests ensuring new AI, LMS, and OOAPI layers import and
return safe values when optional dependencies or external services are missing.
"""
from django.test import TestCase

from ai_engines.local_generator import generate_text
from ai_engines.translator import translate_to_spanish
from app.lms_bridge import create_course
from app.ooapi_serializers import export_course_to_ooapi


class TestLocalAI(TestCase):
    def test_ai_generates_text(self):
        text = generate_text("Explain Día de los Muertos.")
        assert isinstance(text, str)
        assert len(text) > 0

    def test_translation_works(self):
        result = translate_to_spanish("Good evening")
        assert isinstance(result, str)
        assert len(result) > 0


class TestMoodleBridge(TestCase):
    def test_create_course_returns_dict(self):
        res = create_course("Test course")
        assert isinstance(res, dict)


class TestOOAPIExport(TestCase):
    def test_ooapi_course_serializer_output(self):
        class MockCourse:
            id = 1
            title = "Greetings"
            description = "Learn Spanish greetings"
            language = "es"

        data = export_course_to_ooapi(MockCourse())
        assert isinstance(data, dict)
        assert "id" in data and "provider" in data
