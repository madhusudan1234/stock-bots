from config.settings import (
    MAX_RISK_PER_TRADE,
    MAX_POSITION_SIZE,
    DAILY_LOSS_LIMIT,
    STOP_LOSS_PERCENT,
)
from utils.logger import setup_logger

logger = setup_logger("risk_manager")


class RiskManager:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.daily_pnl = 0.0
        self.daily_trades = 0

    def can_trade(self, capital: float) -> bool:
        if self.daily_pnl < 0 and abs(self.daily_pnl) >= self.initial_capital * DAILY_LOSS_LIMIT:
            logger.warning("Daily loss limit reached. No more trades today.")
            return False
        return True

    def calculate_position_size(self, capital: float, price: float) -> int:
        risk_amount = capital * MAX_RISK_PER_TRADE
        max_position_value = capital * MAX_POSITION_SIZE

        dollar_risk_per_share = price * STOP_LOSS_PERCENT
        shares_by_risk = int(risk_amount / dollar_risk_per_share) if dollar_risk_per_share > 0 else 0
        shares_by_position = int(max_position_value / price)

        shares = min(shares_by_risk, shares_by_position)
        shares = max(1, shares)

        logger.info(f"Position size: {shares} shares (risk: ${risk_amount:.2f}, max: ${max_position_value:.2f})")
        return shares

    def calculate_stop_loss(self, entry_price: float) -> float:
        stop_loss = entry_price * (1 - STOP_LOSS_PERCENT)
        logger.info(f"Stop loss: ${stop_loss:.2f} ({STOP_LOSS_PERCENT*100}% below entry)")
        return round(stop_loss, 2)

    def record_trade_result(self, pnl: float):
        self.daily_pnl += pnl
        self.daily_trades += 1
        logger.info(f"Trade P&L: ${pnl:.2f} | Daily P&L: ${self.daily_pnl:.2f}")

    def reset_daily(self):
        self.daily_pnl = 0.0
        self.daily_trades = 0
        logger.info("Daily risk counters reset")
