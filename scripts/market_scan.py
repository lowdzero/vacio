import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SYMBOLS = ["SPY", "QQQ", "VTI", "VOO", "IWM", "DIA", "XLK", "XLF", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "JPM", "BRK-B", "COST", "UNH"]


def get_daily(symbol: str) -> dict:
    key = os.environ["ALPHAVANTAGE_API_KEY"]
    params = urllib.parse.urlencode({"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "compact", "apikey": key})
    with urllib.request.urlopen(f"https://www.alphavantage.co/query?{params}", timeout=20) as r:
        data = json.load(r)
    series = data.get("Time Series (Daily)", {})
    rows = list(series.items())
    if len(rows) < 50:
        raise ValueError("insufficient data")
    prices = [float(row[1]["4. close"]) for row in rows]
    volumes = [float(row[1]["5. volume"]) for row in rows]
    current, previous = prices[0], prices[1]
    sma20 = sum(prices[:20]) / 20
    sma50 = sum(prices[:50]) / 50
    change1 = (current / previous - 1) * 100
    change5 = (current / prices[5] - 1) * 100
    change20 = (current / prices[20] - 1) * 100
    gains, losses = [], []
    for i in range(14):
        delta = prices[i] - prices[i + 1]
        gains.append(max(delta, 0)); losses.append(max(-delta, 0))
    avg_gain = sum(gains) / 14
    avg_loss = sum(losses) / 14
    rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))
    avg_vol = sum(volumes[1:21]) / 20
    rel_vol = volumes[0] / avg_vol if avg_vol else 0
    trend = 100 if current > sma20 > sma50 else 75 if current > sma20 else 40
    momentum = max(0, min(100, 50 + change5 * 5 + (rsi - 50) * 0.5))
    risk = max(10, min(90, 70 - abs(rsi - 50) * 0.6 + (20 if current < sma50 else 0)))
    score = round(0.35 * trend + 0.35 * momentum + 0.20 * (100 - risk) + 0.10 * min(100, rel_vol * 50), 1)
    return {"symbol": symbol, "price": current, "change1": change1, "change5": change5, "change20": change20, "sma20": sma20, "sma50": sma50, "rsi": rsi, "rel_vol": rel_vol, "score": score, "risk": risk}


def analyze_symbol(symbol: str) -> str:
    x = get_daily(symbol)
    label = "🔥 OPORTUNIDAD" if x["score"] >= 75 else "👀 VIGILAR" if x["score"] >= 60 else "⚠️ PRECAUCIÓN"
    trend = "alcista" if x["price"] > x["sma20"] > x["sma50"] else "mixta" if x["price"] > x["sma20"] else "bajista"
    return (f"📊 {x['symbol']} — ANÁLISIS\n\n💰 Precio: {x['price']:.2f}\n📈 1D: {x['change1']:+.2f}% | 5D: {x['change5']:+.2f}% | 20D: {x['change20']:+.2f}%\n\n📐 SMA20: {x['sma20']:.2f}\n📐 SMA50: {x['sma50']:.2f}\n📉 RSI14: {x['rsi']:.1f}\n📦 Volumen relativo: {x['rel_vol']:.2f}x\n📈 Tendencia: {trend}\n\n🧠 Score: {x['score']}/100\n🛡️ Riesgo: {x['risk']:.1f}/100\n\n{label}\n\n⚠️ Señal estadística, no garantía de subida ni recomendación personalizada.")


def scan_symbols() -> list[dict]:
    results = []
    for symbol in SYMBOLS:
        try: results.append(get_daily(symbol))
        except Exception as exc: print(f"{symbol}: skipped ({type(exc).__name__})")
    return sorted(results, key=lambda x: x["score"], reverse=True)


def format_scan(results: list[dict], limit: int = 5, title: str = "📊 MARKET SCAN") -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [title, f"Actualizado: {now}", ""]
    for x in results[:limit]:
        label = "🔥" if x["score"] >= 75 else "👀" if x["score"] >= 60 else "⚠️"
        lines.append(f"{label} {x['symbol']} | {x['price']:.2f} | 1D {x['change1']:+.2f}% | RSI {x['rsi']:.0f} | score {x['score']}/100 | riesgo {x['risk']:.0f}/100")
    lines += ["", "📌 Tú decides cualquier compra/venta.", "⚠️ Análisis automático; no garantiza rentabilidad."]
    return "\n".join(lines)


def send(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]; chat_id = os.environ["TELEGRAM_CHAT_ID"]
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=body, timeout=15) as r:
        if r.status != 200: raise RuntimeError("Telegram notification failed")


def main() -> None:
    results = scan_symbols()
    send(format_scan(results, limit=10))
    print("Alert sent to Telegram")


if __name__ == "__main__": main()
