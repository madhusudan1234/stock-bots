import sqlite3
import pandas as pd
from pathlib import Path
from config.settings import DATA_DIR
from utils.logger import setup_logger

logger = setup_logger("data_store")


class DataStore:
    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self.db_path = DATA_DIR / "market_data.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historical_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    UNIQUE(symbol, date)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    strategy TEXT,
                    pnl REAL
                )
            """)
        logger.info("Database initialized")

    def save_historical_data(self, symbol: str, df: pd.DataFrame):
        with sqlite3.connect(self.db_path) as conn:
            for date, row in df.iterrows():
                date_str = date.strftime("%Y-%m-%d")
                conn.execute("""
                    INSERT OR REPLACE INTO historical_data 
                    (symbol, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (symbol, date_str, row["open"], row["high"], row["low"], row["close"], int(row["volume"])))
        logger.info(f"Saved {len(df)} rows for {symbol}")

    def get_historical_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        query = "SELECT date, open, high, low, close, volume FROM historical_data WHERE symbol = ?"
        params = [symbol]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date"

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)

        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

        return df

    def save_trade(self, symbol: str, side: str, quantity: int, price: float, strategy: str = None, pnl: float = None):
        from datetime import datetime
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO trades (symbol, side, quantity, price, timestamp, strategy, pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, side, quantity, price, datetime.now().isoformat(), strategy, pnl))
        logger.info(f"Trade recorded: {side} {quantity} {symbol} @ ${price:.2f}")

    def get_trades(self, symbol: str = None) -> pd.DataFrame:
        query = "SELECT * FROM trades"
        params = []

        if symbol:
            query += " WHERE symbol = ?"
            params.append(symbol)

        query += " ORDER BY timestamp DESC"

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)
