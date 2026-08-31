import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SYMBOLS = ["SPY", "QQQ", "VTI", "VOO", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META"]


def get_daily(symbol: str) -> dict:
    key = os.environ["ALPHAVANTAGE_API_KEY"]
    params = urllib.parse.urlencode({
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": key,
    })
    with urllib.request.urlopen(f"https://www.alphavantage.co/query?{params}", timeout=20) as r:
        data = json.load(r)
    series = data.get("Time Series (Daily)", {})
    rows = list(series.items())
    if len(rows) < 20:
        raise ValueError(f"insufficient data for {symbol}")
    prices = [float(row[1]["4. close"]) for row in rows]
    current = prices[0]
    previous = prices[1]
    sma20 = sum(prices[:20]) / 20
    change = (current / previous - 1) * 100
    trend = 100 if current >= sma20 else 35
    momentum = max(0, min(100, 50 + change * 8))
    risk = 35 if current >= sma20 else 65
    score = round(0.40 * trend + 0.35 * momentum + 0.25 * (100 - risk), 1)
    return {"symbol": symbol, "price": current, "change": change, "sma20": sma20, "score": score, "risk": risk}


def send(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=body, timeout=15) as r:
        if r.status != 200:
            raise RuntimeError("Telegram notification failed")


def main() -> None:
    results = []
    for symbol in SYMBOLS:
        try:
            results.append(get_daily(symbol))
        except Exception as exc:
            print(f"{symbol}: skipped ({type(exc).__name__})")

    results.sort(key=lambda x: x["score"], reverse=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["📊 MARKET SCAN — V1", f"Actualizado: {now}", "", "Oportunidades detectadas:"]
    for x in results[:5]:
        lines.append(f"{x['symbol']} | {x['price']:.2f} | {x['change']:+.2f}% | score {x['score']}/100 | riesgo {x['risk']}/100")
    lines += ["", "⚠️ Análisis automático, no recomendación ni garantía de rentabilidad."]
    send("\n".join(lines))
    print("Alert sent to Telegram")


if __name__ == "__main__":
    main()
