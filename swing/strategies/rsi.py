import pandas as pd
from strategies.base import BaseStrategy, Signal
from config.settings import STRATEGIES
from utils.logger import setup_logger

logger = setup_logger("rsi")


class RSIStrategy(BaseStrategy):
    def __init__(self):
        params = STRATEGIES["rsi"]
        super().__init__("RSI", params)
        self.period = params["period"]
        self.oversold = params["oversold"]
        self.overbought = params["overbought"]

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))
        df["rsi_sma"] = df["rsi"].rolling(window=5).mean()
        df["sma_trend"] = df["close"].rolling(window=50).mean()
        return df

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        if len(df) < 55:
            return Signal.HOLD

        df = self.calculate_indicators(df)

        current_price = df["close"].iloc[-1]
        current_rsi = df["rsi"].iloc[-1]
        prev_rsi = df["rsi"].iloc[-2]
        current_trend = df["sma_trend"].iloc[-1]

        above_trend = current_price > current_trend

        if current_rsi < 30 and current_rsi > prev_rsi and above_trend:
            return Signal.BUY
        elif prev_rsi >= self.overbought and current_rsi < self.overbought and above_trend:
            return Signal.SELL

        return Signal.HOLD
