# Market-Server

Simple Server that provides some REST endpoints to retrieve stockprices for yahoo ticker symbols, as well as AI-powered investment analyses via the Anthropic Claude API.

## API Endpoints

### GET /market/quotes

Retrieves stock quotes for the specified ticker symbols.

**Parameters:**

- `symbols` (required): Comma-separated list of ticker symbols (e.g., `AAPL,GOOGL,MSFT`)

**Response:**

```json
{
  "AAPL": {
    "price": 150.25,
    "currency": "USD"
  }
}
```

### GET /market/financials

Retrieves comprehensive financial data for a ticker symbol across all available years.

**Parameters:**

- `symbol` (required): Single ticker symbol (e.g., `AAPL`, `MSFT`, `SAP.DE`)
- `format` (optional): Response format - `json` or `tsv` (default: `json`)

**Response (JSON format):**

```json
{
  "symbol": "AAPL",
  "count": 5,
  "years": [
    {
      "Year": "2025-09-30",
      "Total Revenue (mn)": 416161.0,
      "Net Income Common Stockholders (mn)": 112010.0,
      "Free Cash Flow (mn)": 98767.0,
      "Dividend per Share": 1.04,
      "Ordinary Shares Number (mn)": 14773.26,
      "Stockholders Equity (mn)": 73733.0,
      "Total Assets (mn)": 359241.0,
      "Goodwill (mn)": null,
      "Other Intangible Assets (mn)": null
    }
  ]
}
```

**Response (TSV format):**
Tab-delimited data with German number formatting (thousand separator: dot, decimal separator: comma).
Perfect for copy-pasting into Excel.

**Usage Examples:**

```bash
# Get financial data in JSON format
curl "http://localhost:5000/market/financials?symbol=AAPL&format=json"

# Get financial data in TSV format (German Excel compatible)
curl "http://localhost:5000/market/financials?symbol=AAPL&format=tsv" > aapl_financials.tsv
```

````

### GET /market/analysis

Generates an AI-powered investment analysis for a given company using the Anthropic Claude API. The response is Markdown-formatted text suitable for direct rendering.

**Prerequisites:** The environment variable `ANTHROPIC_API_KEY` must be set.

**Parameters:**

- `company` (required): Company identifier — ticker symbol, company name, ISIN, or any other recognizable identifier (e.g., `AAPL`, `Apple Inc`, `US0378331005`)

**Response:**

Markdown text (`text/markdown; charset=utf-8`) containing a structured investment analysis, typically covering business overview, financial highlights, strengths and risks, and an investment verdict.

**Error responses:**

| Status | Reason |
|--------|--------|
| 400 | `company` parameter missing |
| 503 | `ANTHROPIC_API_KEY` not set |
| 502 | Anthropic API error |
| 500 | Unexpected server error |

**Usage Examples:**

```bash
# Analyse by ticker symbol
curl "http://localhost:5000/market/analysis?company=AAPL"

# Analyse by company name
curl "http://localhost:5000/market/analysis?company=SAP+SE"

# Analyse by ISIN
curl "http://localhost:5000/market/analysis?company=US0378331005"

# Save result as Markdown file
curl "http://localhost:5000/market/analysis?company=AAPL" > aapl_analysis.md
```

**Note:** This endpoint calls the Claude API and may take several seconds to complete. For GUI integrations, a streaming variant (`/market/analysis/stream`) using Server-Sent Events (SSE) is preferable to avoid long blocking waits — see the architecture notes in `CLAUDE.md`.

---

## Development

### Running Tests

The test suite includes both **unit tests** (with mocked yfinance calls) and **integration tests** (with real API calls).

