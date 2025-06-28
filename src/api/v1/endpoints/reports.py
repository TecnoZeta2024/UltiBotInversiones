"""
API endpoints para generar informes de trading y métricas de rendimiento.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel

from shared.data_types import Trade, PerformanceMetrics
from services.trading_report_service import TradingReportService
from app_config import get_app_settings
from dependencies import get_trading_report_service

# Configurar logging
logger = logging.getLogger(__name__)

# Crear el router
router = APIRouter()

# Modelos para los parámetros de consulta
class TradeFilters(BaseModel):
    """Filtros para consultar trades históricos."""
    symbol: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0

class TradeHistoryResponse(BaseModel):
    """Respuesta para el historial de trades."""
    trades: List[Trade]
    total_count: int
    has_more: bool
