# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python 3.11 Flask REST API server for financial market data, fetching stock quotes and financial statements from Yahoo Finance via the `yfinance` library, and AI-powered investment analyses via the Anthropic Claude API. Deployed with Gunicorn in Docker, served on port 9000.

## Commands

### Run Server
```bash
# Development
python -m flask run

# Production (Gunicorn)
gunicorn -c src/gunicorn.conf.py wsgi:app

# Docker
docker build . --tag marketserver:latest
docker run -p 9000:9000 marketserver:latest
```

### Install Dependencies
```bash
pip install flask yfinance gunicorn anthropic
pip install -r requirements-dev.txt  # adds pytest, pytest-cov, openpyxl
```

### Run Tests
```bash
pytest test_market_server.py -v -m "not integration"  # unit tests only (fast, mocked)
pytest test_market_server.py -v -m integration          # integration tests (real API calls)
pytest test_market_server.py -v                          # all tests
pytest test_market_server.py --cov=src --cov-report=html # with coverage
```

### Excel Template Filler
```bash
python src/fill_excel_template.py AAPL
python src/fill_excel_template.py SAP.DE output.xlsx
```

## Architecture

**Three-layer design:**

1. **API Layer** (`src/market_server.py`) — Flask routes:
   - `GET /market/quotes?symbols=AAPL,MSFT` — stock price quotes (JSON)
   - `GET /market/financials?symbol=AAPL&format=tsv` — financial statements (JSON or TSV)
   - `GET /market/analysis?company=AAPL` — AI investment analysis (Markdown); accepts name, ticker, ISIN, etc.

2. **Service Layer** (`src/financial_data_service.py`) — data fetching and processing:
   - Fetches income statement, balance sheet, cash flow via `yf.Ticker()`
   - Converts amounts to millions, calculates derived metrics
   - Supports JSON and TSV export with German number formatting (dot thousands, comma decimals)

   `src/analysis_service.py` — Anthropic Claude integration:
   - Reads `ANTHROPIC_API_KEY` from environment
   - Uses `claude-sonnet-4-6`, returns Markdown

3. **Utility** (`src/fill_excel_template.py`) — standalone script that fills `resources/excel_template.xlsx` with financial data (copies template, never modifies original)

**Entry point:** `src/wsgi.py` imports the Flask app for Gunicorn.

## Key Patterns

- **German localization**: Numbers formatted as `1.234.567,89` in TSV output
- **Flexible yfinance field mapping**: Tries multiple field name variants to handle API inconsistencies
- **Test isolation**: Unit tests mock yfinance entirely; integration tests (marked `@pytest.mark.integration`) make real API calls
- **pytest markers** configured in `src/pytest.ini`