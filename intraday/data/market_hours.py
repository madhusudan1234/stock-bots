from datetime import datetime, time
from config.settings import TRADING_HOURS_START, TRADING_HOURS_END, SQUARE_OFF_TIME
from config.holidays import is_indian_market_holiday
from utils.logger import setup_logger

logger = setup_logger("market_hours")


def is_market_open():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    if is_indian_market_holiday(now.date()):
        return False
    market_open = time(*map(int, TRADING_HOURS_START.split(":")))
    market_close = time(*map(int, TRADING_HOURS_END.split(":")))
    return market_open <= now.time() <= market_close


def is_square_off_time():
    now = datetime.now()
    so_time = time(*map(int, SQUARE_OFF_TIME.split(":")))
    return now.time() >= so_time


def time_to_close():
    now = datetime.now()
    market_close = time(*map(int, TRADING_HOURS_END.split(":")))
    close_dt = datetime.combine(now.date(), market_close)
    diff = (close_dt - now).total_seconds()
    return max(0, diff)


def is_trading_day():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    if is_indian_market_holiday(now.date()):
        return False
    return True


def get_session_info():
    now = datetime.now()
    market_open = time(*map(int, TRADING_HOURS_START.split(":")))
    market_close = time(*map(int, TRADING_HOURS_END.split(":")))
    square_off = time(*map(int, SQUARE_OFF_TIME.split(":")))

    if now.weekday() >= 5:
        return {"status": "WEEKEND", "message": "Market closed (weekend)"}

    if is_indian_market_holiday(now.date()):
        return {"status": "HOLIDAY", "message": "Market closed (Indian market holiday)"}

    if now.time() < market_open:
        return {"status": "PRE_MARKET", "message": f"Market opens at {TRADING_HOURS_START}"}

    if now.time() > market_close:
        return {"status": "POST_MARKET", "message": "Market closed for the day"}

    if now.time() >= square_off:
        return {"status": "SQUARE_OFF", "message": "Square off time - closing all positions"}

    return {"status": "OPEN", "message": "Market is open for trading"}
