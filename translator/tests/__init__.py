"""Package marker for translator tests.

Keeps the translator.tests directory importable by the test runner.

Unittest's discovery sometimes imports this package using the top-level name
"tests" (depending on sys.path manipulation during discovery). When that
happens the loader reports an import error because it expects the package to
be importable as ``translator.tests``. To make discovery robust in that
environment we detect the accidental import-as-"tests" and rebind the module
object in ``sys.modules`` so both names point to the same module and the
package metadata reflects the expected package name.
"""

import sys
import os

# Defensive handling: unittest discovery (or other import hooks) sometimes
# import this package using a different top-level name (for example 'tests').
# If that happens, rebind the module object under the canonical
# 'translator.tests' key in sys.modules so discovery and other tooling see a
# consistent package name and location.
mod_file = globals().get('__file__')
canonical_key = 'translator.tests'
if __name__ != canonical_key:
	try:
		if mod_file and (os.path.sep + 'translator' + os.path.sep + 'tests') in mod_file.replace('/', os.path.sep):
			# Register the currently-imported module object under the canonical
			# key if it's not already present. This makes unittest's loader
			# less likely to complain about an incorrectly-named 'tests'
			# module.
			# Ensure both 'translator.tests' and top-level 'tests' reference the
			# same module object so unittest discovery doesn't misidentify the
			# package location.
			sys.modules.setdefault(canonical_key, sys.modules.get(__name__))
			# Also ensure the top-level 'tests' name points to this package when
			# it's been imported that way by the test loader.
			sys.modules.setdefault('tests', sys.modules.get(__name__))
			mod = sys.modules.get(canonical_key)
			if mod is not None:
				try:
					mod.__name__ = canonical_key
				except Exception:
					pass
				try:
					mod.__package__ = canonical_key
				except Exception:
					pass
				# Ensure the module object also appears as the top-level 'tests'
				# package (some unittest loaders import tests as a top-level name).
				try:
					if 'tests' not in sys.modules:
						sys.modules['tests'] = mod
					# Make sure __path__ points to the tests directory so discovery can
					# locate test modules under the expected filesystem path.
					if hasattr(mod, '__file__'):
						mod_dir = os.path.dirname(mod.__file__)
						if getattr(mod, '__path__', None) != [mod_dir]:
							try:
								mod.__path__ = [mod_dir]
							except Exception:
								pass
				except Exception:
					pass
	except Exception:
		# Be defensive: nothing critical should break import-time here.
		pass
