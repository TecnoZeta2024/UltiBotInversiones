"""
Endpoints de la API para la gestión y consulta del portafolio de trading.
"""
import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.shared.data_types import PortfolioSnapshot, PortfolioSummary
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.dependencies import PortfolioDep
from src.ultibot_backend.app_config import settings

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])
logger = logging.getLogger(__name__)

# Tipo para validar el modo de trading
TradingMode = Literal["paper", "real", "both"]

@router.get("/snapshot", response_model=PortfolioSnapshot, status_code=status.HTTP_200_OK)
async def get_portfolio_snapshot(
    portfolio_service = PortfolioDep,
    trading_mode: TradingMode = Query("both", description="Filtro de modo de trading: 'paper', 'real', o 'both'"),
):
    """
    Obtiene una instantánea del portafolio para el usuario y modo de trading especificados.
    """
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Obteniendo snapshot del portafolio para el usuario {user_id} en modo '{trading_mode}'.")
        snapshot = await portfolio_service.get_full_portfolio_snapshot(user_id, trading_mode)
        return snapshot
    except Exception as e:
        logger.error(f"Fallo al obtener el snapshot del portafolio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo obtener la instantánea del portafolio: {str(e)}",
        )

@router.get("/summary", response_model=PortfolioSummary, status_code=status.HTTP_200_OK)
async def get_portfolio_summary(
    portfolio_service = PortfolioDep,
    trading_mode: Literal["paper", "real"] = Query("paper", description="Modo de trading: 'paper' o 'real'"),
):
    """
    Obtiene un resumen del portafolio para un modo de trading específico.
    """
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Obteniendo resumen del portafolio para el usuario {user_id} en modo '{trading_mode}'.")
        summary = await portfolio_service.get_portfolio_summary(user_id, trading_mode)
        return summary
    except Exception as e:
        logger.error(f"Fallo al obtener el resumen del portafolio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo obtener el resumen del portafolio: {str(e)}",
        )

@router.get("/balance", status_code=status.HTTP_200_OK)
async def get_available_balance(
    portfolio_service = PortfolioDep,
    trading_mode: TradingMode = Query("paper", description="Modo de trading: 'paper', 'real', o 'both'"),
):
    """
    Obtiene el balance disponible para operar en el modo especificado.
    """
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Obteniendo balance disponible para el usuario {user_id} en modo '{trading_mode}'.")
        
        if trading_mode == "both":
            paper_balance = await portfolio_service.get_available_balance(user_id, "paper")
            real_balance = await portfolio_service.get_available_balance(user_id, "real")
            return {
                "trading_mode": "both",
                "paper_balance_usdt": paper_balance,
                "real_balance_usdt": real_balance,
                "currency": "USDT",
            }
        
        balance = await portfolio_service.get_available_balance(user_id, trading_mode)
        return {
            "trading_mode": trading_mode,
            "available_balance_usdt": balance,
            "currency": "USDT",
        }
            
    except Exception as e:
        logger.error(f"Fallo al obtener el balance disponible: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo obtener el balance disponible: {str(e)}",
        )
