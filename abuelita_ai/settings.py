"""
Django settings for Abuelita.ai project
Updated to correctly render Django templates (fixes raw {% trans %} issue)
"""

from pathlib import Path
import os

# =========================
# BASE PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
# SECURITY SETTINGS
# =========================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
# Allow passing ALLOWED_HOSTS via environment (comma-separated) for platforms
# like Railway. Defaults keep localhost and testserver so local tests and dev
# continue to work.
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")

# =========================
# APPLICATION DEFINITION
# =========================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "translator",  # your app
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise allows serving static files in production (used by Railway).
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # enables i18n
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "abuelita_ai.urls"

# =========================
# TEMPLATES
# =========================
# ✅ Fixed to use only app-level template discovery
# This ensures Django properly parses {% trans %} and {% block %} tags.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # leave empty so Django uses app templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "abuelita_ai.wsgi.application"

# =========================
# INTERNATIONALIZATION
# =========================
LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", "English"),
    ("es", "Español"),
]

TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# =========================
# STATIC FILES
# =========================
STATIC_URL = "/static/"

# Directories where Django looks for static files during development
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Directory used by collectstatic for production
STATIC_ROOT = BASE_DIR / "staticfiles"

# Use WhiteNoise storage backend in production for compressed static files.
# Keep as an env-driven setting so tests and local dev are unaffected if not
# needed.
STATICFILES_STORAGE = os.getenv(
    "STATICFILES_STORAGE",
    "whitenoise.storage.CompressedManifestStaticFilesStorage",
)

# When deployed behind a proxy (Railway, etc.), honor X-Forwarded-Proto
# if the environment requests it. This is safe to set; Django ignores it
# unless configured.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =========================
# DEFAULT PRIMARY KEY FIELD
# =========================
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

 # =========================
 # Database
 # =========================
 # Allow overriding the DB backend via environment variables (for example, to use
 # Postgres in production). If no DB is configured, default to a local sqlite3
 # file so the test runner and development environment work out of the box.
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
    }
}

# =========================
# LOGGING (optional - helpful during debug)
# =========================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
