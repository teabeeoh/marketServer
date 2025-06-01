from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route('/market/quotes', methods=['GET'])
def get_quotes():
    symbols = request.args.get('symbols')
    if not symbols:
        return jsonify({"error": "Parameter 'symbols' fehlt"}), 400

    symbol_list = [s.strip() for s in symbols.split(',')]
    tickers = yf.Tickers(" ".join(symbol_list))
    result = {}

    for symbol in symbol_list:
        info = tickers.tickers[symbol].info
        kurs = info.get("currentPrice")
        waehrung = info.get("currency")
        result[symbol] = {
            "kurs": kurs,
            "waehrung": waehrung
        }

    return jsonify(result)
