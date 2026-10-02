import math
from statistics import mean, pstdev


def sma(values, n):
    return sum(values[-n:]) / n if len(values) >= n else None


def ema(values, n):
    if len(values) < n:
        return None
    k = 2 / (n + 1)
    value = sum(values[:n]) / n
    for x in values[n:]:
        value = x * k + value * (1 - k)
    return value


def rsi(values, n=14):
    if len(values) <= n:
        return None
    gains, losses = [], []
    for a, b in zip(values[-(n+1):], values[-n:]):
        change = b - a
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = sum(gains) / n
    avg_loss = sum(losses) / n
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))


def macd(values):
    fast = ema(values, 12)
    slow = ema(values, 26)
    if fast is None or slow is None:
        return None, None
    # Signal is approximated from a rolling MACD series for transparency.
    series = []
    for i in range(26, len(values) + 1):
        f = ema(values[:i], 12)
        s = ema(values[:i], 26)
        if f is not None and s is not None:
            series.append(f - s)
    signal = ema(series, 9)
    return fast - slow, signal


def returns(values):
    return [(b / a) - 1 for a, b in zip(values[:-1], values[1:]) if a]


def annual_vol(values):
    r = returns(values)
    return pstdev(r) * math.sqrt(252) if len(r) > 2 else 0


def atr_proxy(values, n=20):
    r = returns(values)
    if len(r) < n:
        return None
    return pstdev(r[-n:]) * values[-1]


def technicals(rows):
    closes = [x['close'] for x in rows]
    volumes = [x['volume'] for x in rows]
    price = closes[-1]
    sma20, sma50, sma200 = sma(closes, 20), sma(closes, 50), sma(closes, 200)
    r = rsi(closes)
    m, ms = macd(closes)
    vol = annual_vol(closes)
    high52, low52 = max(closes[-252:]), min(closes[-252:])
    avg_volume = mean(volumes[-20:]) if volumes else 0
    return {
        'price': price, 'sma20': sma20, 'sma50': sma50, 'sma200': sma200,
        'rsi14': r, 'macd': m, 'macd_signal': ms, 'annual_volatility': vol,
        'high52': high52, 'low52': low52, 'distance_high_pct': (price / high52 - 1) * 100,
        'distance_low_pct': (price / low52 - 1) * 100, 'avg_volume20': avg_volume
    }


