from typing import Dict, List, Optional
from .strategy_base import StrategyAdapter


class StrategyRegistry:
    """Registry for managing trading strategies."""
    
    def __init__(self):
        self._strategies: Dict[str, StrategyAdapter] = {}
    
    def register(self, strategy: StrategyAdapter) -> None:
        """Register a new strategy."""
        self._strategies[strategy.name] = strategy
    
    def get(self, name: str) -> Optional[StrategyAdapter]:
        """Get a strategy by name."""
        return self._strategies.get(name)
    
    def list_all(self) -> List[str]:
        """List all available strategy names."""
        return list(self._strategies.keys())
    
    def get_all(self) -> Dict[str, StrategyAdapter]:
        """Get all registered strategies."""
        return self._strategies.copy()


# Global registry instance
registry = StrategyRegistry()


def register_default_strategies():
    """Register the default strategies."""
    from strategies.ema_crossover import EMACrossoverAdapter
    
    registry.register(EMACrossoverAdapter())


# Register default strategies when module is imported
register_default_strategies()
