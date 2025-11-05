from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)

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
