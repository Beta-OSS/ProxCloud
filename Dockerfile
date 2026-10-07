FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

# Vendor HTMX so pages are served from 'self' (strict CSP, no third-party scripts at runtime).
RUN python -c "import urllib.request; urllib.request.urlretrieve('https://cdn.jsdelivr.net/npm/htmx.org@2.0.4/dist/htmx.min.js', 'app/static/htmx.min.js')" \
    && pip install .

COPY alembic.ini ./
COPY alembic ./alembic

RUN useradd --system --uid 10001 --no-create-home portal && chown -R portal /app
USER portal

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
