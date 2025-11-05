# Market-Server
Simple Server that provides some REST endpoints to retrieve stockprices for yahoo ticker symbols.

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

## Development

### Running Tests

The test suite includes both **unit tests** (with mocked yfinance calls) and **integration tests** (with real API calls).

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests (unit + integration)
pytest test_market_server.py -v

# Run only unit tests (fast, no real API calls)
pytest test_market_server.py -v -m "not integration"

# Run only integration tests (slower, makes real yfinance API calls)
pytest test_market_server.py -v -m integration

# Run tests with coverage
pytest test_market_server.py --cov=market_server --cov-report=html

# Run tests with coverage (unit tests only)
pytest test_market_server.py -m "not integration" --cov=market_server --cov-report=html
```

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

**Note:** Integration tests require internet connectivity and may be slower due to real API calls. Use `-m "not integration"` during development for faster feedback.

