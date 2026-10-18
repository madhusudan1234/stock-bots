from abc import ABC, abstractmethod
from enum import Enum
import pandas as pd


class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class BaseStrategy(ABC):
    def __init__(self, name, params=None):
        self.name = name
        self.params = params or {}
        self.position = 0

    @abstractmethod
    def calculate_indicators(self, df):
        pass

    @abstractmethod
    def generate_signal(self, df):
        pass

    def on_signal(self, signal, symbol, price):
        if signal == Signal.BUY and self.position == 0:
            self.position = 1
            return {"action": "BUY", "symbol": symbol, "price": price}
        elif signal == Signal.SELL and self.position == 1:
            self.position = 0
            return {"action": "SELL", "symbol": symbol, "price": price}
        return None
