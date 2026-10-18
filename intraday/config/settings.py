import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

LOG_DIR = BASE_DIR / "logs"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

TRADING_HOURS_START = "09:00"
TRADING_HOURS_END = "15:00"
SQUARE_OFF_TIME = "15:15"

SCAN_INTERVAL = 15

STOP_LOSS_PERCENT = 0.012
TAKE_PROFIT_PERCENT = 0.025
MAX_POSITIONS = 4
MAX_POSITION_SIZE = 0.50
MAX_DAILY_LOSS = 100

CAPITAL = 10000

INTRADAY_INTERVAL = "5m"
INTRADAY_PERIOD = "1d"

STRATEGIES = {
    "vwap": {},
    "breakout": {
        "lookback": 10,
    },
    "momentum": {
        "volume_multiplier": 1.5,
        "price_change_pct": 0.2,
        "lookback": 5,
    },
}

NSE_WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS",
]
