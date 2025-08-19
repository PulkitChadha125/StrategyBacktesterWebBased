from typing import Type, Optional
import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover
from core.strategy_base import StrategyAdapter

class EMACrossoverAdapter(StrategyAdapter):
    name = "EMA Crossover"
    params_schema = {
        "fast_ema": {"type": "int", "default": 12, "min": 1, "max": 100, "description": "Fast EMA period"},
        "slow_ema": {"type": "int", "default": 26, "min": 2, "max": 200, "description": "Slow EMA period"},
    }

    def get_bt_strategy_class(self) -> Type[Strategy]:
        return EMACrossBT

def _ema_pandas(data, period: int):
    # Works for backtesting DataSeries (with .s) or raw arrays/Series
    s = data.s if hasattr(data, "s") else pd.Series(data)
    return s.ewm(span=int(period), adjust=False).mean().to_numpy()

def _ema_talib_or_pandas(data, period: int):
    # Try TA-Lib; if unavailable, fallback to pandas vectorized EMA
    try:
        import talib  # noqa
        s = data.s if hasattr(data, "s") else pd.Series(data)
        out = talib.EMA(s.values.astype(float), timeperiod=int(period))
        return out
    except Exception:
        # Fallback
        return _ema_pandas(data, period)

class EMACrossBT(Strategy):
    # Parameters populated by bt.run(**params)
    fast_ema: int = 12
    slow_ema: int = 26
    trade_mode: str = "Both_Buy_Sell"    # Only_Buy | Only_Sell | Both_Buy_Sell
    indicator_engine: str = "pandas"     # "pandas" or "TA-Lib"

    def init(self):
        close = self.data.Close
        engine = (self.indicator_engine or "pandas").lower()
        if engine.startswith("ta"):
            self.fast = self.I(_ema_talib_or_pandas, close, self.fast_ema)
            self.slow = self.I(_ema_talib_or_pandas, close, self.slow_ema)
        else:
            self.fast = self.I(_ema_pandas, close, self.fast_ema)
            self.slow = self.I(_ema_pandas, close, self.slow_ema)

    def next(self):
        up = crossover(self.fast, self.slow)      # fast crosses ABOVE slow
        down = crossover(self.slow, self.fast)    # fast crosses BELOW slow

        mode = self.trade_mode

        if mode == "Only_Buy":
            if self.position.is_short:
                self.position.close()
            if up and not self.position.is_long:
                self.buy()
            if self.position.is_long and down:
                self.position.close()
            return

        if mode == "Only_Sell":
            if self.position.is_long:
                self.position.close()
            if down and not self.position.is_short:
                self.sell()
            if self.position.is_short and up:
                self.position.close()
            return

        # Both_Buy_Sell
        if up:
            if self.position.is_short:
                self.position.close()
            if not self.position.is_long:
                self.buy()
        elif down:
            if self.position.is_long:
                self.position.close()
            if not self.position.is_short:
                self.sell()
