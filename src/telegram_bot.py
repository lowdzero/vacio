import os
import urllib.parse
import urllib.request
import json

ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_message(chat_id: str, text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=body, timeout=15):
        pass


def reply(chat_id: str, text: str) -> None:
    if chat_id == ALLOWED_CHAT_ID:
        send_message(chat_id, text)


def handle(chat_id: str, text: str) -> None:
    if chat_id != ALLOWED_CHAT_ID:
        return
    command = text.strip().split(maxsplit=1)
    cmd = command[0].lower() if command else ""
    arg = command[1].strip() if len(command) > 1 else ""
    if cmd in ("/start", "/ayuda", "/help"):
        reply(chat_id, "🤖 Market Bot\n\n/buscar TICKER — analiza un activo\n/scan — escanea oportunidades\n/top — mejores señales\n/mercado — resumen\n/noticias TICKER — noticias\n/ayuda — comandos")
    elif cmd == "/buscar" and arg:
        reply(chat_id, f"🔎 Solicitud recibida: {arg.upper()}\nEl módulo de análisis ampliado procesará precio, tendencia, momentum, riesgo, volumen y escenarios.")
    elif cmd in ("/scan", "/top", "/mercado"):
        reply(chat_id, f"📊 {cmd[1:].upper()} solicitado. El scanner ampliado se ejecutará en la siguiente fase.")
    elif cmd == "/noticias" and arg:
        reply(chat_id, f"📰 Noticias solicitadas para {arg.upper()}.")
    else:
        reply(chat_id, "No reconozco ese comando. Usa /ayuda.")


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
