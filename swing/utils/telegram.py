import requests
from utils.logger import setup_logger

logger = setup_logger("telegram")


class TelegramNotifier:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
        if self.enabled:
            logger.info("Telegram notifications enabled")
        else:
            logger.info("Telegram notifications disabled (no token/chat_id)")

    def send(self, message: str) -> bool:
        if not self.enabled:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return True
            else:
                logger.warning(f"Telegram send failed: {resp.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Telegram error: {e}")
            return False

    def send_buy_signal(self, symbol: str, price: float, shares: int, stop_loss: float, take_profit: float, confidence: str, fund_score: float):
        message = (
            f"<b>PAPER TRADE - BUY</b>\n\n"
            f"<b>Stock:</b> {symbol}\n"
            f"<b>Price:</b> Rs. {price:.2f}\n"
            f"<b>Shares:</b> {shares}\n"
            f"<b>Stop Loss:</b> Rs. {stop_loss:.2f}\n"
            f"<b>Take Profit:</b> Rs. {take_profit:.2f}\n"
            f"<b>Confidence:</b> {confidence}\n"
            f"<b>Fund Score:</b> {fund_score:.0f}/100"
        )
        return self.send(message)

    def send_sell_signal(self, symbol: str, price: float, shares: int, pnl: float, reason: str):
        emoji = "+" if pnl >= 0 else ""
        message = (
            f"<b>PAPER TRADE - SELL</b>\n\n"
            f"<b>Stock:</b> {symbol}\n"
            f"<b>Price:</b> Rs. {price:.2f}\n"
            f"<b>Shares:</b> {shares}\n"
            f"<b>P&amp;L:</b> Rs. {emoji}{pnl:.2f}\n"
            f"<b>Reason:</b> {reason}"
        )
        return self.send(message)

    def send_portfolio_summary(self, cash: float, positions_value: float, total_value: float, total_return: float, trades: int, win_rate: float):
        message = (
            f"<b>PORTFOLIO UPDATE</b>\n\n"
            f"<b>Cash:</b> Rs. {cash:,.2f}\n"
            f"<b>Positions:</b> Rs. {positions_value:,.2f}\n"
            f"<b>Total:</b> Rs. {total_value:,.2f}\n"
            f"<b>Return:</b> {total_return:.2f}%\n"
            f"<b>Trades Today:</b> {trades}\n"
            f"<b>Win Rate:</b> {win_rate:.0f}%"
        )
        return self.send(message)

    def send_error(self, error: str):
        message = f"<b>ERROR</b>\n\n{error}"
        return self.send(message)

    def send_startup(self, capital: float, stocks: list):
        stock_list = ", ".join(stocks[:5])
        message = (
            f"<b>PAPER TRADING STARTED</b>\n\n"
            f"<b>Capital:</b> Rs. {capital:,.2f}\n"
            f"<b>Stocks:</b> {stock_list}\n"
            f"<b>Mode:</b> Auto-execute\n"
            f"<b>Scan:</b> Every 5 minutes"
        )
        return self.send(message)