```bash
# Install development dependencies
uv sync

# Run all tests (unit + integration)
uv run pytest tests/ -v

# Run only unit tests (fast, no real API calls)
uv run pytest tests/ -v -m "not integration"

# Run only integration tests (slower, makes real yfinance API calls)
uv run pytest tests/ -v -m integration

# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run tests with coverage (unit tests only)
uv run pytest tests/ -m "not integration" --cov=src --cov-report=html
````

### Test Suite Overview

#### Unit Tests (`TestMarketQuotesEndpoint`)

Fast tests using mocked yfinance responses:

- ✅ Missing parameter validation
- ✅ Empty parameter validation
- ✅ Single and multiple symbol queries
- ✅ Handling of whitespace in parameters
- ✅ Missing data handling (None values)
- ✅ Partial data scenarios
- ✅ Multiple currencies
- ✅ Exception handling
- ✅ Response format validation

#### Integration Tests (`TestMarketQuotesIntegration`)

Real API calls to Yahoo Finance (marked with `@pytest.mark.integration`):

- ✅ Single real symbol (AAPL)
- ✅ Multiple real symbols (AAPL, MSFT, GOOGL)
- ✅ Real ETF symbol (SPY)
- ✅ International symbols with different currencies (Nestlé, Toyota)
- ✅ Market indices (S&P 500, Dow Jones)
- ✅ Invalid/non-existent symbols
- ✅ Mixed valid and invalid symbols
- ✅ Cryptocurrencies (BTC-USD, ETH-USD)

#### Unit Tests (`TestAnalysisEndpoint`)

Fast tests using a mocked Anthropic client (no real API calls, no `ANTHROPIC_API_KEY` required):

- ✅ Missing parameter validation
- ✅ Correct `text/markdown` content type
- ✅ Company identifier forwarded to Claude
- ✅ Whitespace stripping
- ✅ Missing API key → 503
- ✅ Anthropic API error → 502
- ✅ Multiple content blocks (non-text blocks ignored)

#### Integration Tests (`TestAnalysisIntegration`)

Real API calls to Anthropic Claude (require `ANTHROPIC_API_KEY` and incur API costs):

- ✅ Ticker symbol input (AAPL)
- ✅ Full company name input (Apple Inc)

**Note:** Integration tests require internet connectivity and may be slower due to real API calls. Use `-m "not integration"` during development for faster feedback.

## Excel Template Filler Script

The `fill_excel_template.py` script retrieves financial data from Yahoo Finance and fills an Excel template with the data.

**Important:** The template file is **never modified** - it is only read and copied to create a new output file.

### Usage

```bash
# Basic usage (creates AAPL_financials.xlsx)
python fill_excel_template.py AAPL

# Specify custom output file
python fill_excel_template.py AAPL my_output.xlsx

# Use a different template
python fill_excel_template.py SAP.DE --template path/to/custom_template.xlsx

# International symbols
python fill_excel_template.py SAP.DE
```

### Features

- 📊 Fetches financial data from Yahoo Finance (using the existing `financial_data_service.py`)
- 📋 Creates a new Excel file based on the template (template is **never modified**)
- ✏️ Fills the new file with retrieved financial data
- 💾 Saves the result as a new Excel file
- 🌍 Supports international ticker symbols (e.g., `SAP.DE`, `NESN.SW`)
- 🔒 Template file protection - the original template remains unchanged

### Template Structure

The script expects an Excel template (`resources/excel_template.xlsx`) with the following structure:

- **Row 1-4**: Metadata (Name, ISIN, Sector, Currency, Dashboard)
- **Row 5**: Headers (Jahr, Umsatz, J, FCF, Dividende, etc.)
- **Row 6+**: Data rows (populated by the script)

### Column Mapping

The script maps the following financial data to Excel columns:

| Excel Column | Financial Data                         |
| ------------ | -------------------------------------- |
| A            | Year                                   |
| B            | Total Revenue (mn)                     |
| C            | Net Income Common Stockholders (mn)    |
| D            | Free Cash Flow (mn)                    |
| E            | Dividend per Share                     |
| F            | Ordinary Shares Number (mn)            |
| G            | Stockholders Equity (mn)               |
| H            | Total Assets (mn)                      |
| I            | Goodwill (mn)                          |
| J            | Other Intangible Assets (mn)           |

### Requirements

All runtime dependencies (including `openpyxl`, `pandas`, and `yfinance`) are declared in `pyproject.toml`. Install them with:

```bash
uv sync
```


