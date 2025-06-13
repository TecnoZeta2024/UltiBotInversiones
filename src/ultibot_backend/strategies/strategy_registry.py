from typing import Dict, Type, Optional
from .base_strategy import BaseStrategy

class StrategyRegistry:
    """
    Registro central para todas las estrategias de trading disponibles.
    Permite registrar y recuperar clases de estrategias por su nombre.
    """
    _strategies: Dict[str, Type[BaseStrategy]] = {}

    @classmethod
    def register(cls, name: str):
        """
        Decorador para registrar una clase de estrategia.
        """
        def decorator(strategy_cls: Type[BaseStrategy]):
            if not issubclass(strategy_cls, BaseStrategy):
                raise TypeError("La clase registrada debe heredar de BaseStrategy")
            cls._strategies[name] = strategy_cls
            return strategy_cls
        return decorator

    @classmethod
    def get_strategy(cls, name: str) -> Optional[Type[BaseStrategy]]:
        """
        Obtiene una clase de estrategia por su nombre.
        """
        return cls._strategies.get(name)

    @classmethod
    def get_all_strategies(cls) -> Dict[str, Type[BaseStrategy]]:
        """
        Devuelve un diccionario con todas las estrategias registradas.
        """
        return cls._strategies.copy()
