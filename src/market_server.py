import os
from flask import Flask, request, jsonify, Response
import yfinance as yf
import anthropic
from financial_data_service import fetch_financial_data, export_to_tsv, export_to_json
from analysis_service import get_investment_analysis

app = Flask(__name__)

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("WARNING: ANTHROPIC_API_KEY is not set — AI features will not work.")
else:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if "heX" in api_key:
        print("Using personal API key")
    else:
        print(f"Using CTSH API key ${api_key[:2]}...${api_key[-2:]}")

@app.route('/market/quotes', methods=['GET'])
def get_quotes():
    symbols = request.args.get('symbols')
    if not symbols:
        return jsonify({"error": "Parameter 'symbols' missing"}), 400

    symbol_list = [s.strip() for s in symbols.split(',')]
    tickers = yf.Tickers(" ".join(symbol_list))
    result = {}

    for symbol in symbol_list:
        try:
            info = tickers.tickers[symbol].info
            # log result to console
            print(f"{symbol}: {info}")
            price = info.get("currentPrice")
            currency = info.get("currency")
            result[symbol] = {
                "price": price,
                "currency": currency
            }
        except Exception:
            # If yfinance raises an exception (e.g., invalid symbol, HTTP 404),
            # return None values for that symbol instead of failing the entire request
            result[symbol] = {
                "price": None,
                "currency": None
            }

    return jsonify(result)


@app.route('/market/financials', methods=['GET'])
def get_financials():
    """
    Get comprehensive financial data for a ticker symbol.
    
    Query Parameters:
        symbol (required): Ticker symbol (e.g., AAPL, MSFT, SAP.DE)
        format (optional): Response format - 'json' or 'tsv' (default: 'json')
    
    Returns:
        JSON or TSV formatted financial data for all available years
    """
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "Parameter 'symbol' missing"}), 400
    
    # Get format parameter (default to json)
    response_format = request.args.get('format', 'json').lower()
    if response_format not in ['json', 'tsv']:
        return jsonify({"error": "Parameter 'format' must be 'json' or 'tsv'"}), 400
    
    try:
        # Fetch financial data
        df = fetch_financial_data(symbol.strip())
        
        if response_format == 'tsv':
            # Return TSV format with German number formatting
            tsv_data = export_to_tsv(df)
            return Response(
                tsv_data,
                mimetype='text/tab-separated-values',
                headers={'Content-Disposition': f'attachment; filename={symbol}_financials.tsv'}
            )
        else:
            # Return JSON format
            json_data = export_to_json(df)
            json_data['symbol'] = symbol.strip()
            return jsonify(json_data)
            
    except ValueError as e:
        # Handle invalid ticker or missing data
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route('/market/analysis', methods=['GET', 'POST'])
def get_analysis():
    """
    Generate an AI-powered investment analysis for a company.

    Query Parameters (GET or POST form fields):
        company (required): Company identifier — name, ticker symbol, ISIN, or similar.
        context (optional): Analyst background / expectations appended to the system prompt.

    POST multipart/form-data:
        files (optional): One or more documents (PDF, plain text) attached for Claude to read.

    Returns:
        Markdown-formatted investment analysis (text/markdown).
    """
    # Support both query params (GET) and form fields (POST)
    company = request.values.get('company')
    if not company:
        return jsonify({"error": "Parameter 'company' missing"}), 400

    context = request.values.get('context') or None

    # Collect uploaded files as (filename, bytes, media_type) tuples
    files = None
    if request.files:
        files = []
        for uploaded_file in request.files.getlist('files'):
            if uploaded_file.filename:
                media_type = uploaded_file.mimetype or 'application/octet-stream'
                files.append((uploaded_file.filename, uploaded_file.read(), media_type))
        if not files:
            files = None

    try:
        markdown = get_investment_analysis(company.strip(), context=context, files=files)
        return Response(markdown, mimetype='text/markdown; charset=utf-8')
    except EnvironmentError as e:
        return jsonify({"error": str(e)}), 503
    except anthropic.APIError as e:
        return jsonify({"error": f"Anthropic API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
