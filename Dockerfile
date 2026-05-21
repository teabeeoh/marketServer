# Dockerfile
FROM python:3.11-slim

LABEL org.label-schema.schema-version="1.0"
LABEL maintainer="Thomas Bolz <thomas.bolz@gmail.com>"
LABEL org.label-schema.name="Stock Market Data Server"

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/*.py .
COPY resources/excel_template.xlsx /resources/excel_template.xlsx

# Umgebungsvariable ANTHROPIC_API_KEY beim Starten des Containers vom Host übernehmen:
# Beispiel: docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY ...
# Alternativ kann hier ein Default gesetzt werden:
# ENV ANTHROPIC_API_KEY=""

EXPOSE 9000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]