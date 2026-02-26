import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import anthropic
from src.market_server import app


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


class TestFinancialsEndpoint:
    """Test suite for the /market/financials endpoint."""

    def test_get_financials_missing_symbol_parameter(self, client):
        """Test that the endpoint returns 400 when symbol parameter is missing."""
        response = client.get('/market/financials')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == "Parameter 'symbol' missing"

    def test_get_financials_invalid_format_parameter(self, client):
        """Test that the endpoint returns 400 for invalid format parameter."""
        response = client.get('/market/financials?symbol=AAPL&format=xml')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert "must be 'json' or 'tsv'" in data['error']

    @patch('financial_data_service.yf.Ticker')
    def test_get_financials_json_format(self, mock_ticker_class, client):
        """Test getting financials in JSON format."""
        # Setup mock
        mock_ticker = Mock()
        
        # Mock income statement
        mock_income_stmt = pd.DataFrame({
            pd.Timestamp('2023-12-31'): {
                'Total Revenue': 400000000000,
                'Net Income Common Stockholders': 100000000000
            }
        })
        
        # Mock balance sheet
        mock_balance_sheet = pd.DataFrame({
            pd.Timestamp('2023-12-31'): {
                'Ordinary Shares Number': 15000000000,
                'Stockholders Equity': 60000000000,
                'Total Assets': 350000000000,
                'Goodwill': 0,
                'Other Intangible Assets': 0
            }
        })
        
        # Mock cash flow
        mock_cash_flow = pd.DataFrame({
            pd.Timestamp('2023-12-31'): {
                'Free Cash Flow': 95000000000,
                'Cash Dividends Paid': -15000000000
            }
        })
        
        mock_ticker.income_stmt = mock_income_stmt
        mock_ticker.balance_sheet = mock_balance_sheet
        mock_ticker.cashflow = mock_cash_flow
        mock_ticker_class.return_value = mock_ticker
        
        # Make request
        response = client.get('/market/financials?symbol=AAPL&format=json')
        
        # Assertions
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = response.get_json()
        
        assert 'symbol' in data
        assert data['symbol'] == 'AAPL'
        assert 'years' in data
        assert 'count' in data
        assert data['count'] == 1
        assert len(data['years']) == 1
        
        # Check first year data
        year_data = data['years'][0]
        assert 'Year' in year_data
        assert 'Total Revenue (mn)' in year_data
        assert 'Dividend per Share' in year_data

    @patch('financial_data_service.yf.Ticker')
    def test_get_financials_tsv_format(self, mock_ticker_class, client):
        """Test getting financials in TSV format with German number formatting."""
        # Setup mock
        mock_ticker = Mock()
        
        # Mock income statement
        mock_income_stmt = pd.DataFrame({
            pd.Timestamp('2023-12-31'): {
                'Total Revenue': 400000000000,
                'Net Income Common Stockholders': 100000000000
            }
        })
        
        # Mock balance sheet
        mock_balance_sheet = pd.DataFrame({
            pd.Timestamp('2023-12-31'): {
                'Ordinary Shares Number': 15000000000,
                'Stockholders Equity': 60000000000,
                'Total Assets': 350000000000,
                'Goodwill': 0,
                'Other Intangible Assets': 0
            }
        })
        
        # Mock cash flow
        mock_cash_flow = pd.DataFrame({
            pd.Timestamp('2023-12-31'): {
                'Free Cash Flow': 95000000000,
                'Cash Dividends Paid': -15000000000
            }
        })
        
        mock_ticker.income_stmt = mock_income_stmt
        mock_ticker.balance_sheet = mock_balance_sheet
        mock_ticker.cashflow = mock_cash_flow
        mock_ticker_class.return_value = mock_ticker
        
        # Make request
        response = client.get('/market/financials?symbol=AAPL&format=tsv')
        
        # Assertions
        assert response.status_code == 200
        assert response.content_type.startswith('text/tab-separated-values')
        
        # Check TSV content
        tsv_data = response.data.decode('utf-8')
        assert '\t' in tsv_data  # Tab-delimited
        assert ',' in tsv_data  # German decimal separator
        assert '.' in tsv_data  # German thousand separator
        assert 'Year' in tsv_data
        assert 'Total Revenue (mn)' in tsv_data

    @patch('financial_data_service.yf.Ticker')
    def test_get_financials_invalid_ticker(self, mock_ticker_class, client):
        """Test handling of invalid ticker symbol."""
        # Setup mock to return empty data
        mock_ticker = Mock()
        mock_ticker.income_stmt = pd.DataFrame()  # Empty dataframe
        mock_ticker.balance_sheet = pd.DataFrame()
        mock_ticker.cashflow = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker
        
        # Make request
        response = client.get('/market/financials?symbol=INVALID123')
        
        # Assertions
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    @patch('financial_data_service.yf.Ticker')
    def test_get_financials_default_format(self, mock_ticker_class, client):
        """Test that default format is JSON when format parameter is omitted."""
        # Setup mock
        mock_ticker = Mock()
        
        mock_income_stmt = pd.DataFrame({
            pd.Timestamp('2023-12-31'): {
                'Total Revenue': 400000000000,
                'Net Income Common Stockholders': 100000000000
            }
        })
        
        mock_balance_sheet = pd.DataFrame({
            pd.Timestamp('2023-12-31'): {
                'Ordinary Shares Number': 15000000000,
                'Stockholders Equity': 60000000000,
                'Total Assets': 350000000000
            }
        })
        
        mock_cash_flow = pd.DataFrame({
            pd.Timestamp('2023-12-31'): {
                'Free Cash Flow': 95000000000,
                'Cash Dividends Paid': -15000000000
            }
        })
        
        mock_ticker.income_stmt = mock_income_stmt
        mock_ticker.balance_sheet = mock_balance_sheet
        mock_ticker.cashflow = mock_cash_flow
        mock_ticker_class.return_value = mock_ticker
        
        # Make request without format parameter
        response = client.get('/market/financials?symbol=AAPL')
        
        # Assertions
        assert response.status_code == 200
        assert response.content_type == 'application/json'


