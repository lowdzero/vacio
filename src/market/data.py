import os
import urllib.parse
import urllib.request
import json


class AlphaVantageClient:
    """Small read-only client for public market data."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ALPHAVANTAGE_API_KEY")
        if not self.api_key:
            raise RuntimeError("Set ALPHAVANTAGE_API_KEY")

    def _get(self, function: str, **params) -> dict:
        query = urllib.parse.urlencode({"function": function, "apikey": self.api_key, **params})
        with urllib.request.urlopen(f"https://www.alphavantage.co/query?{query}", timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    def quote(self, symbol: str) -> dict:
        return self._get("GLOBAL_QUOTE", symbol=symbol)

    def daily(self, symbol: str) -> dict:
        return self._get("TIME_SERIES_DAILY", symbol=symbol, outputsize="compact")

    def rsi(self, symbol: str) -> dict:
        return self._get("RSI", symbol=symbol, interval="daily", time_period=14, series_type="close")

    def macd(self, symbol: str) -> dict:
        return self._get("MACD", symbol=symbol, interval="daily", series_type="close")

    def overview(self, symbol: str) -> dict:
        return self._get("OVERVIEW", symbol=symbol)

    def etf_profile(self, symbol: str) -> dict:
        return self._get("ETF_PROFILE", symbol=symbol)

    def news(self, tickers: str) -> dict:
        return self._get("NEWS_SENTIMENT", tickers=tickers)
