from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Type
from backtesting import Strategy


@dataclass
class StrategyConfig:
    """Configuration for a trading strategy."""
    name: str
    params: Dict[str, Any]
    trade_mode: str


class StrategyAdapter(ABC):
    """Abstract base class for strategy adapters."""
    
    name: str
    params_schema: Dict[str, Dict[str, Any]]
    
    @abstractmethod
    def get_bt_strategy_class(self) -> Type[Strategy]:
        """Return the backtesting.py Strategy class."""
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate strategy parameters against the schema."""
        for param_name, param_info in self.params_schema.items():
            if param_name not in params:
                if "default" not in param_info:
                    return False
                continue
                
            value = params[param_name]
            param_type = param_info["type"]
            
            # Type validation
            if param_type == "int" and not isinstance(value, int):
                return False
            elif param_type == "float" and not isinstance(value, (int, float)):
                return False
            
            # Range validation
            if "min" in param_info and value < param_info["min"]:
                return False
            if "max" in param_info and value > param_info["max"]:
                return False
        
        return True
    
    def get_default_params(self) -> Dict[str, Any]:
        """Get default parameters for the strategy."""
        return {
            name: info.get("default", None)
            for name, info in self.params_schema.items()
            if "default" in info
        }
