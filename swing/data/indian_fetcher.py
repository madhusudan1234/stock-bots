import requests
import pandas as pd
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger("indian_fetcher")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


class YahooSession:
    """Manages Yahoo Finance session with crumb authentication."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.crumb = None
        self._init_crumb()

    def _init_crumb(self):
        try:
            self.session.get("https://fc.yahoo.com", timeout=10)
            r = self.session.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=10)
            if r.status_code == 200:
                self.crumb = r.text
                logger.info("Yahoo crumb obtained")
            else:
                logger.warning("Could not get Yahoo crumb, fundamentals may fail")
        except Exception as e:
            logger.warning(f"Crumb init failed: {e}")

    def get(self, url: str, **kwargs) -> requests.Response:
        if self.crumb and "crumb=" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}crumb={self.crumb}"
        return self.session.get(url, **kwargs)


class IndianDataFetcher:
    def __init__(self):
        logger.info("Indian Market Data Fetcher initialized")
        self.yahoo = YahooSession()

    def get_historical_data(self, symbol: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        logger.info(f"Fetching historical data: {symbol} ({period}, {interval})")
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={period}&interval={interval}"
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            result = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            quotes = result["indicators"]["quote"][0]

            df = pd.DataFrame({
                "open": quotes["open"],
                "high": quotes["high"],
                "low": quotes["low"],
                "close": quotes["close"],
                "volume": quotes["volume"],
            }, index=pd.to_datetime(timestamps, unit="s"))

            df.dropna(inplace=True)

            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()

            logger.info(f"Got {len(df)} rows for {symbol}")
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def get_realtime_price(self, symbol: str) -> dict:
        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            meta = data["chart"]["result"][0]["meta"]

            return {
                "symbol": symbol,
                "price": float(meta.get("regularMarketPrice", 0)),
                "bid": 0,
                "ask": 0,
                "timestamp": datetime.now(),
            }
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return {}

    def get_fundamentals(self, symbol: str) -> dict:
        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"

        try:
            url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=summaryDetail,defaultKeyStatistics,financialData"
            resp = self.yahoo.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            info = {}
            modules = data["quoteSummary"]["result"][0]
            for mod_name in ["summaryDetail", "defaultKeyStatistics", "financialData"]:
                if mod_name in modules:
                    info.update(modules[mod_name])

            def _get(key):
                val = info.get(key, {})
                if isinstance(val, dict):
                    return val.get("raw", 0) or 0
                return val or 0

            fundamentals = {
                "symbol": symbol,
                "pe_ratio": _get("trailingPE"),
                "forward_pe": _get("forwardPE"),
                "peg_ratio": _get("pegRatio"),
                "price_to_book": _get("priceToBook"),
                "debt_to_equity": _get("debtToEquity"),
                "return_on_equity": _get("returnOnEquity"),
                "profit_margins": _get("profitMargins"),
                "revenue_growth": _get("revenueGrowth"),
                "earnings_growth": _get("earningsGrowth"),
                "dividend_yield": _get("dividendYield"),
                "market_cap": _get("marketCap"),
                "current_price": _get("currentPrice") or _get("regularMarketPrice"),
                "target_price": _get("targetMeanPrice"),
                "analyst_recommendation": info.get("recommendationKey", "none") if isinstance(info.get("recommendationKey"), str) else "none",
            }
            logger.info(f"Got fundamentals for {symbol}")
            return fundamentals
        except Exception as e:
            logger.error(f"Error getting fundamentals for {symbol}: {e}")
            return {}

    def get_batch_data(self, symbols: list, period: str = "2y") -> dict:
        data = {}
        for symbol in symbols:
            df = self.get_historical_data(symbol, period)
            if not df.empty:
                data[symbol] = df
        return data
