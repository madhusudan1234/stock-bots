from datetime import datetime, time
from config.settings import TRADING_HOURS_START, TRADING_HOURS_END
from utils.holidays import is_indian_market_holiday


def is_market_open() -> bool:
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    if is_indian_market_holiday(now.date()):
        return False
    market_open = time(*map(int, TRADING_HOURS_START.split(":")))
    market_close = time(*map(int, TRADING_HOURS_END.split(":")))
    return market_open <= now.time() <= market_close


def format_currency(amount: float) -> str:
    return f"${amount:,.2f}"


def format_percent(value: float) -> str:
    return f"{value:.2f}%"


def calculate_position_size(capital: float, risk_percent: float, stop_loss_percent: float) -> float:
    risk_amount = capital * risk_percent
    position_size = risk_amount / stop_loss_percent
    return round(position_size, 2)
