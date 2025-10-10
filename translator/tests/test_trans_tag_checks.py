from django.test import SimpleTestCase
from pathlib import Path
import importlib.util
import sys


class TransTagChecks(SimpleTestCase):
    """Fail tests if templates contain multi-line/split `{% trans %}` tags."""

    def test_no_multiline_trans_tags(self):
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "check_trans_tags.py"
        spec = importlib.util.spec_from_file_location("check_trans_tags", script_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        repo_root = Path(__file__).resolve().parents[2]
        failures = module.find_multiline_trans_tags(repo_root)
        if failures:
            msgs = []
            for fp, snippet in failures:
                msgs.append(f"File: {fp}\n{snippet}\n---\n")
            self.fail("Found multi-line/split {% trans %} occurrences:\n" + "\n".join(msgs))
