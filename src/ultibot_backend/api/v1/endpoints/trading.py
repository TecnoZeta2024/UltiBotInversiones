"""
Endpoints de la API para la ejecución y gestión de operaciones de trading.
"""
import logging
from decimal import Decimal
from typing import Optional, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ultibot_backend.core.domain_models.trading import OrderSide, OrderType, Order
from ultibot_backend.dependencies import TradingEngineDep
from ultibot_backend.app_config import get_app_settings

router = APIRouter(prefix="/trading", tags=["Trading"])
logger = logging.getLogger(__name__)

TradingMode = Literal["paper", "real"]

class PlaceOrderRequest(BaseModel):
    """Modelo de solicitud para colocar una nueva orden."""
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Optional[Decimal] = None  # Requerido para órdenes LIMIT
    order_type: OrderType
    strategy_id: Optional[str] = None
    trading_mode: TradingMode


# El endpoint /confirm-opportunity ha sido deshabilitado temporalmente para su refactorización.
# Se restaurará en una fase posterior alineado con la arquitectura CQRS.

@router.post("/order", response_model=Order)
async def place_order(
    request: PlaceOrderRequest,
    trading_engine: TradingEngineDep,
):
    """
    Coloca una nueva orden de trading en el sistema.
    """
    try:
        logger.info(f"Recibida solicitud de orden: {request.model_dump_json()}")

        # Obtener user_id de la configuración (solución temporal)
        settings = get_app_settings()
        user_id = UUID(settings.fixed_user_id)

        # El TradingEngine se encarga de la lógica de ejecución.
        order_result = await trading_engine.execute_order(
            symbol=request.symbol,
            order_type=request.order_type,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            trading_mode=request.trading_mode,
            user_id=user_id,
            strategy_id=UUID(request.strategy_id) if request.strategy_id else None,
        )
        return order_result

    except ValueError as ve:
        logger.warning(f"Error de validación al colocar la orden: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error inesperado al colocar la orden: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo procesar la orden: {str(e)}"
        )
