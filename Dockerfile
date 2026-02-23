# Dockerfile
FROM python:3.11-slim

LABEL org.label-schema.schema-version="1.0"
LABEL maintainer="Thomas Bolz <thomas.bolz@gmail.com>"
LABEL org.label-schema.name="Stock Market Data Server"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY src/*.py .
COPY requirements-dev.txt ./

RUN pip install --no-cache-dir flask yfinance gunicorn anthropic

# Umgebungsvariable ANTHROPIC_API_KEY beim Starten des Containers vom Host übernehmen:
# Beispiel: docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY ...
# Alternativ kann hier ein Default gesetzt werden:
# ENV ANTHROPIC_API_KEY=""

EXPOSE 9000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
