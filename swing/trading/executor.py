from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from config.credentials import ALPACA_API_KEY, ALPACA_SECRET_KEY
from utils.logger import setup_logger

logger = setup_logger("executor")


class OrderExecutor:
    def __init__(self, paper: bool = True):
        self.api = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=paper)
        self.paper = paper
        logger.info(f"Order executor initialized (paper={paper})")

    def submit_order(self, symbol: str, side: str, qty: int, order_type: str = "market") -> dict:
        try:
            order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
            request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY,
            )
            order = self.api.submit_order(request)
            logger.info(f"Order submitted: {side} {qty} {symbol} (ID: {order.id})")
            return {
                "id": str(order.id),
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "status": order.status.value,
            }
        except Exception as e:
            logger.error(f"Order failed: {e}")
            return {"error": str(e)}

    def get_positions(self) -> list:
        try:
            positions = self.api.get_all_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": int(p.qty),
                    "avg_entry": float(p.avg_entry_price),
                    "current_price": float(p.current_price),
                    "unrealized_pl": float(p.unrealized_pl),
                }
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_account(self) -> dict:
        try:
            account = self.api.get_account()
            return {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value),
            }
        except Exception as e:
            logger.error(f"Error getting account: {e}")
            return {}
