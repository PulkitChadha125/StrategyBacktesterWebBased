from typing import Type
import pandas as pd
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

class EMACrossBT(Strategy):
    # Strategy parameters (set via bt.run(**params))
    fast_ema: int = 12
    slow_ema: int = 26
    trade_mode: str = "Both_Buy_Sell"  # Only_Buy | Only_Sell | Both_Buy_Sell

    def init(self):
        close = self.data.Close
        # Use pandas ewm for EMA calculation - integrates with backtesting.py's indicator pipeline
        # Convert backtesting._Array to pandas Series for ewm calculation
        def ema(data, period):
            # Convert to pandas Series if needed and calculate EMA
            # Use modern .s accessor instead of deprecated .to_series()
            if hasattr(data, 's'):
                data_series = data.s
            else:
                data_series = pd.Series(data)
            return data_series.ewm(span=period).mean()
        
        self.fast = self.I(ema, close, self.fast_ema)
        self.slow = self.I(ema, close, self.slow_ema)

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
