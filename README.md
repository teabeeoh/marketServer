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
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest test_market_server.py -v

# Run tests with coverage
pytest test_market_server.py --cov=market_server --cov-report=html
```

### Test Coverage
The test suite includes:
- ✅ Missing parameter validation
- ✅ Single and multiple symbol queries
- ✅ Handling of whitespace in parameters
- ✅ Missing data handling
- ✅ Partial data scenarios
- ✅ Multiple currencies
- ✅ Error handling
- ✅ Response format validation

