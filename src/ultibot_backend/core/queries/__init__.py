"""
Módulo de inicialización para el paquete queries.
Define las consultas del sistema, que representan intenciones de lectura de estado.
Estas consultas son modelos Pydantic puros y no deben contener lógica de negocio.
"""

from .portfolio_queries import (
    GetPortfolioQuery, GetTradeHistoryQuery, GetStrategyPerformanceQuery,
    GetMarketDataQuery, GetConfigQuery
)
