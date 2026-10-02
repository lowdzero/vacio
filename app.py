from __future__ import annotations

import math
from datetime import datetime, timezone
from statistics import mean, stdev
from typing import Any

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


def yahoo_chart(symbol: str, range_: str = "1y", interval: str = "1d") -> dict[str, Any]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}"
    r = requests.get(url, params={"range": range_, "interval": interval, "events": "div,splits"}, timeout=10)
    r.raise_for_status()
    data = r.json()["chart"]["result"][0]
    quote = data["indicators"]["quote"][0]
    closes = [float(x) for x in quote["close"] if x is not None]
    volumes = [float(x) for x in quote["volume"] if x is not None]
    timestamps = data.get("timestamp", [])
    return {"closes": closes, "volumes": volumes, "timestamps": timestamps, "currency": data.get("meta", {}).get("currency")}


def ema(values: list[float], period: int) -> list[float]:
    if len(values) < period:
        return []
    k = 2 / (period + 1)
    out = [mean(values[:period])]
    for x in values[period:]:
        out.append(x * k + out[-1] * (1 - k))
    return out


def rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    gains, losses = [], []
    for a, b in zip(values[-period - 1:-1], values[-period:]):
        d = b - a
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_gain, avg_loss = mean(gains), mean(losses)
    if avg_loss == 0:
        return 100.0
    return 100 - 100 / (1 + avg_gain / avg_loss)


def indicators(closes: list[float], volumes: list[float]) -> dict[str, float | None]:
    current = closes[-1]
    sma20 = mean(closes[-20:]) if len(closes) >= 20 else None
    sma50 = mean(closes[-50:]) if len(closes) >= 50 else None
    sma200 = mean(closes[-200:]) if len(closes) >= 200 else None
    e12, e26 = ema(closes, 12), ema(closes, 26)
    macd = None
    if e12 and e26:
        macd = e12[-1] - e26[-1]
    signal = None
    if len(closes) >= 35:
        macd_series = []
        for i in range(26, len(closes) + 1):
            a = ema(closes[:i], 12)[-1]
            b = ema(closes[:i], 26)[-1]
            macd_series.append(a - b)
        signal_values = ema(macd_series, 9)
        signal = signal_values[-1] if signal_values else None
    returns = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    vol = stdev(returns[-30:]) * math.sqrt(252) if len(returns) >= 30 else None
    return {
        "price": current,
        "sma20": sma20,
        "sma50": sma50,
        "sma200": sma200,
        "rsi14": rsi(closes),
        "macd": macd,
        "macd_signal": signal,
        "volatility_annualized": vol,
        "high_52w": max(closes),
        "low_52w": min(closes),
        "avg_volume_20": mean(volumes[-20:]) if len(volumes) >= 20 else None,
    }


def analysis(symbol: str, capital: float = 1000, risk_pct: float = 1, horizon: str = "medium") -> dict[str, Any]:
    raw = yahoo_chart(symbol)
    closes, volumes = raw["closes"], raw["volumes"]
    if len(closes) < 30:
        raise ValueError("No hay suficientes datos históricos para analizar este activo.")
    ind = indicators(closes, volumes)
    price = ind["price"]
    score = 50.0
    factors = {}

    trend = 50
    if ind["sma50"]:
        trend += 25 if price > ind["sma50"] else -25
    if ind["sma200"]:
        trend += 25 if price > ind["sma200"] else -25
    factors["tendencia"] = max(0, min(100, trend))

    mom = 50
    if ind["rsi14"] is not None:
        mom += 25 if 50 <= ind["rsi14"] <= 70 else (-20 if ind["rsi14"] > 75 or ind["rsi14"] < 30 else 0)
    if ind["macd"] is not None and ind["macd_signal"] is not None:
        mom += 25 if ind["macd"] > ind["macd_signal"] else -25
    factors["momentum"] = max(0, min(100, mom))

    vol_score = 75 if ind["volatility_annualized"] is None else max(0, min(100, 100 - ind["volatility_annualized"] * 100))
    factors["riesgo"] = vol_score

    score = round(0.45 * factors["tendencia"] + 0.35 * factors["momentum"] + 0.20 * factors["riesgo"], 1)
    if score >= 65:
        action = "ENTRADA CONDICIONADA"
    elif score >= 45:
        action = "ESPERAR"
    else:
        action = "NO ENTRAR"

    risk_amount = capital * risk_pct / 100
    stop_distance = max(price * 0.05, price * (ind["volatility_annualized"] or 0.25) * 0.25)
    units = risk_amount / stop_distance if stop_distance else 0
    suggested = min(capital * 0.20, units * price)
    entry_low = min(price, ind["sma20"] or price) * 0.97
    entry_high = max(price, ind["sma20"] or price) * 1.01

    reasons = [
        f"Precio actual: {price:.2f} {raw.get('currency') or ''}".strip(),
        f"RSI(14): {ind['rsi14']:.1f}" if ind["rsi14"] is not None else "RSI no disponible",
        f"Volatilidad anualizada estimada: {ind['volatility_annualized']*100:.1f}%" if ind["volatility_annualized"] is not None else "Volatilidad no disponible",
        "La señal combina tendencia, momentum y volatilidad; no incluye valoración fundamental ni noticias en este MVP.",
    ]
    return {
        "symbol": symbol.upper(), "action": action, "score": score, "factors": factors,
        "indicators": ind, "entry_zone": [round(entry_low, 2), round(entry_high, 2)],
        "suggested_amount": round(suggested, 2), "risk_amount": round(risk_amount, 2),
        "reasons": reasons,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "Yahoo Finance chart endpoint; market data availability may vary.",
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/analyze/<symbol>")
def analyze(symbol: str):
    try:
        capital = float(request.args.get("capital", 1000))
        risk = float(request.args.get("risk", 1))
        return jsonify(analysis(symbol, capital, risk))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "mode": "analysis-only", "real_orders": False})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
