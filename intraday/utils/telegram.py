import requests
from utils.logger import setup_logger

logger = setup_logger("telegram")


class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
        if self.enabled:
            logger.info("Telegram notifications enabled")
        else:
            logger.info("Telegram notifications disabled (no token/chat_id)")

    def send(self, message):
        if not self.enabled:
            return False
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            resp = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
            }, timeout=30)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    def send_startup(self, capital, stocks):
        msg = (
            f"<b>Intraday Bot Started</b>\n"
            f"Capital: {capital}\n"
            f"Stocks: {len(stocks)}\n"
            f"Scan: Every 30 seconds"
        )
        return self.send(msg)

    def send_buy_signal(self, symbol, price, shares, stop_loss, take_profit, strategy):
        msg = (
            f"<b>BUY</b>\n"
            f"Stock: {symbol}\n"
            f"Price: {price}\n"
            f"Shares: {shares}\n"
            f"Stop Loss: {stop_loss}\n"
            f"Take Profit: {take_profit}\n"
            f"Strategy: {strategy}"
        )
        return self.send(msg)

    def send_sell_signal(self, symbol, price, shares, pnl, reason):
        emoji = "+" if pnl >= 0 else ""
        msg = (
            f"<b>SELL</b>\n"
            f"Stock: {symbol}\n"
            f"Price: {price}\n"
            f"Shares: {shares}\n"
            f"P&L: {emoji}{pnl}\n"
            f"Reason: {reason}"
        )
        return self.send(msg)

    def send_square_off(self, positions, total_pnl):
        msg = f"<b>SQUARE OFF</b>\nAll positions closed.\nTotal P&L: {total_pnl}"
        return self.send(msg)

    def send_portfolio_summary(self, cash, positions_value, total_value, total_return, trades, win_rate):
        msg = (
            f"<b>Portfolio</b>\n"
            f"Cash: {cash}\n"
            f"Positions: {positions_value}\n"
            f"Total: {total_value}\n"
            f"Return: {total_return}\n"
            f"Trades today: {trades} | Win rate: {win_rate}"
        )
        return self.send(msg)

    def send_error(self, error):
        msg = f"<b>ERROR</b>\n{error}"
        return self.send(msg)
