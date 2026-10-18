import pandas as pd
from strategies.base import Signal
from utils.logger import setup_logger

logger = setup_logger("backtest")


class BacktestEngine:
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0
        self.position_price = 0
        self.trades = []
        self.equity_curve = []

    def run(self, df: pd.DataFrame, strategy) -> dict:
        logger.info(f"Running backtest for {strategy.name}")

        df = strategy.calculate_indicators(df)
        self.capital = self.initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []

        for i in range(len(df)):
            current_data = df.iloc[:i+1]
            current_price = df["close"].iloc[i]
            current_date = df.index[i]

            signal = strategy.generate_signal(current_data)

            if signal == Signal.BUY and self.position == 0:
                shares = int(self.capital // current_price)
                if shares > 0:
                    self.position = shares
                    self.position_price = current_price
                    self.capital -= shares * current_price
                    self.trades.append({
                        "date": current_date,
                        "action": "BUY",
                        "price": current_price,
                        "shares": shares,
                    })

            elif signal == Signal.SELL and self.position > 0:
                sell_price = current_price
                pnl = (sell_price - self.position_price) * self.position
                self.capital += self.position * sell_price
                self.trades.append({
                    "date": current_date,
                    "action": "SELL",
                    "price": sell_price,
                    "shares": self.position,
                    "pnl": pnl,
                })
                self.position = 0
                self.position_price = 0

            equity = self.capital + (self.position * current_price)
            self.equity_curve.append({"date": current_date, "equity": equity})

        if self.position > 0:
            final_price = df["close"].iloc[-1]
            self.capital += self.position * final_price
            self.position = 0

        return self._calculate_results()

    def _calculate_results(self) -> dict:
        equity_df = pd.DataFrame(self.equity_curve)
        if equity_df.empty:
            return {"error": "No trades executed"}

        final_equity = equity_df["equity"].iloc[-1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100

        winning_trades = [t for t in self.trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in self.trades if t.get("pnl", 0) < 0]

        total_pnl = sum(t.get("pnl", 0) for t in self.trades)
        avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0

        return {
            "initial_capital": self.initial_capital,
            "final_equity": final_equity,
            "total_return_pct": round(total_return, 2),
            "total_pnl": round(total_pnl, 2),
            "total_trades": len([t for t in self.trades if t["action"] == "SELL"]),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(len(winning_trades) / len([t for t in self.trades if t["action"] == "SELL"]) * 100, 2) if self.trades and [t for t in self.trades if t["action"] == "SELL"] else 0,
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
        }
