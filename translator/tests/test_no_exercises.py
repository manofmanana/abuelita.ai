from django.test import SimpleTestCase
from ai_core import generate_lesson

class NoExercisesTests(SimpleTestCase):
    def test_generate_lesson_has_no_exercise_keys(self):
        ls = generate_lesson('test topic', as_struct=True)
        # Walk phrases and examples and ensure no keys start with 'exercise'
        for kind in ('phrases','examples'):
            for item in ls.get(kind, []):
                for k in item.keys():
                    self.assertFalse(k.startswith('exercise'), f"Found unexpected exercise key: {k}")
