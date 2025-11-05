import pytest
from unittest.mock import Mock, patch
from market_server import app


@pytest.fixture
def client():
    """Flask test client fixture."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestMarketQuotesEndpoint:
    """Test suite for the /market/quotes endpoint."""

    def test_get_quotes_missing_symbols_parameter(self, client):
        """Test that the endpoint returns 400 when symbols parameter is missing."""
        response = client.get('/market/quotes')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == "Parameter 'symbols' missing"

    def test_get_quotes_empty_symbols_parameter(self, client):
        """Test that the endpoint returns 400 when symbols parameter is empty."""
        response = client.get('/market/quotes?symbols=')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    @patch('market_server.yf.Tickers')
    def test_get_quotes_single_symbol(self, mock_tickers_class, client):
        """Test getting quotes for a single symbol."""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.info = {
            'currentPrice': 150.25,
            'currency': 'USD'
        }

        mock_tickers_instance = Mock()
        mock_tickers_instance.tickers = {'AAPL': mock_ticker}
        mock_tickers_class.return_value = mock_tickers_instance

        # Make request
        response = client.get('/market/quotes?symbols=AAPL')

        # Assertions
        assert response.status_code == 200
        data = response.get_json()
        assert 'AAPL' in data
        assert data['AAPL']['price'] == 150.25
        assert data['AAPL']['currency'] == 'USD'

        # Verify yfinance was called correctly
        mock_tickers_class.assert_called_once_with('AAPL')

    @patch('market_server.yf.Tickers')
    def test_get_quotes_multiple_symbols(self, mock_tickers_class, client):
        """Test getting quotes for multiple symbols."""
        # Setup mock
        mock_ticker_aapl = Mock()
        mock_ticker_aapl.info = {
            'currentPrice': 150.25,
            'currency': 'USD'
        }

        mock_ticker_googl = Mock()
        mock_ticker_googl.info = {
            'currentPrice': 2800.50,
            'currency': 'USD'
        }

        mock_ticker_tsla = Mock()
        mock_ticker_tsla.info = {
            'currentPrice': 245.75,
            'currency': 'USD'
        }

        mock_tickers_instance = Mock()
        mock_tickers_instance.tickers = {
            'AAPL': mock_ticker_aapl,
            'GOOGL': mock_ticker_googl,
            'TSLA': mock_ticker_tsla
        }
        mock_tickers_class.return_value = mock_tickers_instance

        # Make request
        response = client.get('/market/quotes?symbols=AAPL,GOOGL,TSLA')

        # Assertions
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 3

        assert data['AAPL']['price'] == 150.25
        assert data['AAPL']['currency'] == 'USD'

        assert data['GOOGL']['price'] == 2800.50
        assert data['GOOGL']['currency'] == 'USD'

        assert data['TSLA']['price'] == 245.75
        assert data['TSLA']['currency'] == 'USD'

        # Verify yfinance was called with space-separated symbols
        mock_tickers_class.assert_called_once_with('AAPL GOOGL TSLA')

    @patch('market_server.yf.Tickers')
    def test_get_quotes_with_spaces_in_symbols(self, mock_tickers_class, client):
        """Test that spaces in the symbols parameter are handled correctly."""
        # Setup mock
        mock_ticker_aapl = Mock()
        mock_ticker_aapl.info = {
            'currentPrice': 150.25,
            'currency': 'USD'
        }

        mock_ticker_msft = Mock()
        mock_ticker_msft.info = {
            'currentPrice': 350.00,
            'currency': 'USD'
        }

        mock_tickers_instance = Mock()
        mock_tickers_instance.tickers = {
            'AAPL': mock_ticker_aapl,
            'MSFT': mock_ticker_msft
        }
        mock_tickers_class.return_value = mock_tickers_instance

        # Make request with spaces around symbols
        response = client.get('/market/quotes?symbols=AAPL, MSFT')

        # Assertions
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert 'AAPL' in data
        assert 'MSFT' in data

    @patch('market_server.yf.Tickers')
    def test_get_quotes_missing_price_data(self, mock_tickers_class, client):
        """Test handling of missing price data in yfinance response."""
        # Setup mock with missing data
        mock_ticker = Mock()
        mock_ticker.info = {}  # Empty info, no currentPrice or currency

        mock_tickers_instance = Mock()
        mock_tickers_instance.tickers = {'INVALID': mock_ticker}
        mock_tickers_class.return_value = mock_tickers_instance

        # Make request
        response = client.get('/market/quotes?symbols=INVALID')

        # Assertions
        assert response.status_code == 200
        data = response.get_json()
        assert 'INVALID' in data
        assert data['INVALID']['price'] is None
        assert data['INVALID']['currency'] is None

    @patch('market_server.yf.Tickers')
    def test_get_quotes_partial_data(self, mock_tickers_class, client):
        """Test handling of partial data (only price or only currency)."""
        # Setup mock with partial data
        mock_ticker = Mock()
        mock_ticker.info = {
            'currentPrice': 100.50
            # Missing currency
        }

        mock_tickers_instance = Mock()
        mock_tickers_instance.tickers = {'PARTIAL': mock_ticker}
        mock_tickers_class.return_value = mock_tickers_instance

        # Make request
        response = client.get('/market/quotes?symbols=PARTIAL')

        # Assertions
        assert response.status_code == 200
        data = response.get_json()
        assert data['PARTIAL']['price'] == 100.50
        assert data['PARTIAL']['currency'] is None

    @patch('market_server.yf.Tickers')
    def test_get_quotes_different_currencies(self, mock_tickers_class, client):
        """Test getting quotes with different currencies."""
        # Setup mock
        mock_ticker_dax = Mock()
        mock_ticker_dax.info = {
            'currentPrice': 15500.00,
            'currency': 'EUR'
        }

        mock_ticker_nikkei = Mock()
        mock_ticker_nikkei.info = {
            'currentPrice': 28000.00,
            'currency': 'JPY'
        }

        mock_tickers_instance = Mock()
        mock_tickers_instance.tickers = {
            '^GDAXI': mock_ticker_dax,
            '^N225': mock_ticker_nikkei
        }
        mock_tickers_class.return_value = mock_tickers_instance

        # Make request
        response = client.get('/market/quotes?symbols=^GDAXI,^N225')

        # Assertions
        assert response.status_code == 200
        data = response.get_json()
        assert data['^GDAXI']['currency'] == 'EUR'
        assert data['^N225']['currency'] == 'JPY'

    @patch('market_server.yf.Tickers')
    def test_get_quotes_yfinance_exception(self, mock_tickers_class, client):
        """Test handling of yfinance exceptions."""
        # Setup mock to raise exception
        mock_tickers_class.side_effect = Exception("yfinance API error")

        # Make request
        with pytest.raises(Exception):
            response = client.get('/market/quotes?symbols=AAPL')

    @patch('market_server.yf.Tickers')
    def test_get_quotes_response_format(self, mock_tickers_class, client):
        """Test that the response format is correct JSON."""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.info = {
            'currentPrice': 100.0,
            'currency': 'USD'
        }

        mock_tickers_instance = Mock()
        mock_tickers_instance.tickers = {'TEST': mock_ticker}
        mock_tickers_class.return_value = mock_tickers_instance

        # Make request
        response = client.get('/market/quotes?symbols=TEST')

        # Assertions
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = response.get_json()
        assert isinstance(data, dict)
        assert isinstance(data['TEST'], dict)
        assert 'price' in data['TEST']
        assert 'currency' in data['TEST']


@pytest.mark.integration
class TestMarketQuotesIntegration:
    """Integration tests for /market/quotes endpoint with real yfinance calls.

    These tests make actual API calls to Yahoo Finance and may be slower.
    They can be skipped with: pytest -m "not integration"
    """

    def test_get_quotes_single_real_symbol(self, client):
        """Test getting real quotes for a single popular symbol (AAPL)."""
        response = client.get('/market/quotes?symbols=AAPL')

        assert response.status_code == 200
        data = response.get_json()

        # Verify structure
        assert 'AAPL' in data
        assert 'price' in data['AAPL']
        assert 'currency' in data['AAPL']

        # Verify data types and reasonable values
        if data['AAPL']['price'] is not None:
            assert isinstance(data['AAPL']['price'], (int, float))
            assert data['AAPL']['price'] > 0  # Stock price should be positive

        if data['AAPL']['currency'] is not None:
            assert isinstance(data['AAPL']['currency'], str)
            assert len(data['AAPL']['currency']) > 0

    def test_get_quotes_multiple_real_symbols(self, client):
        """Test getting real quotes for multiple popular symbols."""
        response = client.get('/market/quotes?symbols=AAPL,MSFT,GOOGL')

        assert response.status_code == 200
        data = response.get_json()

        # Verify all requested symbols are in response
        assert 'AAPL' in data
        assert 'MSFT' in data
        assert 'GOOGL' in data

        # Check each symbol has the required fields
        for symbol in ['AAPL', 'MSFT', 'GOOGL']:
            assert 'price' in data[symbol]
            assert 'currency' in data[symbol]

            # If data is available, verify it's reasonable
            if data[symbol]['price'] is not None:
                assert isinstance(data[symbol]['price'], (int, float))
                assert data[symbol]['price'] > 0

    def test_get_quotes_real_etf_symbol(self, client):
        """Test getting real quotes for an ETF (SPY - S&P 500 ETF)."""
        response = client.get('/market/quotes?symbols=SPY')

        assert response.status_code == 200
        data = response.get_json()

        assert 'SPY' in data
        assert 'price' in data['SPY']
        assert 'currency' in data['SPY']

        # SPY should have valid data
        if data['SPY']['price'] is not None:
            assert isinstance(data['SPY']['price'], (int, float))
            assert data['SPY']['price'] > 0

        if data['SPY']['currency'] is not None:
            assert data['SPY']['currency'] == 'USD'

    def test_get_quotes_real_international_symbols(self, client):
        """Test getting real quotes for international symbols with different currencies."""
        # Using well-known international stocks
        response = client.get('/market/quotes?symbols=NESN.SW,7203.T')

        assert response.status_code == 200
        data = response.get_json()

        # NESN.SW is Nestlé (Swiss)
        assert 'NESN.SW' in data
        assert 'price' in data['NESN.SW']
        assert 'currency' in data['NESN.SW']

        # 7203.T is Toyota (Japanese)
        assert '7203.T' in data
        assert 'price' in data['7203.T']
        assert 'currency' in data['7203.T']

    def test_get_quotes_real_index_symbols(self, client):
        """Test getting real quotes for market indices."""
        response = client.get('/market/quotes?symbols=^GSPC,^DJI')

        assert response.status_code == 200
        data = response.get_json()

        # ^GSPC is S&P 500 Index
        assert '^GSPC' in data
        # ^DJI is Dow Jones Industrial Average
        assert '^DJI' in data

        for symbol in ['^GSPC', '^DJI']:
            assert 'price' in data[symbol]
            assert 'currency' in data[symbol]

            if data[symbol]['price'] is not None:
                assert isinstance(data[symbol]['price'], (int, float))
                # Indices should have positive values
                assert data[symbol]['price'] > 0

    def test_get_quotes_real_invalid_symbol(self, client):
        """Test getting quotes for an invalid/non-existent symbol."""
        response = client.get('/market/quotes?symbols=INVALIDTICKER123')

        assert response.status_code == 200
        data = response.get_json()

        # Should still return a response, but data may be None/null
        assert 'INVALIDTICKER123' in data
        assert 'price' in data['INVALIDTICKER123']
        assert 'currency' in data['INVALIDTICKER123']

    def test_get_quotes_real_mixed_valid_invalid_symbols(self, client):
        """Test getting quotes with a mix of valid and invalid symbols."""
        response = client.get('/market/quotes?symbols=AAPL,INVALIDTICKER123,MSFT')

        assert response.status_code == 200
        data = response.get_json()

        # All symbols should be in response
        assert 'AAPL' in data
        assert 'INVALIDTICKER123' in data
        assert 'MSFT' in data

        # Valid symbols should have data
        if data['AAPL']['price'] is not None:
            assert data['AAPL']['price'] > 0

        if data['MSFT']['price'] is not None:
            assert data['MSFT']['price'] > 0

    def test_get_quotes_real_cryptocurrency(self, client):
        """Test getting quotes for cryptocurrency symbols."""
        response = client.get('/market/quotes?symbols=BTC-USD,ETH-USD')

        assert response.status_code == 200
        data = response.get_json()

        assert 'BTC-USD' in data
        assert 'ETH-USD' in data

        for symbol in ['BTC-USD', 'ETH-USD']:
            assert 'price' in data[symbol]
            assert 'currency' in data[symbol]

            if data[symbol]['price'] is not None:
                assert isinstance(data[symbol]['price'], (int, float))
                assert data[symbol]['price'] > 0


