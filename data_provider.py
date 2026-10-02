import math
import time
from datetime import datetime, timezone
import requests

BASE = 'https://query1.finance.yahoo.com'

class DataUnavailable(Exception):
    pass

class DataProvider:
    def __init__(self, timeout=12, stale_hours=24):
        self.timeout = timeout
        self.stale_hours = stale_hours
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'InvestmentDecisionApp/1.0'})

    def _get(self, url, params=None):
        try:
            r = self.session.get(url, params=params, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            raise DataUnavailable(f'No se pudieron obtener datos actuales: {exc}') from exc

    def history(self, symbol, period='5y', interval='1d'):
        data = self._get(f'{BASE}/v8/finance/chart/{symbol}', {'range': period, 'interval': interval, 'events': 'div,splits'})
        result = data.get('chart', {}).get('result') or []
        if not result:
            raise DataUnavailable(f'No hay datos de mercado para {symbol}')
        meta = result[0].get('meta', {})
        timestamps = result[0].get('timestamp') or []
        quote = (result[0].get('indicators', {}).get('quote') or [{}])[0]
        closes = quote.get('close') or []
        volumes = quote.get('volume') or []
        rows = []
        for ts, close, volume in zip(timestamps, closes, volumes):
            if close is not None:
                rows.append({'ts': ts, 'close': float(close), 'volume': int(volume or 0)})
        if len(rows) < 30:
            raise DataUnavailable(f'Datos insuficientes para analizar {symbol}')
        last_ts = rows[-1]['ts']
        age_hours = max(0, time.time() - last_ts) / 3600
        return {
            'symbol': symbol,
            'currency': meta.get('currency'),
            'exchange': meta.get('exchangeName'),
            'rows': rows,
            'last_update': datetime.fromtimestamp(last_ts, tz=timezone.utc).isoformat(),
            'age_hours': round(age_hours, 2),
            'stale': age_hours > self.stale_hours,
            'source': 'Yahoo Finance chart API'
        }

    def quote(self, symbol):
        data = self._get(f'{BASE}/v7/finance/quote', {'symbols': symbol})
        results = data.get('quoteResponse', {}).get('result') or []
        if not results:
            raise DataUnavailable(f'No existe una cotización para {symbol}')
        return results[0]

    def news(self, symbol):
        data = self._get(f'{BASE}/v1/finance/search', {'q': symbol, 'newsCount': 10, 'quotesCount': 1})
        return {
            'symbol': symbol,
            'items': [
                {
                    'title': n.get('title'),
                    'publisher': n.get('publisher'),
                    'published': n.get('providerPublishTime'),
                    'url': n.get('link')
                }
                for n in data.get('news', [])
            ],
            'source': 'Yahoo Finance search'
        }

    def prices(self, symbols):
        if not symbols:
            return {}
        data = self._get(f'{BASE}/v7/finance/quote', {'symbols': ','.join(symbols)})
        return {x.get('symbol'): x.get('regularMarketPrice') for x in data.get('quoteResponse', {}).get('result', []) if x.get('regularMarketPrice') is not None}
