from django.test import TestCase
from django.template import Template, Context, TemplateSyntaxError
from django.template.loader import get_template
import os
import glob


class TemplateValidationTests(TestCase):
    """
    Tests to ensure all templates are syntactically valid and prevent 500 errors.
    """
    
    def test_about_page_template_compiles(self):
        """Ensure about.html template compiles without syntax errors."""
        try:
            template = get_template('translator/about.html')
            # Try to render with empty context to catch any runtime template issues
            rendered = template.render({})
            self.assertIn('Francisca Martínez', rendered)
        except TemplateSyntaxError as e:
            self.fail(f"Template syntax error in about.html: {e}")
    
    def test_all_translator_templates_compile(self):
        """Ensure all templates in translator app compile without syntax errors."""
        template_dir = 'translator/templates/translator'
        if os.path.exists(template_dir):
            template_files = glob.glob(f"{template_dir}/*.html")
            for template_file in template_files:
                template_name = os.path.relpath(template_file, 'translator/templates').replace(os.sep, '/')
                with self.subTest(template=template_name):
                    try:
                        template = get_template(template_name)
                        # Basic compilation test
                        template.render({})
                    except TemplateSyntaxError as e:
                        self.fail(f"Template syntax error in {template_name}: {e}")
    
    def test_about_template_no_multiple_tags_per_line(self):
        """Ensure no line in about.html contains multiple Django template tags."""
        template_path = 'translator/templates/translator/about.html'
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Count template tag occurrences
                tag_count = line.count('{%')
                if tag_count > 1:
                    self.fail(
                        f"Line {line_num} in about.html contains {tag_count} template tags. "
                        f"Each tag should be on its own line to prevent parsing errors. "
                        f"Line content: {line.strip()}"
                    )
    
    def test_about_page_renders_successfully(self):
        """Test that the about page returns 200 and contains expected content."""
        # Follow redirects because LocaleMiddleware may redirect to a
        # language-prefixed URL (e.g. /en/about/). The test should verify
        # the final rendered page contents rather than the intermediate 302.
        response = self.client.get('/about/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Francisca Martínez')
        self.assertContains(response, 'Abuelita.ai')
        # Ensure it's not an error page
        self.assertNotContains(response, 'Server Error')
        self.assertNotContains(response, 'TemplateSyntaxError')