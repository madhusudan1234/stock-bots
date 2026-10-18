import pandas as pd
from strategies.base import BaseStrategy, Signal
from config.settings import STRATEGIES
from utils.logger import setup_logger

logger = setup_logger("macd")


class MACDStrategy(BaseStrategy):
    def __init__(self):
        params = STRATEGIES["macd"]
        super().__init__("MACD", params)
        self.fast_period = params["fast_period"]
        self.slow_period = params["slow_period"]
        self.signal_period = params["signal_period"]

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["ema_fast"] = df["close"].ewm(span=self.fast_period, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=self.slow_period, adjust=False).mean()
        df["macd"] = df["ema_fast"] - df["ema_slow"]
        df["signal_line"] = df["macd"].ewm(span=self.signal_period, adjust=False).mean()
        df["histogram"] = df["macd"] - df["signal_line"]
        df["sma_trend"] = df["close"].rolling(window=50).mean()
        return df

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        if len(df) < 55:
            return Signal.HOLD

        df = self.calculate_indicators(df)

        current_price = df["close"].iloc[-1]
        current_macd = df["macd"].iloc[-1]
        current_signal = df["signal_line"].iloc[-1]
        prev_macd = df["macd"].iloc[-2]
        prev_signal = df["signal_line"].iloc[-2]
        current_trend = df["sma_trend"].iloc[-1]

        above_trend = current_price > current_trend

        if prev_macd <= prev_signal and current_macd > current_signal and above_trend:
            return Signal.BUY
        elif prev_macd >= prev_signal and current_macd < current_signal:
            return Signal.SELL

        return Signal.HOLD
