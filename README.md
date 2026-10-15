# 🌹 Abuelita.ai

*Para mi abuelita, Francisca Martínez — para que nunca más una abuela tenga que esperar a entender el mundo.*
*"So that never again will a grandmother have to wait to understand the world."*

[![CI](https://github.com/manofmanana/abuelita.ai/actions/workflows/ci.yml/badge.svg)](https://github.com/manofmanana/abuelita.ai/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)
![Django](https://img.shields.io/badge/django-6.1-0c4b33)
![License](https://img.shields.io/badge/license-MIT-green)

Abuelita.ai is a bilingual **English ⇄ Spanish** web app. It translates text and documents, and generates small lessons with pronunciation guides and a mini-quiz. Every page is available in English and Spanish.

## Why I built this

Spanish was my first language. My grandmother, Francisca Martínez, never learned English. I grew up reading her doctor's notes, letters and forms out loud, explaining what words meant, and teaching her how to say a phrase so she could feel confident on her own. Those small moments of understanding are the heart of this project: tools that bring language, context and a little warmth to the people who need them most.

## Features

**Translation Hub**
- Translate typed text, or upload a **TXT, DOCX or PDF** and download the translation
- Long documents are split on paragraph and sentence boundaries, so they aren't cut off at the translation service's per-request limit
- If text is already in the target language, it's translated the other way automatically (e.g. Spanish typed with "From: English")
- **Voice input** (🎤 Speak) and **Listen** (text-to-speech) in the browser via the Web Speech API
- Copy, download, swap languages; works without JavaScript too

**Learn with Abuelita**
- Type any topic (*food, travel, cook, toys…*) to get a bilingual micro-lesson:
  - Phrases grouped **Easy → Medium → Hard**, each expandable to show the other language
  - A **pronunciation guide** for every phrase (e.g. *mañana → ma nya na*) and a Listen button
  - Example sentences and a two-question **mini-quiz**. English speakers translate into Spanish; Spanish speakers translate into English.
- Lessons have shareable links (`/en/learn/?topic=food`)

**About**: the story of Francisca, from Nochistlán, Zacatecas.

**Fully bilingual UI**: switch between 🇺🇸 English and 🇲🇽 Español at `/en/…` and `/es/…`.

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Python 3.12+, Django 6.1, SQLite or Postgres (`DATABASE_URL`) |
| Translation | Google Translate (public endpoint, with deep-translator as a fallback) |
| Lessons | Rule-based generator in `ai_core/` with `inflect`; optional NLTK WordNet / spaCy for richer output |
| Documents | `pypdf`, `python-docx` |
| Frontend | Bootstrap 5.3, Bootstrap Icons, vanilla JS (no build step), Web Speech API |
| Serving | Gunicorn + WhiteNoise, Docker, or any Procfile host |
| Quality | pytest + pytest-django, Ruff, GitHub Actions |

## Quick start

Requires Python 3.12+.

```bash
git clone https://github.com/manofmanana/abuelita.ai.git
cd abuelita.ai

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

export DJANGO_DEBUG=1            # Windows PowerShell: $env:DJANGO_DEBUG=1
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000>.

> Using [uv](https://docs.astral.sh/uv/)? `uv venv && uv pip install -r requirements-dev.txt` works too.

## Configuration

Everything is configured with environment variables; see [`.env.example`](.env.example).

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_DEBUG` | `0` | Set to `1` for local development |
| `DJANGO_SECRET_KEY` | — | **Required in production** |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,testserver` | Comma-separated hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | — | e.g. `https://abuelita.example.com` |
| `DATABASE_URL` | SQLite | e.g. `postgres://user:pass@host/db` |
| `ABUELITA_MAX_UPLOAD_MB` | `5` | Upload size limit |
| `ABUELITA_MAX_TRANSLATE_CHARS` | `20000` | Longer documents are truncated, and the user is told |
| `ABUELITA_OFFLINE` | `0` | `1` skips all network calls (used by the tests) |

The old unprefixed `DEBUG`, `SECRET_KEY` and `ALLOWED_HOSTS` names still work.

## Tests and linting

```bash
python -m pytest -q        # runs offline; no network needed
ruff check . && ruff format --check .
```

CI runs lint, the translation-catalog check, Django system checks and the test suite on Python 3.12 and 3.13 for every push and pull request.

An optional Playwright smoke test lives in `e2e/playwright/` (run it against `runserver`).

## Deployment

**Docker**

```bash
docker build -t abuelita-ai .
docker run -p 8000:8000 -e DJANGO_SECRET_KEY=change-me -e DJANGO_ALLOWED_HOSTS=localhost abuelita-ai
```

**Render / Railway / Heroku-style hosts**: the `Procfile` runs migrations on release and starts Gunicorn. Set `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`, and run `python manage.py collectstatic --noinput` in the build step.

**PythonAnywhere**: point the WSGI file at `abuelita_ai.wsgi`, set the environment variables above, run `collectstatic`, and map `/static/` to the `staticfiles/` directory.

## Project structure

```
abuelita_ai/          Django project (settings, urls, wsgi/asgi)
ai_core/              Translation + lesson generation (framework-independent)
  translator.py       Chunked Google translation with caching and offline mode
  generator.py        Bilingual lesson builder
  enhancer.py         Pronunciation guide, difficulty, paraphrases
  data/               Topic vocabularies (food, toys, travel…)
translator/           Django app: views, forms, templates, static files, tests
locale/es/            Spanish translations (.po/.mo)
static/backgrounds/   Optimized WebP backgrounds and icons
scripts/              Template i18n checker
e2e/                  Optional Playwright test
```

## Updating translations

After changing `{% trans %}` strings, with GNU gettext installed:

```bash
python manage.py makemessages -l es --ignore=.venv
# edit locale/es/LC_MESSAGES/django.po
python manage.py compilemessages --ignore=.venv
```

Keep `{% trans %}` tags on one line; `scripts/check_trans_tags.py` (also run in CI) enforces this.

## Privacy

Text and documents are sent to Google Translate to be translated. Translated documents are kept only in the visitor's session, for download, and are never written to disk. Before a public launch, add a short notice telling users this.

## Roadmap

- Pluggable translation providers (official Google Cloud / DeepL API keys)
- Saved lessons and progress per user
- Evaluation harness (BLEU / BERTScore) on a curated example set
- Idioms and *dichos* section with cultural notes

## License

MIT — see [LICENSE](LICENSE).

---

*For Francisca Martínez — for the small, powerful lessons.* 🌹
