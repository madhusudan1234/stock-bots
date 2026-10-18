import requests
import pandas as pd
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger("live_fetcher")


class YahooSession:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "Mozilla/5.0"
        self.crumb = None
        self._init_crumb()

    def _init_crumb(self):
        try:
            self.session.get("https://fc.yahoo.com")
            resp = self.session.get(
                "https://query2.finance.yahoo.com/v1/test/getcrumb"
            )
            self.crumb = resp.text
            logger.info("Yahoo crumb obtained")
        except Exception as e:
            logger.error(f"Crumb init failed: {e}")

    def get(self, url, **kwargs):
        if self.crumb:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}crumb={self.crumb}"
        return self.session.get(url, **kwargs)


class LiveFetcher:
    def __init__(self):
        self.yahoo = YahooSession()

    def get_5min_candles(self, symbol, lookback_days=1):
        try:
            url = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                f"?range=5d&interval=5m&includePrePost=false"
            )
            resp = self.yahoo.get(url)
            data = resp.json()

            result = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            ohlcv = result["indicators"]["quote"][0]

            df = pd.DataFrame({
                "timestamp": [datetime.fromtimestamp(t) for t in timestamps],
                "open": ohlcv["open"],
                "high": ohlcv["high"],
                "low": ohlcv["low"],
                "close": ohlcv["close"],
                "volume": ohlcv["volume"],
            })
            df = df.dropna()
            logger.debug(f"Got {len(df)} 5-min candles for {symbol}")
            return df
        except Exception as e:
            logger.error(f"Failed to get 5min candles for {symbol}: {e}")
            return pd.DataFrame()

    def get_realtime_price(self, symbol):
        try:
            url = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                f"?interval=1m&range=1d"
            )
            resp = self.yahoo.get(url)
            data = resp.json()
            result = data["chart"]["result"][0]
            meta = result["meta"]
            return meta.get("regularMarketPrice", 0)
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return 0

    def get_batch_5min(self, symbols, lookback_days=1):
        result = {}
        for symbol in symbols:
            df = self.get_5min_candles(symbol, lookback_days)
            if not df.empty:
                result[symbol] = df
        return result
