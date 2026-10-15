FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput

RUN useradd --create-home app && chown -R app /app
USER app

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn abuelita_ai.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --timeout 60"]
