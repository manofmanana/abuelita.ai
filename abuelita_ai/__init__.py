"""Project package initializer.

Some test helpers call translation.override() very early during collection which
may trigger Django's translation machinery before the apps registry is ready.
To keep tests stable in our environment we ensure Django is initialized when
the project package is imported. This is a safe no-op when Django is already
configured by the test runner or WSGI server.
"""
try:
	import django
	if not getattr(django.apps, 'apps', None) or not django.apps.apps.ready:
		try:
			django.setup()
		except Exception:
			# Let the test runner handle initialization if this fails.
			pass
except Exception:
	# If Django isn't installed in this environment, do nothing.
	pass
