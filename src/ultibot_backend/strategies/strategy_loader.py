"""
Cargador de Estrategias Dinámico

Este módulo proporciona una forma de descubrir y cargar dinámicamente
clases de estrategia desde el directorio de estrategias.
"""

import importlib
import inspect
import os
from typing import Dict, Type

from .base_strategy import BaseStrategy

def load_strategies(path: str = "src/ultibot_backend/strategies") -> Dict[str, Type[BaseStrategy]]:
    """
    Descubre y carga dinámicamente todas las clases de estrategia que heredan de BaseStrategy.

    Args:
        path: La ruta al directorio de estrategias.

    Returns:
        Un diccionario que mapea el nombre de la estrategia a su clase.
    """
    strategies: Dict[str, Type[BaseStrategy]] = {}
    
    for filename in os.listdir(path):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            module_path = f"src.ultibot_backend.strategies.{module_name}"
            
            try:
                module = importlib.import_module(module_path)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
                        # Usar un nombre de estrategia único, como el nombre de la clase en snake_case
                        strategy_name = name.lower()
                        strategies[strategy_name] = obj
                        print(f"Estrategia cargada: {name} as '{strategy_name}'")
            except ImportError as e:
                print(f"Error al importar la estrategia desde {filename}: {e}")

    return strategies

if __name__ == '__main__':
    # Ejemplo de uso para verificar las estrategias cargadas
    loaded_strategies = load_strategies()
    print("\nEstrategias de trading disponibles:")
    for name, cls in loaded_strategies.items():
        print(f"- {name}: {cls.__doc__.strip().splitlines()[0] if cls.__doc__ else 'No description'}")
