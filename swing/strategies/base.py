from abc import ABC, abstractmethod
import pandas as pd
from enum import Enum
from utils.logger import setup_logger

logger = setup_logger("strategy")


class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class BaseStrategy(ABC):
    def __init__(self, name: str, params: dict = None):
        self.name = name
        self.params = params or {}
        self.position = 0

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        pass

    def on_signal(self, signal: Signal, symbol: str, price: float) -> dict:
        if signal == Signal.BUY and self.position == 0:
            self.position = 1
            logger.info(f"[{self.name}] BUY signal for {symbol} @ ${price:.2f}")
            return {"action": "BUY", "symbol": symbol, "price": price, "strategy": self.name}
        elif signal == Signal.SELL and self.position == 1:
            self.position = 0
            logger.info(f"[{self.name}] SELL signal for {symbol} @ ${price:.2f}")
            return {"action": "SELL", "symbol": symbol, "price": price, "strategy": self.name}
        return None
