import pandas as pd
import numpy as np
from utils.logger import setup_logger

logger = setup_logger("analyzer")


class PerformanceAnalyzer:
    @staticmethod
    def calculate_sharpe_ratio(equity_curve: list, risk_free_rate: float = 0.02) -> float:
        if not equity_curve or len(equity_curve) < 2:
            return 0.0

        equity = pd.Series([e["equity"] for e in equity_curve])
        returns = equity.pct_change().dropna()

        if returns.empty or returns.std() == 0:
            return 0.0

        excess_returns = returns.mean() - (risk_free_rate / 252)
        sharpe = np.sqrt(252) * excess_returns / returns.std()
        return round(sharpe, 2)

    @staticmethod
    def calculate_max_drawdown(equity_curve: list) -> float:
        if not equity_curve:
            return 0.0

        equity = [e["equity"] for e in equity_curve]
        peak = equity[0]
        max_drawdown = 0.0

        for value in equity:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return round(max_drawdown * 100, 2)

    @staticmethod
    def analyze(results: dict) -> dict:
        if "error" in results:
            return results

        equity_curve = results.get("equity_curve", [])

        analysis = {
            "total_return_pct": results.get("total_return_pct", 0),
            "total_pnl": results.get("total_pnl", 0),
            "total_trades": results.get("total_trades", 0),
            "win_rate": results.get("win_rate", 0),
            "profit_factor": results.get("profit_factor", 0),
            "avg_win": results.get("avg_win", 0),
            "avg_loss": results.get("avg_loss", 0),
            "sharpe_ratio": PerformanceAnalyzer.calculate_sharpe_ratio(equity_curve),
            "max_drawdown_pct": PerformanceAnalyzer.calculate_max_drawdown(equity_curve),
        }

        if analysis["total_trades"] > 0:
            analysis["profitable"] = analysis["total_pnl"] > 0
            analysis["meets_criteria"] = (
                analysis["win_rate"] >= 40 and
                analysis["sharpe_ratio"] >= 0.5 and
                analysis["max_drawdown_pct"] <= 20 and
                analysis["total_return_pct"] > 0
            )
        else:
            analysis["profitable"] = False
            analysis["meets_criteria"] = False

        return analysis

    @staticmethod
    def print_report(analysis: dict, strategy_name: str):
        logger.info("=" * 50)
        logger.info(f"BACKTEST REPORT: {strategy_name}")
        logger.info("=" * 50)
        logger.info(f"Total Return:     {analysis.get('total_return_pct', 0):.2f}%")
        logger.info(f"Total P&L:        ₹{analysis.get('total_pnl', 0):,.2f}")
        logger.info(f"Total Trades:     {analysis.get('total_trades', 0)}")
        logger.info(f"Win Rate:         {analysis.get('win_rate', 0):.1f}%")
        logger.info(f"Profit Factor:    {analysis.get('profit_factor', 0):.2f}")
        logger.info(f"Avg Win:          ₹{analysis.get('avg_win', 0):,.2f}")
        logger.info(f"Avg Loss:         ₹{analysis.get('avg_loss', 0):,.2f}")
        logger.info(f"Sharpe Ratio:     {analysis.get('sharpe_ratio', 0):.2f}")
        logger.info(f"Max Drawdown:     {analysis.get('max_drawdown_pct', 0):.2f}%")
        logger.info("-" * 50)

        meets = analysis.get('meets_criteria', False)
        logger.info(f"Meets Criteria:   {'YES' if meets else 'NO'}")
        logger.info("=" * 50)
