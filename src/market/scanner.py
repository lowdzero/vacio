from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class MarketSignal:
    symbol: str
    price: float
    change_pct: float
    score: int
    outlook: str
    reasons: tuple[str, ...]


def analyze(symbol: str, prices: list[float]) -> MarketSignal | None:
    if len(prices) < 20 or prices[-1] <= 0:
        return None

    current = prices[-1]
    change_pct = (current / prices[-2] - 1) * 100
    short = mean(prices[-5:])
    long = mean(prices[-20:])

    score = 50
    reasons: list[str] = []
    if short > long:
        score += 15
        reasons.append("media de 5 sesiones por encima de la de 20")
    else:
        score -= 15
        reasons.append("media de 5 sesiones por debajo de la de 20")
    if change_pct > 1:
        score += 10
        reasons.append("impulso diario positivo")
    elif change_pct < -1:
        score -= 10
        reasons.append("caída diaria relevante")

    score = max(0, min(100, score))
    outlook = "favorable" if score >= 65 else "neutral" if score >= 45 else "débil"
    return MarketSignal(symbol, current, change_pct, score, outlook, tuple(reasons))
