import pandas as pd
from strategies.base import Signal
from strategies.moving_average import MovingAverageStrategy
from strategies.rsi import RSIStrategy
from strategies.macd import MACDStrategy
from data.fundamentals import FundamentalAnalyzer
from utils.logger import setup_logger

logger = setup_logger("hybrid")


class HybridStrategy:
    def __init__(self):
        self.strategies = [
            MovingAverageStrategy(),
            RSIStrategy(),
            MACDStrategy(),
        ]
        self.fundamental_analyzer = FundamentalAnalyzer()

    def get_technical_signal(self, df: pd.DataFrame) -> dict:
        signals = {}
        for strategy in self.strategies:
            signal = strategy.generate_signal(df)
            signals[strategy.name] = signal

        buy_count = sum(1 for s in signals.values() if s == Signal.BUY)
        sell_count = sum(1 for s in signals.values() if s == Signal.SELL)

        if buy_count >= 2:
            consensus = Signal.BUY
        elif sell_count >= 2:
            consensus = Signal.SELL
        else:
            consensus = Signal.HOLD

        return {
            "consensus": consensus,
            "individual": {k: v.value for k, v in signals.items()},
            "buy_votes": buy_count,
            "sell_votes": sell_count,
        }

    def generate_hybrid_signal(self, df: pd.DataFrame, fundamentals: dict = None, news_sentiment: float = 50) -> dict:
        technical = self.get_technical_signal(df)
        tech_signal = technical["consensus"]

        fund_score = 50
        if fundamentals:
            fund_result = self.fundamental_analyzer.analyze(fundamentals)
            fund_score = fund_result["total_score"]

        tech_score_map = {Signal.BUY: 80, Signal.HOLD: 50, Signal.SELL: 20}
        tech_score = tech_score_map.get(tech_signal, 50)

        combined_score = (fund_score * 0.4) + (news_sentiment * 0.3) + (tech_score * 0.3)

        if tech_signal == Signal.BUY:
            if combined_score >= 70:
                final_signal = Signal.BUY
                confidence = "HIGH"
            elif combined_score >= 50:
                final_signal = Signal.BUY
                confidence = "MEDIUM"
            else:
                final_signal = Signal.HOLD
                confidence = "LOW (fundamentals weak)"
        elif tech_signal == Signal.SELL:
            if combined_score <= 30:
                final_signal = Signal.SELL
                confidence = "HIGH"
            elif combined_score <= 50:
                final_signal = Signal.SELL
                confidence = "MEDIUM"
            else:
                final_signal = Signal.HOLD
                confidence = "LOW (fundamentals strong)"
        else:
            final_signal = Signal.HOLD
            confidence = "N/A"

        return {
            "final_signal": final_signal,
            "confidence": confidence,
            "technical": technical,
            "fundamental_score": fund_score,
            "news_sentiment": news_sentiment,
            "combined_score": round(combined_score, 2),
        }
