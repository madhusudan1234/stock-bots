import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

TRADING_HOURS_START = "09:15"
TRADING_HOURS_END = "15:30"

MAX_RISK_PER_TRADE = 0.02
MAX_POSITION_SIZE = 0.10
DAILY_LOSS_LIMIT = 0.05
STOP_LOSS_PERCENT = 0.07
TAKE_PROFIT_PERCENT = 0.15

DEFAULT_CAPITAL = 10000
PAPER_TRADE_CAPITAL = 10000
PAPER_SCAN_INTERVAL = 300

STRATEGIES = {
    "moving_average": {
        "short_window": 20,
        "long_window": 50,
        "trend_filter": 200,
    },
    "rsi": {
        "period": 14,
        "oversold": 30,
        "overbought": 70,
    },
    "macd": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
    },
}

NSE_WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS",
]

FUNDAMENTAL_WEIGHTS = {
    "earnings_growth": 0.25,
    "revenue_growth": 0.20,
    "pe_ratio": 0.15,
    "debt_equity": 0.15,
    "profit_margin": 0.15,
    "dividend_yield": 0.10,
}
