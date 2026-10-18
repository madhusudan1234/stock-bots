from config.settings import STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT, MAX_DAILY_LOSS, CAPITAL
from utils.logger import setup_logger

logger = setup_logger("risk_manager")


class RiskManager:
    def __init__(self, capital=CAPITAL):
        self.initial_capital = capital
        self.daily_loss = 0
        self.daily_pnl = 0

    def can_trade(self):
        if abs(self.daily_loss) >= MAX_DAILY_LOSS:
            logger.warning(f"Daily loss limit reached: {self.daily_loss}")
            return False
        return True

    def calculate_position_size(self, price):
        risk_amount = self.initial_capital * 0.02
        shares = int(risk_amount / (price * STOP_LOSS_PERCENT)) if price > 0 else 0
        max_amount = self.initial_capital * 0.50
        shares_by_max = int(max_amount / price) if price > 0 else 0
        shares = min(shares, shares_by_max)
        return max(1, shares)

    def calculate_stop_loss(self, price):
        return price * (1 - STOP_LOSS_PERCENT)

    def calculate_take_profit(self, price):
        return price * (1 + TAKE_PROFIT_PERCENT)

    def record_trade(self, pnl):
        self.daily_pnl += pnl
        if pnl < 0:
            self.daily_loss += abs(pnl)

    def reset_daily(self):
        self.daily_loss = 0
        self.daily_pnl = 0
        logger.info("Daily risk counters reset")
