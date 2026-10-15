import os

from django.conf import settings


def test_procfile_exists():
    assert os.path.exists(os.path.join(settings.BASE_DIR, "Procfile"))


def test_python_version_pinned():
    assert os.path.exists(os.path.join(settings.BASE_DIR, ".python-version"))


def test_whitenoise_in_middleware():
    assert any("WhiteNoiseMiddleware" in m for m in settings.MIDDLEWARE)


def test_staticfiles_storage_uses_whitenoise():
    assert "whitenoise" in settings.STORAGES["staticfiles"]["BACKEND"]


def test_secret_key_is_not_the_old_public_default():
    assert settings.SECRET_KEY != "dev-key"
