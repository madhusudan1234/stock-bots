import pandas as pd
from strategies.base import BaseStrategy, Signal
from config.settings import STRATEGIES
from utils.logger import setup_logger

logger = setup_logger("moving_average")


class MovingAverageStrategy(BaseStrategy):
    def __init__(self):
        params = STRATEGIES["moving_average"]
        super().__init__("MovingAverage", params)
        self.short_window = params["short_window"]
        self.long_window = params["long_window"]
        self.trend_filter = params.get("trend_filter", 50)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["sma_short"] = df["close"].rolling(window=self.short_window).mean()
        df["sma_long"] = df["close"].rolling(window=self.long_window).mean()
        df["sma_trend"] = df["close"].rolling(window=self.trend_filter).mean()
        df["volume_sma"] = df["volume"].rolling(window=20).mean()
        return df

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        if len(df) < self.trend_filter + 1:
            return Signal.HOLD

        df = self.calculate_indicators(df)

        current_price = df["close"].iloc[-1]
        current_short = df["sma_short"].iloc[-1]
        current_long = df["sma_long"].iloc[-1]
        current_trend = df["sma_trend"].iloc[-1]
        prev_short = df["sma_short"].iloc[-2]
        prev_long = df["sma_long"].iloc[-2]
        current_volume = df["volume"].iloc[-1]
        avg_volume = df["volume_sma"].iloc[-1]

        above_trend = current_price > current_trend
        volume_ok = current_volume > avg_volume * 0.8

        if prev_short <= prev_long and current_short > current_long and above_trend and volume_ok:
            return Signal.BUY
        elif prev_short >= prev_long and current_short < current_long:
            return Signal.SELL

        return Signal.HOLD
