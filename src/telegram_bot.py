import os
import sys
import urllib.parse
import urllib.request
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from market_scan import scan_symbols, format_scan, analyze_symbol

ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_message(chat_id: str, text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=body, timeout=15):
        pass


def reply(chat_id: str, text: str) -> None:
    if chat_id == ALLOWED_CHAT_ID:
        for i in range(0, len(text), 3500):
            send_message(chat_id, text[i:i + 3500])


def help_text() -> str:
    return ("🤖 MARKET BOT\n\n"
            "/buscar TICKER — análisis completo\n"
            "/scan — escanea la lista de activos\n"
            "/top — mejores oportunidades\n"
            "/mercado — resumen del mercado\n"
            "/noticias TICKER — noticias\n"
            "/ayuda — comandos\n\n"
            "También puedes escribir: Analiza NVDA")


def handle(chat_id: str, text: str) -> None:
    if chat_id != ALLOWED_CHAT_ID:
        return
    raw = text.strip()
    parts = raw.split(maxsplit=1)
    cmd = parts[0].lower() if parts else ""
    arg = parts[1].strip().upper() if len(parts) > 1 else ""
    if not cmd.startswith("/"):
        if raw.lower().startswith(("analiza ", "analiza el ", "analizar ")):
            arg = raw.split()[-1].upper()
            cmd = "/buscar"
        else:
            reply(chat_id, "No reconozco ese mensaje. Usa /ayuda.")
            return
    try:
        if cmd in ("/start", "/ayuda", "/help"):
            reply(chat_id, help_text())
        elif cmd == "/buscar" and arg:
            reply(chat_id, analyze_symbol(arg))
        elif cmd == "/scan":
            reply(chat_id, format_scan(scan_symbols(), title="📊 MARKET SCAN"))
        elif cmd == "/top":
            reply(chat_id, format_scan(scan_symbols(), limit=5, title="🔥 TOP OPORTUNIDADES"))
        elif cmd == "/mercado":
            reply(chat_id, format_scan(scan_symbols(), limit=10, title="🌍 RESUMEN DE MERCADO"))
        elif cmd == "/noticias" and arg:
            reply(chat_id, f"📰 Noticias de {arg}: módulo de noticias pendiente de una fuente compatible.")
        else:
            reply(chat_id, "Uso: /buscar NVDA, /scan, /top, /mercado, /noticias NVDA o /ayuda")
    except Exception as exc:
        reply(chat_id, f"⚠️ No pude completar la consulta: {type(exc).__name__}. Revisa la API/datos.")


def poll() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    offset = 0
    while True:
        query = urllib.parse.urlencode({"timeout": 30, "offset": offset})
        with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getUpdates?{query}", timeout=40) as r:
            data = json.load(r)
        for update in data.get("result", []):
            offset = update["update_id"] + 1
            message = update.get("message", {})
            chat = message.get("chat", {})
            text = message.get("text", "")
            if text:
                handle(str(chat.get("id", "")), text)


if __name__ == "__main__":
    poll()
