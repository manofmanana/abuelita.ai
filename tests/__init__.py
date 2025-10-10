"""Compatibility shim package so unittest discovery that imports the top-level
'name "tests" resolves to the app package ``translator.tests``.

This repository keeps tests under the application package
``translator.tests``. Some environments (or Python/unittest versions) cause the
loader to import packages using the bare name "tests" during discovery which
leads to the ImportError seen in the CI. Creating this tiny shim ensures that
both import paths resolve to the same module object and that discovery finds
our tests consistently.
"""

import importlib
import sys

# Import the real tests package and register it under both names so importers
# using either path see the exact same module object.
_real = importlib.import_module("translator.tests")
# Ensure canonical key is present
sys.modules.setdefault("translator.tests", _real)
# Bind the top-level name to the same module so test discovery does not
# complain about an incorrectly-named module.
sys.modules.setdefault("tests", _real)

# Expose path and basic metadata to mimic a normal package
try:
    __path__ = _real.__path__  # type: ignore
except Exception:
    pass
try:
    __file__ = getattr(_real, "__file__", __file__)
except Exception:
    pass

# Re-export module attributes for convenience
from importlib import import_module as _import_module
for _name in ("__all__",):
    if hasattr(_real, _name):
        globals()[_name] = getattr(_real, _name)
