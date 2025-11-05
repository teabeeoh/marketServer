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

