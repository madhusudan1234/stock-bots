import json
from dataclasses import dataclass, field
from typing import Dict
from pathlib import Path
from utils.logger import setup_logger
from config.settings import BASE_DIR

logger = setup_logger("portfolio")

PORTFOLIO_FILE = BASE_DIR / "paper_portfolio.json"


@dataclass
class Position:
    symbol: str
    quantity: int
    avg_entry_price: float
    current_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.avg_entry_price) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.avg_entry_price == 0:
            return 0.0
        return ((self.current_price - self.avg_entry_price) / self.avg_entry_price) * 100


class Portfolio:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history = []
        self.daily_trades = 0
        self.daily_wins = 0
        self.cooldown: Dict[str, str] = {}

    def is_on_cooldown(self, symbol: str) -> bool:
        from datetime import date
        if symbol not in self.cooldown:
            return False
        last_exit = date.fromisoformat(self.cooldown[symbol])
        days_since = (date.today() - last_exit).days
        return days_since < 5

    def buy(self, symbol: str, quantity: int, price: float, strategy: str = None, stop_loss: float = 0, take_profit: float = 0) -> bool:
        if self.is_on_cooldown(symbol):
            logger.info(f"{symbol} is on cooldown (5-day exclusion after stop loss)")
            return False
        cost = quantity * price
        if cost > self.cash:
            logger.warning(f"Insufficient cash: need ₹{cost:.2f}, have ₹{self.cash:.2f}")
            return False

        if symbol in self.positions:
            pos = self.positions[symbol]
            total_qty = pos.quantity + quantity
            pos.avg_entry_price = (pos.avg_entry_price * pos.quantity + price * quantity) / total_qty
            pos.quantity = total_qty
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_entry_price=price,
                current_price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
            )

        self.cash -= cost
        self.trade_history.append({
            "action": "BUY",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "strategy": strategy,
        })
        self.daily_trades += 1
        logger.info(f"BUY {quantity} {symbol} @ ₹{price:.2f} | Cash: ₹{self.cash:.2f}")
        self.save()
        return True

    def sell(self, symbol: str, quantity: int, price: float, strategy: str = None) -> float:
        if symbol not in self.positions:
            logger.warning(f"No position in {symbol}")
            return 0.0

        pos = self.positions[symbol]
        if quantity > pos.quantity:
            quantity = pos.quantity

        pnl = (price - pos.avg_entry_price) * quantity
        self.cash += quantity * price

        if quantity == pos.quantity:
            del self.positions[symbol]
        else:
            pos.quantity -= quantity

        if strategy == "STOP_LOSS":
            from datetime import date
            self.cooldown[symbol] = date.today().isoformat()

        self.trade_history.append({
            "action": "SELL",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "pnl": round(pnl, 2),
            "strategy": strategy,
        })
        self.daily_trades += 1
        if pnl > 0:
            self.daily_wins += 1
        logger.info(f"SELL {quantity} {symbol} @ ₹{price:.2f} | P&L: ₹{pnl:.2f}")
        self.save()
        return pnl

    def check_stop_loss_take_profit(self, prices: dict) -> list:
        triggered = []
        for symbol, pos in list(self.positions.items()):
            if symbol in prices:
                pos.current_price = prices[symbol]
                if pos.stop_loss > 0 and pos.current_price <= pos.stop_loss:
                    logger.info(f"STOP LOSS triggered for {symbol} @ ₹{pos.current_price:.2f}")
                    self.sell(symbol, pos.quantity, pos.current_price, strategy="STOP_LOSS")
                    triggered.append({"symbol": symbol, "action": "STOP_LOSS", "price": pos.current_price})
                elif pos.take_profit > 0 and pos.current_price >= pos.take_profit:
                    logger.info(f"TAKE PROFIT triggered for {symbol} @ ₹{pos.current_price:.2f}")
                    self.sell(symbol, pos.quantity, pos.current_price, strategy="TAKE_PROFIT")
                    triggered.append({"symbol": symbol, "action": "TAKE_PROFIT", "price": pos.current_price})
        return triggered

    def update_prices(self, prices: dict):
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price

    def get_total_value(self) -> float:
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value

    def get_summary(self) -> dict:
        total_value = self.get_total_value()
        win_rate = (self.daily_wins / self.daily_trades * 100) if self.daily_trades > 0 else 0
        return {
            "cash": round(self.cash, 2),
            "positions_value": round(total_value - self.cash, 2),
            "total_value": round(total_value, 2),
            "total_return_pct": round((total_value - self.initial_capital) / self.initial_capital * 100, 2),
            "daily_trades": self.daily_trades,
            "daily_win_rate": round(win_rate, 1),
            "positions": {
                symbol: {
                    "qty": pos.quantity,
                    "avg_entry": pos.avg_entry_price,
                    "current": pos.current_price,
                    "pnl": round(pos.unrealized_pnl, 2),
                    "pnl_pct": round(pos.unrealized_pnl_pct, 2),
                }
                for symbol, pos in self.positions.items()
            },
        }

    def print_summary(self):
        summary = self.get_summary()
        logger.info("=" * 55)
        logger.info("PORTFOLIO SUMMARY")
        logger.info("=" * 55)
        logger.info(f"Cash:             ₹{summary['cash']:,.2f}")
        logger.info(f"Positions Value:  ₹{summary['positions_value']:,.2f}")
        logger.info(f"Total Value:      ₹{summary['total_value']:,.2f}")
        logger.info(f"Total Return:     {summary['total_return_pct']:.2f}%")
        logger.info(f"Today's Trades:   {summary['daily_trades']} | Win Rate: {summary['daily_win_rate']}%")

        if summary["positions"]:
            logger.info("-" * 55)
            logger.info("POSITIONS:")
            for symbol, data in summary["positions"].items():
                logger.info(f"  {symbol}: {data['qty']} shares | Entry: ₹{data['avg_entry']:.2f} | Current: ₹{data['current']:.2f} | P&L: ₹{data['pnl']:.2f} ({data['pnl_pct']:.1f}%)")
        logger.info("=" * 55)

    def save(self):
        data = {
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "daily_trades": self.daily_trades,
            "daily_wins": self.daily_wins,
            "cooldown": self.cooldown,
            "positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "avg_entry_price": pos.avg_entry_price,
                    "current_price": pos.current_price,
                    "stop_loss": pos.stop_loss,
                    "take_profit": pos.take_profit,
                }
                for symbol, pos in self.positions.items()
            },
            "trade_history": self.trade_history[-100:],
        }
        PORTFOLIO_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls) -> "Portfolio":
        if not PORTFOLIO_FILE.exists():
            return cls(initial_capital=10000)

        try:
            data = json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
            portfolio = cls(initial_capital=data["initial_capital"])
            portfolio.cash = data["cash"]
            portfolio.daily_trades = data.get("daily_trades", 0)
            portfolio.daily_wins = data.get("daily_wins", 0)
            portfolio.cooldown = data.get("cooldown", {})
            portfolio.trade_history = data.get("trade_history", [])

            for symbol, pos_data in data.get("positions", {}).items():
                portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=pos_data["quantity"],
                    avg_entry_price=pos_data["avg_entry_price"],
                    current_price=pos_data["current_price"],
                    stop_loss=pos_data.get("stop_loss", 0),
                    take_profit=pos_data.get("take_profit", 0),
                )

            logger.info(f"Loaded portfolio: ₹{portfolio.cash:.2f} cash, {len(portfolio.positions)} positions")
            return portfolio
        except Exception as e:
            logger.error(f"Error loading portfolio: {e}")
            return cls(initial_capital=10000)
