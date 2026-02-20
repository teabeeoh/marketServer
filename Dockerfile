# Dockerfile
FROM python:3.11-slim

LABEL org.label-schema.schema-version="1.0"
LABEL maintainer="Thomas Bolz <thomas.bolz@gmail.com>"
LABEL org.label-schema.name="Stock Market Data Server"

WORKDIR /app

COPY src/*.py .
COPY requirements-dev.txt ./

RUN pip install --no-cache-dir flask yfinance gunicorn anthropic

EXPOSE 9000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
