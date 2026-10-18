import pandas as pd
from strategies.base import BaseStrategy, Signal
from utils.logger import setup_logger

logger = setup_logger("vwap")


class VWAPStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("VWAP")

    def calculate_indicators(self, df):
        df = df.copy()
        df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3
        df["tp_vol"] = df["typical_price"] * df["volume"]
        df["cum_tp_vol"] = df["tp_vol"].cumsum()
        df["cum_vol"] = df["volume"].cumsum()
        df["vwap"] = df["cum_tp_vol"] / df["cum_vol"]
        df["vwap_sma"] = df["vwap"].rolling(window=10).mean()
        df["volume_sma"] = df["volume"].rolling(window=20).mean()
        return df

    def generate_signal(self, df):
        if len(df) < 25:
            return Signal.HOLD

        df = self.calculate_indicators(df)

        curr_close = df["close"].iloc[-1]
        prev_close = df["close"].iloc[-2]
        curr_vwap = df["vwap"].iloc[-1]
        prev_vwap = df["vwap"].iloc[-2]
        curr_vol = df["volume"].iloc[-1]
        avg_vol = df["volume_sma"].iloc[-1]

        vol_ok = curr_vol > avg_vol * 0.8 if pd.notna(avg_vol) and avg_vol > 0 else True

        if curr_close > curr_vwap and vol_ok:
            return Signal.BUY
        elif curr_close < curr_vwap:
            return Signal.SELL

        return Signal.HOLD
