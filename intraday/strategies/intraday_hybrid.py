import pandas as pd
from strategies.base import Signal
from strategies.vwap import VWAPStrategy
from strategies.breakout import BreakoutStrategy
from strategies.momentum import MomentumStrategy
from utils.logger import setup_logger

logger = setup_logger("intraday_hybrid")


class IntradayHybrid:
    def __init__(self):
        self.strategies = [
            VWAPStrategy(),
            BreakoutStrategy(),
            MomentumStrategy(),
        ]

    def get_signal(self, df):
        signals = {}
        for strategy in self.strategies:
            signal = strategy.generate_signal(df)
            signals[strategy.name] = signal

        buy_count = sum(1 for s in signals.values() if s == Signal.BUY)
        sell_count = sum(1 for s in signals.values() if s == Signal.SELL)

        if buy_count >= 1:
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
