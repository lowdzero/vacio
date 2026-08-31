import os
import sys
import urllib.parse
import urllib.request
import json


def check_env(name: str) -> bool:
    value = os.getenv(name)
    ok = bool(value and value.strip())
    print(f"{name}: {'OK' if ok else 'MISSING'}")
    return ok


def check_telegram() -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.load(response)
        ok = bool(data.get("ok"))
        print(f"Telegram API: {'OK' if ok else 'ERROR'}")
        if ok:
            print(f"Telegram bot: @{data['result'].get('username', 'unknown')}")
        return ok
    except Exception as exc:
        print(f"Telegram API: ERROR ({type(exc).__name__})")
        return False


def main() -> int:
    print("=== TR Portfolio Bot — connection check ===")
    env_ok = all(check_env(name) for name in (
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "ALPHAVANTAGE_API_KEY",
    ))
    telegram_ok = check_telegram() if env_ok else False
    print("=== Result ===")
    if env_ok and telegram_ok:
        print("CONFIGURATION OK: Telegram credentials are valid and no secret was printed.")
        return 0
    print("CONFIGURATION INCOMPLETE: review GitHub Actions secrets.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
