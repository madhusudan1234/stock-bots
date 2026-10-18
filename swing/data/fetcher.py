import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config.credentials import ALPACA_API_KEY, ALPACA_SECRET_KEY
from config.settings import ALPACA_BASE_URL
from utils.logger import setup_logger

logger = setup_logger("data_fetcher")


class DataFetcher:
    def __init__(self):
        self.api = None
        self._setup_alpaca()

    def _setup_alpaca(self):
        try:
            from alpaca.trading.client import TradingClient
            self.api = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
            logger.info("Alpaca API connected")
        except Exception as e:
            logger.warning(f"Alpaca connection failed: {e}. Using yfinance only.")
            self.api = None

    def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        logger.info(f"Fetching historical data: {symbol} ({period}, {interval})")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            df = df[["Open", "High", "Low", "Close", "Volume"]]
            df.columns = ["open", "high", "low", "close", "volume"]
            logger.info(f"Got {len(df)} rows for {symbol}")
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def get_realtime_quote(self, symbol: str) -> dict:
        if self.api:
            try:
                from alpaca.data.requests import StockLatestQuoteRequest
                request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                quote = self.api.get_stock_latest_quote(request)
                return {
                    "symbol": symbol,
                    "bid": float(quote.bid_price),
                    "ask": float(quote.ask_price),
                    "bid_size": quote.bid_size,
                    "ask_size": quote.ask_size,
                    "timestamp": quote.timestamp,
                }
            except Exception as e:
                logger.warning(f"Alpaca quote failed: {e}. Falling back to yfinance.")

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            return {
                "symbol": symbol,
                "price": float(info.last_price),
                "bid": float(info.bid),
                "ask": float(info.ask),
                "timestamp": datetime.now(),
            }
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return {}

    def get_batch_quotes(self, symbols: list) -> dict:
        quotes = {}
        for symbol in symbols:
            quotes[symbol] = self.get_realtime_quote(symbol)
        return quotes
