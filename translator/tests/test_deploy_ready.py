import os
from django.conf import settings


def test_procfile_exists():
    # Ensure Procfile exists for platforms like Railway
    assert os.path.exists(os.path.join(settings.BASE_DIR, "Procfile"))


def test_runtime_txt_exists():
    assert os.path.exists(os.path.join(settings.BASE_DIR, "runtime.txt"))


def test_whitenoise_in_middleware():
    # WhiteNoise middleware should be present for serving static files in prod
    assert any("WhiteNoiseMiddleware" in m for m in settings.MIDDLEWARE)


def test_staticfiles_storage_set():
    assert hasattr(settings, "STATICFILES_STORAGE")
    # The default should include 'whitenoise' (but allow override via env)
    assert "whitenoise" in settings.STATICFILES_STORAGE
