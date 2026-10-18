from datetime import date

# NSE/BSE Stock Market Holidays 2026
INDIAN_MARKET_HOLIDAYS_2026 = [
    date(2026, 1, 26),   # Republic Day
    date(2026, 3, 19),   # Holi
    date(2026, 3, 30),   # Id-Ul-Fitr
    date(2026, 4, 14),   # Dr. Ambedkar Jayanti
    date(2026, 4, 21),   # Ram Navami
    date(2026, 5, 1),    # Maharashtra Day
    date(2026, 8, 19),   # Janmashtami
    date(2026, 9, 14),   # Ganesh Chaturthi
    date(2026, 10, 2),   # Gandhi Jayanti
    date(2026, 10, 20),  # Diwali Laxmi Pujan
    date(2026, 10, 21),  # Diwali Balipratipada
    date(2026, 11, 27),  # Guru Nanak Jayanti
    date(2026, 12, 25),  # Christmas
]

INDIAN_MARKET_HOLIDAYS_2027 = [
    date(2027, 1, 26),   # Republic Day
    date(2027, 3, 8),    # Holi
    date(2027, 3, 19),   # Id-Ul-Fitr
    date(2027, 4, 14),   # Dr. Ambedkar Jayanti
    date(2027, 4, 11),   # Ram Navami
    date(2027, 5, 1),    # Maharashtra Day
    date(2027, 8, 9),    # Janmashtami
    date(2027, 10, 2),   # Gandhi Jayanti
    date(2027, 11, 8),   # Diwali Laxmi Pujan
    date(2027, 11, 9),   # Diwali Balipratipada
    date(2027, 11, 17),  # Guru Nanak Jayanti
    date(2027, 12, 25),  # Christmas
]

ALL_HOLIDAYS = INDIAN_MARKET_HOLIDAYS_2026 + INDIAN_MARKET_HOLIDAYS_2027


def is_indian_market_holiday(check_date=None):
    if check_date is None:
        check_date = date.today()
    return check_date in ALL_HOLIDAYS
