import json
from dataclasses import dataclass, asdict
from pathlib import Path
from config.settings import CAPITAL, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT, MAX_POSITIONS
from utils.logger import setup_logger

logger = setup_logger("intraday_portfolio")

PORTFOLIO_FILE = Path(__file__).resolve().parent.parent / "intraday_portfolio.json"


@dataclass
class Position:
    symbol: str
    quantity: int
    avg_entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    strategy: str

    @property
    def market_value(self):
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self):
        return (self.current_price - self.avg_entry_price) * self.quantity

    @property
    def unrealized_pnl_pct(self):
        return ((self.current_price - self.avg_entry_price) / self.avg_entry_price) * 100


class IntradayPortfolio:
    def __init__(self, initial_capital=CAPITAL):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.trade_history = []
        self.daily_trades = 0
        self.daily_wins = 0
        self.recently_sold = {}
        self.last_reset_date = None

    def can_open_position(self):
        return len(self.positions) < MAX_POSITIONS

    def buy(self, symbol, quantity, price, strategy, stop_loss=None, take_profit=None):
        if not self.can_open_position():
            logger.info(f"Max positions ({MAX_POSITIONS}) reached")
            return False

        cost = quantity * price
        if cost > self.cash:
            logger.info(f"Insufficient cash for {symbol}: need {cost}, have {self.cash}")
            return False

        if symbol in self.positions:
            pos = self.positions[symbol]
            total_qty = pos.quantity + quantity
            pos.avg_entry_price = (pos.avg_entry_price * pos.quantity + price * quantity) / total_qty
            pos.quantity = total_qty
            pos.current_price = price
            self.cash -= cost
        else:
            if stop_loss is None:
                stop_loss = price * (1 - STOP_LOSS_PERCENT)
            if take_profit is None:
                take_profit = price * (1 + TAKE_PROFIT_PERCENT)

            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_entry_price=price,
                current_price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy=strategy,
            )
            self.cash -= cost

        self.daily_trades += 1
        self.trade_history.append({
            "action": "BUY",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "strategy": strategy,
        })
        logger.info(f"BOUGHT {quantity} {symbol} @ {price}")
        return True

    def sell(self, symbol, price, reason=""):
        if symbol not in self.positions:
            return 0

        pos = self.positions[symbol]
        pnl = (price - pos.avg_entry_price) * pos.quantity
        proceeds = pos.quantity * price
        self.cash += proceeds

        if pnl > 0:
            self.daily_wins += 1

        self.daily_trades += 1
        self.trade_history.append({
            "action": "SELL",
            "symbol": symbol,
            "quantity": pos.quantity,
            "price": price,
            "pnl": pnl,
            "reason": reason,
        })

        del self.positions[symbol]
        self.recently_sold[symbol] = price
        logger.info(f"SOLD {symbol} @ {price} | P&L: {pnl:+.2f} ({reason})")
        return pnl

    def can_reenter(self, symbol, current_price, pullback_pct=0.003):
        if symbol not in self.recently_sold:
            return True
        sell_price = self.recently_sold[symbol]
        pullback = (sell_price - current_price) / sell_price
        return pullback >= pullback_pct

    def check_stop_loss_take_profit(self, prices):
        triggered = []
        for symbol in list(self.positions.keys()):
            if symbol not in prices:
                continue
            pos = self.positions[symbol]
            current = prices[symbol]
            pos.current_price = current

            profit_pct = (current - pos.avg_entry_price) / pos.avg_entry_price
            if profit_pct >= 0.01 and pos.stop_loss < pos.avg_entry_price:
                pos.stop_loss = pos.avg_entry_price
                logger.info(f"  {symbol}: Trailing stop moved to breakeven @ {pos.avg_entry_price:.2f}")

            if current <= pos.stop_loss:
                pnl = self.sell(symbol, current, "STOP LOSS")
                triggered.append({"symbol": symbol, "price": current, "action": "STOP LOSS", "pnl": pnl})
            elif current >= pos.take_profit:
                pnl = self.sell(symbol, current, "TAKE PROFIT")
                triggered.append({"symbol": symbol, "price": current, "action": "TAKE PROFIT", "pnl": pnl})

        return triggered

    def square_off_all(self, prices):
        closed = []
        for symbol in list(self.positions.keys()):
            if symbol in prices:
                pnl = self.sell(symbol, prices[symbol], "SQUARE OFF")
                closed.append({"symbol": symbol, "pnl": pnl})
            else:
                pnl = self.sell(symbol, self.positions[symbol].current_price, "SQUARE OFF")
                closed.append({"symbol": symbol, "pnl": pnl})
        return closed

    def update_prices(self, prices):
        for symbol, pos in self.positions.items():
            if symbol in prices:
                pos.current_price = prices[symbol]

    def get_positions_value(self):
        return sum(pos.market_value for pos in self.positions.values())

    def get_total_value(self):
        return self.cash + self.get_positions_value()

    def get_total_pnl(self):
        return self.get_total_value() - self.initial_capital

    def get_summary(self):
        total_value = self.get_total_value()
        total_return = ((total_value - self.initial_capital) / self.initial_capital) * 100
        win_rate = (self.daily_wins / max(1, self.daily_trades // 2)) * 100

        return {
            "cash": round(self.cash, 2),
            "positions_value": round(self.get_positions_value(), 2),
            "total_value": round(total_value, 2),
            "total_return_pct": round(total_return, 2),
            "daily_trades": self.daily_trades,
            "daily_win_rate": round(win_rate, 1),
        }

    def print_summary(self):
        s = self.get_summary()
        logger.info("=" * 55)
        logger.info("PORTFOLIO SUMMARY")
        logger.info("=" * 55)
        logger.info(f"Cash:             {s['cash']}")
        logger.info(f"Positions Value:  {s['positions_value']}")
        logger.info(f"Total Value:      {s['total_value']}")
        logger.info(f"Total Return:     {s['total_return_pct']}%")
        logger.info(f"Today's Trades:   {s['daily_trades']} | Win Rate: {s['daily_win_rate']}%")

        if self.positions:
            logger.info("-" * 55)
            logger.info("POSITIONS:")
            for symbol, pos in self.positions.items():
                logger.info(
                    f"  {symbol}: {pos.quantity} shares | "
                    f"Entry: {pos.avg_entry_price:.2f} | "
                    f"Current: {pos.current_price:.2f} | "
                    f"P&L: {pos.unrealized_pnl:+.2f} ({pos.unrealized_pnl_pct:+.1f}%)"
                )
        logger.info("=" * 55)

    def reset_daily(self):
        from datetime import date
        today = date.today().isoformat()
        if self.last_reset_date == today:
            return

        if self.positions:
            logger.warning(
                f"Found {len(self.positions)} leftover position(s) from previous day - "
                f"closing at last known prices"
            )
            for symbol in list(self.positions.keys()):
                pos = self.positions[symbol]
                self.sell(symbol, pos.current_price, "RESET CLEANUP")

        self.daily_trades = 0
        self.daily_wins = 0
        self.last_reset_date = today
        self.save()
        logger.info(f"Daily reset: {self.cash} cash ready for new trades")

    def save(self):
        data = {
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "daily_trades": self.daily_trades,
            "daily_wins": self.daily_wins,
            "last_reset_date": self.last_reset_date,
            "positions": {k: asdict(v) for k, v in self.positions.items()},
            "trade_history": self.trade_history[-100:],
        }
        PORTFOLIO_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls):
        if PORTFOLIO_FILE.exists():
            data = json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
            portfolio = cls(initial_capital=data.get("initial_capital", CAPITAL))
            portfolio.cash = data.get("cash", CAPITAL)
            portfolio.daily_trades = data.get("daily_trades", 0)
            portfolio.daily_wins = data.get("daily_wins", 0)
            portfolio.last_reset_date = data.get("last_reset_date")
            portfolio.trade_history = data.get("trade_history", [])
            for symbol, pos_data in data.get("positions", {}).items():
                portfolio.positions[symbol] = Position(**pos_data)
            logger.info(f"Loaded portfolio: {portfolio.cash} cash, {len(portfolio.positions)} positions")
            return portfolio
        return cls()
