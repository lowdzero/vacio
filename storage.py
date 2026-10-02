import sqlite3
from pathlib import Path

DB = Path('investment_app.db')

class Store:
    def __init__(self):
        self.db = DB
        with self._conn() as c:
            c.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS positions (symbol TEXT PRIMARY KEY, quantity REAL NOT NULL, avg_price REAL NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL, target REAL NOT NULL, direction TEXT NOT NULL)')
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('cash','0')")

    def _conn(self):
        return sqlite3.connect(self.db)

    def cash(self):
        with self._conn() as c:
            row = c.execute("SELECT value FROM settings WHERE key='cash'").fetchone()
            return float(row[0]) if row else 0

    def set_cash(self, value):
        with self._conn() as c:
            c.execute("INSERT INTO settings(key,value) VALUES('cash',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(value),))

    def positions(self):
        with self._conn() as c:
            return [{'symbol': r[0], 'quantity': r[1], 'avg_price': r[2]} for r in c.execute('SELECT symbol,quantity,avg_price FROM positions')]

    def upsert_position(self, symbol, quantity, avg_price):
        with self._conn() as c:
            c.execute('INSERT INTO positions(symbol,quantity,avg_price) VALUES(?,?,?) ON CONFLICT(symbol) DO UPDATE SET quantity=excluded.quantity, avg_price=excluded.avg_price', (symbol, quantity, avg_price))

    def delete_position(self, symbol):
        with self._conn() as c:
            c.execute('DELETE FROM positions WHERE symbol=?', (symbol,))

    def add_alert(self, symbol, target, direction):
        with self._conn() as c:
            c.execute('INSERT INTO alerts(symbol,target,direction) VALUES(?,?,?)', (symbol, target, direction))

    def alerts(self):
        with self._conn() as c:
            return [{'id': r[0], 'symbol': r[1], 'target': r[2], 'direction': r[3]} for r in c.execute('SELECT id,symbol,target,direction FROM alerts ORDER BY id DESC')]
