import pandas as pd
from strategies.base import BaseStrategy, Signal
from config.settings import STRATEGIES
from utils.logger import setup_logger

logger = setup_logger("breakout")


class BreakoutStrategy(BaseStrategy):
    def __init__(self):
        params = STRATEGIES["breakout"]
        super().__init__("Breakout", params)
        self.lookback = params["lookback"]

    def calculate_indicators(self, df):
        df = df.copy()
        df["high_n"] = df["high"].rolling(window=self.lookback).max()
        df["low_n"] = df["low"].rolling(window=self.lookback).min()
        df["range_mid"] = (df["high_n"] + df["low_n"]) / 2
        df["volume_sma"] = df["volume"].rolling(window=20).mean()
        return df

    def generate_signal(self, df):
        if len(df) < 25:
            return Signal.HOLD

        df = self.calculate_indicators(df)

        curr_close = df["close"].iloc[-1]
        prev_close = df["close"].iloc[-2]
        prev_high = df["high_n"].iloc[-2]
        prev_low = df["low_n"].iloc[-2]
        curr_vol = df["volume"].iloc[-1]
        avg_vol = df["volume_sma"].iloc[-1]

        vol_ok = curr_vol > avg_vol * 1.2 if pd.notna(avg_vol) else True

        if curr_close > prev_high and vol_ok:
            return Signal.BUY
        elif curr_close < prev_low:
            return Signal.SELL

        return Signal.HOLD
