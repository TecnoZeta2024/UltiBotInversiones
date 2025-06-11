# src/ultibot_backend/api/v1/endpoints/trading_mode.py
"""
API endpoints for managing the trading mode.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.ultibot_backend.services.trading_mode_service import (
    get_trading_mode_service,
    TradingMode,
    TradingModeService,
)

router = APIRouter()

class TradingModePayload(BaseModel):
    mode: TradingMode

@router.post("/trading-mode", status_code=200)
def set_trading_mode(
    payload: TradingModePayload,
    trading_mode_service: TradingModeService = Depends(get_trading_mode_service),
):
    """
    Sets the application's trading mode.
    """
    try:
        trading_mode_service.set_mode(payload.mode)
        return {"message": f"Trading mode successfully set to {payload.mode.value}"}
    except TypeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/trading-mode", response_model=TradingModePayload)
def get_trading_mode(
    trading_mode_service: TradingModeService = Depends(get_trading_mode_service),
):
    """
    Gets the application's current trading mode.
    """
    mode = trading_mode_service.get_mode()
    return {"mode": mode}
