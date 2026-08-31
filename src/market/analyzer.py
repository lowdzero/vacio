from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class Analysis:
    symbol: str
    price: float
    change_pct: float
    sma20: float | None
    sma50: float | None
    rsi14: float | None
    score: float
    risk: str
    scenarios: tuple[str, ...]


def _sma(values: list[float], n: int) -> float | None:
    return mean(values[-n:]) if len(values) >= n else None


def analyze(symbol: str, daily_payload: dict, quote_payload: dict, rsi_payload: dict) -> Analysis:
    series = daily_payload.get("Time Series (Daily)", {})
    closes = [float(v["4. close"]) for _, v in sorted(series.items())]
    latest = float(quote_payload.get("Global Quote", {}).get("05. price", closes[-1] if closes else 0))
    change = float(quote_payload.get("Global Quote", {}).get("10. change percent", "0%").replace("%", ""))
    sma20, sma50 = _sma(closes, 20), _sma(closes, 50)
    rsi_values = rsi_payload.get("Technical Analysis: RSI", {})
    rsi = float(next(iter(rsi_values.values()))["RSI"]) if rsi_values else None

    score = 50.0
    if sma20 and latest > sma20: score += 12
    if sma50 and latest > sma50: score += 12
    if sma20 and sma50 and sma20 > sma50: score += 10
    if change > 0: score += min(8, change)
    if rsi is not None:
        if 45 <= rsi <= 65: score += 8
        elif rsi > 75 or rsi < 25: score -= 12
    score = max(0, min(100, score))

    risk = "ALTO" if score < 45 else "MEDIO" if score < 70 else "BAJO/MODERADO"
    scenarios = (
        "Alcista: continuidad de tendencia si el precio mantiene las medias.",
        "Base: consolidación lateral si pierde momentum.",
        "Bajista: deterioro si rompe soportes y medias relevantes.",
    )
    return Analysis(symbol, latest, change, sma20, sma50, rsi, round(score, 1), risk, scenarios)
