import pandas as pd
from strategies.base import BaseStrategy, Signal
from config.settings import STRATEGIES
from utils.logger import setup_logger

logger = setup_logger("momentum")


class MomentumStrategy(BaseStrategy):
    def __init__(self):
        params = STRATEGIES["momentum"]
        super().__init__("Momentum", params)
        self.volume_multiplier = params["volume_multiplier"]
        self.price_change_pct = params["price_change_pct"]
        self.lookback = params["lookback"]

    def calculate_indicators(self, df):
        df = df.copy()
        df["volume_sma"] = df["volume"].rolling(window=20).mean()
        df["price_change"] = df["close"].pct_change(periods=self.lookback) * 100
        df["ema_9"] = df["close"].ewm(span=9).mean()
        df["ema_21"] = df["close"].ewm(span=21).mean()
        return df

    def generate_signal(self, df):
        if len(df) < 25:
            return Signal.HOLD

        df = self.calculate_indicators(df)

        curr_vol = df["volume"].iloc[-1]
        avg_vol = df["volume_sma"].iloc[-1]
        price_change = df["price_change"].iloc[-1]
        ema_9 = df["ema_9"].iloc[-1]
        ema_21 = df["ema_21"].iloc[-1]
        prev_ema_9 = df["ema_9"].iloc[-2]
        prev_ema_21 = df["ema_21"].iloc[-2]

        vol_spike = curr_vol > avg_vol * self.volume_multiplier if pd.notna(avg_vol) and pd.notna(curr_vol) and curr_vol > 0 else False

        if vol_spike and price_change > self.price_change_pct and ema_9 > ema_21:
            return Signal.BUY
        elif vol_spike and price_change < -self.price_change_pct and ema_9 < ema_21:
            return Signal.SELL

        return Signal.HOLD