def analyze_asset(provider, symbol, capital, cash_reserve, risk_pct, horizon, max_position_pct):
    if capital <= 0 or cash_reserve < 0 or risk_pct <= 0 or max_position_pct <= 0:
        raise ValueError('Capital, reserva, riesgo y máximo de posición deben ser válidos.')
    market = provider.history(symbol, '5y', '1d')
    t = technicals(market['rows'])
    price = t['price']
    scores = {}
    reasons = []

    trend = 50
    if t['sma50'] and price > t['sma50']: trend += 20; reasons.append('Precio por encima de SMA50.')
    else: trend -= 15; reasons.append('Precio por debajo de SMA50.')
    if t['sma200'] and price > t['sma200']: trend += 20; reasons.append('Precio por encima de SMA200.')
    elif t['sma200']: trend -= 20; reasons.append('Precio por debajo de SMA200.')
    scores['tendencia'] = max(0, min(100, trend))

    momentum = 50
    if t['rsi14'] is not None:
        if 45 <= t['rsi14'] <= 65: momentum += 15
        elif t['rsi14'] > 75: momentum -= 20; reasons.append('RSI elevado: existe riesgo de sobreextensión.')
        elif t['rsi14'] < 30: momentum -= 10; reasons.append('RSI bajo: puede existir presión vendedora.')
    if t['macd'] is not None and t['macd_signal'] is not None:
        momentum += 15 if t['macd'] > t['macd_signal'] else -15
    scores['momentum'] = max(0, min(100, momentum))

    risk_score = max(0, min(100, 100 - t['annual_volatility'] * 100))
    scores['riesgo'] = risk_score
    if t['annual_volatility'] > 0.45:
        reasons.append('Volatilidad anualizada alta; reduce el tamaño potencial.')

    overall = round(scores['tendencia'] * .4 + scores['momentum'] * .35 + scores['riesgo'] * .25)
    stale = market['stale']
    if stale:
        action = 'ESPERAR'
        reasons.append('Los datos superan el umbral de frescura; no se genera una señal de entrada.')
    elif overall >= 68:
        action = 'ENTRADA CONDICIONADA'
    elif overall >= 45:
        action = 'ESPERAR'
    else:
        action = 'NO ENTRAR'

    atr = atr_proxy([x['close'] for x in market['rows']]) or price * 0.05
    lower = max(0, price - max(atr, price * .03))
    upper = price + price * .01
    stop = max(0, price - max(atr * 1.5, price * .05))
    risk_amount = max(0, (capital - cash_reserve) * risk_pct / 100)
    per_share_risk = max(price - stop, price * .01)
    risk_position = risk_amount / per_share_risk * price
    cap_position = max(0, (capital - cash_reserve) * max_position_pct / 100)
    suggested = min(risk_position, cap_position)
    first_entry = suggested * .5
    second_entry = suggested * .3
    third_entry = suggested * .2

    invalidators = [
        'Cambio de tendencia con pérdida sostenida de SMA200.',
        'Aumento material de volatilidad o deterioro del riesgo/recompensa.',
        'Noticias o resultados que cambien la tesis fundamental.',
        'Datos de mercado desactualizados o inconsistentes.'
    ]
    return {
        'symbol': symbol, 'action': action, 'score': overall, 'scores': scores,
        'currency': market['currency'], 'exchange': market['exchange'], 'data_source': market['source'],
        'last_update': market['last_update'], 'data_age_hours': market['age_hours'], 'stale': stale,
        'technicals': t, 'entry_zone': {'low': lower, 'high': upper}, 'stop_reference': stop,
        'position_plan': {'total': suggested, 'first': first_entry, 'second': second_entry, 'third': third_entry,
                          'risk_amount': risk_amount, 'cash_after_first': max(0, capital - cash_reserve - first_entry)},
        'scenarios': {
            'A_ahora': 'Entrada parcial solo si se acepta el riesgo y los datos siguen frescos.',
            'B_esperar': f'Esperar una zona aproximada de {lower:.2f}–{upper:.2f} o una mejora de las condiciones técnicas.',
            'C_no_entrar': 'No entrar si la tendencia se deteriora, los datos dejan de estar frescos o aparece un riesgo que invalide la tesis.'
        },
        'invalidators': invalidators, 'reasons': reasons,
        'disclaimer': 'Herramienta de apoyo y análisis; no garantiza resultados ni sustituye la comprobación de datos.'
    }


def analyze_portfolio(positions, cash, prices):
    total = cash + sum(p['quantity'] * prices.get(p['symbol'], p['avg_price']) for p in positions)
    items = []
    for p in positions:
        current = prices.get(p['symbol'], p['avg_price'])
        value = p['quantity'] * current
        pnl = (current / p['avg_price'] - 1) * 100
        items.append({'symbol': p['symbol'], 'value': value, 'weight_pct': value / total * 100 if total else 0, 'pnl_pct': pnl})
    return {'cash': cash, 'total_value': total, 'positions': items,
            'concentration': sorted(items, key=lambda x: x['weight_pct'], reverse=True),
            'note': 'La diversificación debe evaluarse también por sector, geografía, moneda y correlación; esta versión no inventa esos datos.'}


def backtest_strategy(provider, symbol, years=5):
    years = max(1, min(years, 10))
    market = provider.history(symbol, f'{years}y', '1d')
    closes = [r['close'] for r in market['rows']]
    if len(closes) < 220:
        raise ValueError('No hay suficientes datos para el backtest.')
    cash = 1.0
    shares = 0.0
    equity = []
    for i, price in enumerate(closes):
        if i >= 200:
            s20 = sum(closes[i-19:i+1]) / 20
            s200 = sum(closes[i-199:i+1]) / 200
            if shares == 0 and price > s20 > s200:
                shares = cash * .95 / price
                cash -= shares * price
            elif shares > 0 and price < s20:
                cash += shares * price
                shares = 0
        equity.append(cash + shares * price)
    final = equity[-1]
    peak = equity[0]
    max_dd = 0
    for x in equity:
        peak = max(peak, x)
        max_dd = min(max_dd, x / peak - 1)
    return {'symbol': symbol, 'years': years, 'initial': 1.0, 'final': final,
            'return_pct': (final - 1) * 100, 'max_drawdown_pct': max_dd * 100,
            'warning': 'El backtest usa datos históricos y no garantiza resultados futuros.',
            'data_source': market['source'], 'last_update': market['last_update']}
