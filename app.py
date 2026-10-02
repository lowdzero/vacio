from flask import Flask, jsonify, render_template, request
from analysis_engine import analyze_asset, analyze_portfolio, backtest_strategy
from data_provider import DataProvider, DataUnavailable
from storage import Store

app = Flask(__name__)
provider = DataProvider()
store = Store()

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/api/health')
def health():
    return jsonify({'ok': True, 'mode': 'analysis-only', 'real_orders': False})

@app.get('/api/analyze/<symbol>')
def analyze(symbol):
    try:
        capital = float(request.args.get('capital', 1000))
        cash_reserve = float(request.args.get('cash_reserve', 0))
        risk_pct = float(request.args.get('risk_pct', 1))
        horizon = request.args.get('horizon', 'medium')
        max_position_pct = float(request.args.get('max_position_pct', 20))
        result = analyze_asset(provider, symbol.upper(), capital, cash_reserve, risk_pct, horizon, max_position_pct)
        return jsonify(result)
    except (ValueError, DataUnavailable) as exc:
        return jsonify({'error': str(exc)}), 400

@app.get('/api/news/<symbol>')
def news(symbol):
    try:
        return jsonify(provider.news(symbol.upper()))
    except DataUnavailable as exc:
        return jsonify({'error': str(exc)}), 400

@app.get('/api/portfolio')
def portfolio():
    positions = store.positions()
    cash = store.cash()
    symbols = [p['symbol'] for p in positions]
    prices = provider.prices(symbols) if symbols else {}
    return jsonify(analyze_portfolio(positions, cash, prices))

@app.post('/api/portfolio')
def save_position():
    body = request.get_json(force=True)
    symbol = str(body.get('symbol', '')).upper().strip()
    quantity = float(body.get('quantity', 0))
    avg_price = float(body.get('avg_price', 0))
    if not symbol or quantity <= 0 or avg_price <= 0:
        return jsonify({'error': 'symbol, quantity y avg_price deben ser válidos'}), 400
    store.upsert_position(symbol, quantity, avg_price)
    return jsonify({'ok': True})

@app.post('/api/cash')
def save_cash():
    body = request.get_json(force=True)
    cash = float(body.get('cash', 0))
    if cash < 0:
        return jsonify({'error': 'El efectivo no puede ser negativo'}), 400
    store.set_cash(cash)
    return jsonify({'ok': True})

@app.delete('/api/portfolio/<symbol>')
def delete_position(symbol):
    store.delete_position(symbol.upper())
    return jsonify({'ok': True})

@app.get('/api/alerts')
def alerts():
    return jsonify(store.alerts())

@app.post('/api/alerts')
def create_alert():
    body = request.get_json(force=True)
    symbol = str(body.get('symbol', '')).upper().strip()
    target = float(body.get('target', 0))
    direction = body.get('direction', 'below')
    if not symbol or target <= 0 or direction not in ('above', 'below'):
        return jsonify({'error': 'Alerta no válida'}), 400
    store.add_alert(symbol, target, direction)
    return jsonify({'ok': True})

@app.get('/api/backtest/<symbol>')
def backtest(symbol):
    try:
        years = int(request.args.get('years', 5))
        return jsonify(backtest_strategy(provider, symbol.upper(), years))
    except (ValueError, DataUnavailable) as exc:
        return jsonify({'error': str(exc)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
