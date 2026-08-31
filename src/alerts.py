from src.market.scanner import MarketSignal


def format_alert(signal: MarketSignal) -> str:
    reasons = "\n".join(f"• {reason}" for reason in signal.reasons)
    return (
        f"📊 ALERTA DE MERCADO — {signal.symbol}\n\n"
        f"Precio: {signal.price:.2f}\n"
        f"Cambio diario: {signal.change_pct:+.2f}%\n"
        f"Score: {signal.score}/100\n"
        f"Perspectiva técnica: {signal.outlook}\n\n"
        f"Señales:\n{reasons}\n\n"
        "⚠️ Esto es una señal automática, no una garantía de subida."
    )