class TestAnalysisEndpoint:
    """Test suite for the /market/analysis endpoint."""

    def test_get_analysis_missing_company_parameter(self, client):
        """Test that the endpoint returns 400 when company parameter is missing."""
        response = client.get('/market/analysis')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == "Parameter 'company' missing"

    @patch('analysis_service.build_client')
    def test_get_analysis_returns_markdown(self, mock_build_client, client):
        """Test that the endpoint returns Markdown content for a valid company."""
        mock_message = Mock()
        mock_block = Mock()
        mock_block.type = 'text'
        mock_block.text = '# Investment Analysis\n\nThis is a test analysis.'
        mock_message.content = [mock_block]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_build_client.return_value = mock_client

        response = client.get('/market/analysis?company=AAPL')

        assert response.status_code == 200
        assert 'text/markdown' in response.content_type
        body = response.data.decode('utf-8')
        assert '# Investment Analysis' in body
        assert 'test analysis' in body

    @patch('analysis_service.build_client')
    def test_get_analysis_passes_company_to_claude(self, mock_build_client, client):
        """Test that the company parameter is forwarded to the Claude API."""
        mock_message = Mock()
        mock_block = Mock()
        mock_block.type = 'text'
        mock_block.text = '# Analysis'
        mock_message.content = [mock_block]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_build_client.return_value = mock_client

        client.get('/market/analysis?company=SAP')

        call_kwargs = mock_client.messages.create.call_args
        user_content = next(
            m['content'] for m in (call_kwargs.kwargs.get('messages') or [])
            if m['role'] == 'user'
        )
        # content is a list of blocks; find the text block
        text_block = next(b for b in user_content if b['type'] == 'text')
        assert 'SAP' in text_block['text']

    @patch('analysis_service.build_client')
    def test_get_analysis_with_context(self, mock_build_client, client):
        """Test that the context query param is appended to the system prompt."""
        mock_message = Mock()
        mock_block = Mock()
        mock_block.type = 'text'
        mock_block.text = '# Analysis'
        mock_message.content = [mock_block]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_build_client.return_value = mock_client

        client.get('/market/analysis?company=AAPL&context=Focus+on+ESG+risks')

        call_kwargs = mock_client.messages.create.call_args
        system = call_kwargs.kwargs.get('system', '')
        assert 'Focus on ESG risks' in system

    @patch('analysis_service.build_client')
    def test_post_analysis_with_company_form_field(self, mock_build_client, client):
        """Test that POST with company as a form field works."""
        mock_message = Mock()
        mock_block = Mock()
        mock_block.type = 'text'
        mock_block.text = '# Analysis'
        mock_message.content = [mock_block]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_build_client.return_value = mock_client

        response = client.post('/market/analysis', data={'company': 'MSFT'})
        assert response.status_code == 200
        assert 'text/markdown' in response.content_type

    def test_post_analysis_missing_company_returns_400(self, client):
        """Test that POST without company field returns 400."""
        response = client.post('/market/analysis', data={})
        assert response.status_code == 400
        assert response.get_json()['error'] == "Parameter 'company' missing"

    @patch('analysis_service.build_client')
    def test_post_analysis_with_context_form_field(self, mock_build_client, client):
        """Test that POST context form field is forwarded to the system prompt."""
        mock_message = Mock()
        mock_block = Mock()
        mock_block.type = 'text'
        mock_block.text = '# Analysis'
        mock_message.content = [mock_block]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_build_client.return_value = mock_client

        client.post('/market/analysis', data={'company': 'AAPL', 'context': 'Long-term horizon'})

        call_kwargs = mock_client.messages.create.call_args
        system = call_kwargs.kwargs.get('system', '')
        assert 'Long-term horizon' in system

    @patch('analysis_service.build_client')
    def test_post_analysis_with_file_upload(self, mock_build_client, client):
        """Test that uploaded files appear as document blocks before the text block."""
        mock_message = Mock()
        mock_block = Mock()
        mock_block.type = 'text'
        mock_block.text = '# Analysis'
        mock_message.content = [mock_block]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_build_client.return_value = mock_client

        pdf_bytes = b'%PDF-1.4 fake pdf content'
        response = client.post(
            '/market/analysis',
            data={'company': 'AAPL'},
            content_type='multipart/form-data',
        )
        # Baseline: no file → single text block
        call_kwargs = mock_client.messages.create.call_args
        user_content = next(
            m['content'] for m in call_kwargs.kwargs.get('messages', [])
            if m['role'] == 'user'
        )
        assert user_content[0]['type'] == 'text'

        # Now send with a file
        from io import BytesIO
        response = client.post(
            '/market/analysis',
            data={'company': 'AAPL', 'files': (BytesIO(pdf_bytes), 'report.pdf')},
            content_type='multipart/form-data',
        )
        assert response.status_code == 200
        call_kwargs = mock_client.messages.create.call_args
        user_content = next(
            m['content'] for m in call_kwargs.kwargs.get('messages', [])
            if m['role'] == 'user'
        )
        # Document block should come first, text block last
        assert user_content[0]['type'] == 'document'
        assert user_content[0]['title'] == 'report.pdf'
        assert user_content[-1]['type'] == 'text'
        assert 'AAPL' in user_content[-1]['text']

    @patch('analysis_service.build_client')
    def test_get_analysis_strips_whitespace_from_company(self, mock_build_client, client):
        """Test that leading/trailing whitespace is stripped from the company parameter."""
        mock_message = Mock()
        mock_block = Mock()
        mock_block.type = 'text'
        mock_block.text = 'Analysis result'
        mock_message.content = [mock_block]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_build_client.return_value = mock_client

        response = client.get('/market/analysis?company=+AAPL+')
        assert response.status_code == 200

    @patch('analysis_service.build_client')
    def test_get_analysis_missing_api_key(self, mock_build_client, client):
        """Test that a missing API key results in a 503 response."""
        mock_build_client.side_effect = EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is not set."
        )

        response = client.get('/market/analysis?company=AAPL')

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'ANTHROPIC_API_KEY' in data['error']

    @patch('analysis_service.build_client')
    def test_get_analysis_anthropic_api_error(self, mock_build_client, client):
        """Test that an Anthropic API error results in a 502 response."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = anthropic.APIStatusError(
            message="Service unavailable",
            response=Mock(status_code=503, headers={}),
            body={},
        )
        mock_build_client.return_value = mock_client

        response = client.get('/market/analysis?company=AAPL')

        assert response.status_code == 502
        data = response.get_json()
        assert 'error' in data
        assert 'Anthropic API error' in data['error']

    @patch('analysis_service.build_client')
    def test_get_analysis_multiple_text_blocks(self, mock_build_client, client):
        """Test that multiple text blocks in the response are joined correctly."""
        mock_block1 = Mock()
        mock_block1.type = 'text'
        mock_block1.text = 'Part one'

        mock_block2 = Mock()
        mock_block2.type = 'tool_use'  # Non-text block, should be ignored

        mock_block3 = Mock()
        mock_block3.type = 'text'
        mock_block3.text = 'Part two'

        mock_message = Mock()
        mock_message.content = [mock_block1, mock_block2, mock_block3]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_build_client.return_value = mock_client

        response = client.get('/market/analysis?company=AAPL')

        assert response.status_code == 200
        body = response.data.decode('utf-8')
        assert 'Part one' in body
        assert 'Part two' in body
        assert 'tool_use' not in body


@pytest.mark.integration
class TestAnalysisIntegration:
    """Integration tests for /market/analysis endpoint with real Anthropic API calls.

    These tests require ANTHROPIC_API_KEY to be set and will incur API costs.
    They can be skipped with: pytest -m "not integration"
    """

    def test_get_analysis_real_ticker(self, client):
        """Test getting a real investment analysis for AAPL."""
        response = client.get('/market/analysis?company=AAPL')

        assert response.status_code == 200
        assert 'text/markdown' in response.content_type
        body = response.data.decode('utf-8')
        assert len(body) > 100  # Should contain meaningful content
        assert '#' in body  # Should contain Markdown headings

    def test_get_analysis_real_company_name(self, client):
        """Test getting a real investment analysis using a full company name."""
        response = client.get('/market/analysis?company=Apple+Inc')

        assert response.status_code == 200
        body = response.data.decode('utf-8')
        assert len(body) > 100


@pytest.mark.integration
class TestFinancialsIntegration:
    """Integration tests for /market/financials endpoint with real yfinance calls.
    
    These tests make actual API calls to Yahoo Finance and may be slower.
    They can be skipped with: pytest -m "not integration"
    """

    def test_get_financials_real_symbol_json(self, client):
        """Test getting real financial data for AAPL in JSON format."""
        response = client.get('/market/financials?symbol=AAPL&format=json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify structure
        assert 'symbol' in data
        assert data['symbol'] == 'AAPL'
        assert 'years' in data
        assert 'count' in data
        assert data['count'] > 0
        
        # Check that we have year data
        assert len(data['years']) > 0
        
        # Check first year has expected fields
        first_year = data['years'][0]
        assert 'Year' in first_year
        assert 'Total Revenue (mn)' in first_year
        assert 'Net Income Common Stockholders (mn)' in first_year
        assert 'Free Cash Flow (mn)' in first_year
        assert 'Dividend per Share' in first_year

    def test_get_financials_real_symbol_tsv(self, client):
        """Test getting real financial data for MSFT in TSV format."""
        response = client.get('/market/financials?symbol=MSFT&format=tsv')
        
        assert response.status_code == 200
        assert response.content_type == 'text/tab-separated-values; charset=utf-8'
        
        # Check TSV content
        tsv_data = response.data.decode('utf-8')
        assert '\t' in tsv_data  # Tab-delimited
        assert 'Year' in tsv_data
        assert 'Total Revenue (mn)' in tsv_data
        
        # Verify German number formatting (should have dots and commas)
        lines = tsv_data.strip().split('\n')
        assert len(lines) > 1  # At least header + one data row

    def test_get_financials_real_invalid_symbol(self, client):
        """Test getting financials for an invalid symbol."""
        response = client.get('/market/financials?symbol=INVALIDTICKER999')
        
        # Should return 404 for invalid ticker
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_get_financials_real_international_symbol(self, client):
        """Test getting financials for an international symbol (SAP.DE)."""
        response = client.get('/market/financials?symbol=SAP.DE&format=json')
        
        # Should work for international symbols
        if response.status_code == 200:
            data = response.get_json()
            assert 'symbol' in data
            assert data['symbol'] == 'SAP.DE'
            assert 'years' in data





