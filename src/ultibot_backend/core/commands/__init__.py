"""
Módulo de inicialización para el paquete commands.
Define los comandos del sistema, que representan intenciones de mutación de estado.
Estos comandos son modelos Pydantic puros y no deben contener lógica de negocio.
"""

from .trading_commands import (
    PlaceOrderCommand, CancelOrderCommand, ActivateStrategyCommand,
    DeactivateStrategyCommand, UpdateConfigCommand
)
