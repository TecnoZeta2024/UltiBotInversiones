"""
Endpoints de la API para la ejecución y gestión de operaciones de trading.
"""
import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel

from src.shared.data_types import ConfirmRealTradeRequest, Trade
from src.ultibot_backend.services.trading_engine import TradingEngineService
from src.ultibot_backend.core.ports import IOrderExecutionPort
from src.ultibot_backend.dependencies import TradingEngineDep
from src.ultibot_backend.core.domain_models.commands import PlaceOrderCommand

router = APIRouter(prefix="/trading", tags=["Trading"])
logger = logging.getLogger(__name__)

TradingMode = Literal["paper", "real"]

class MarketOrderRequest(BaseModel):
    """Modelo de solicitud para una orden de mercado."""
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float
    trading_mode: TradingMode

@router.post("/confirm-opportunity", response_model=Trade)
async def confirm_opportunity(
    request: ConfirmRealTradeRequest,
    trading_engine: TradingEngineService = TradingEngineDep,
):
    """
    Confirma una oportunidad de trading para su ejecución.
    El TradingEngine se encargará de la lógica de validación y ejecución.
    """
    try:
        logger.info(f"Confirmando oportunidad {request.opportunity_id} para el usuario {request.user_id}")
        trade = await trading_engine.execute_trade_from_opportunity(
            opportunity_id=request.opportunity_id,
            user_id=request.user_id
        )
        return trade
    except ValueError as e:
        logger.warning(f"Error de validación al confirmar oportunidad: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Error de permisos al confirmar oportunidad: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado al confirmar oportunidad: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error inesperado al ejecutar la operación.")

@router.post("/market-order", response_model=Trade)
async def execute_market_order(
    request: MarketOrderRequest,
    # Nota: La inyección directa de un puerto puede ser un anti-patrón.
    # Idealmente, esto debería pasar a través de un servicio de aplicación.
    # Se mantiene por ahora para no alterar la lógica existente, pero se marca para revisión.
    trading_engine: TradingEngineService = TradingEngineDep,
):
    """
    Ejecuta una orden de mercado directamente a través del TradingEngineService.
    """
    try:
        logger.info(f"Ejecutando orden de mercado: {request.model_dump_json()}")
        command = PlaceOrderCommand(
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            order_type="MARKET",
            is_real_trade=(request.trading_mode == "real")
        )
        # El TradingEngineService ahora manejará la ejecución de la orden
        trade_result = await trading_engine.execute_manual_order(command)
        return trade_result
    except Exception as e:
        logger.error(f"Error al ejecutar orden de mercado: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo ejecutar la orden de mercado: {str(e)}"
        )
