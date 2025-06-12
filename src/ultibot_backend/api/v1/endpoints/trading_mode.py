"""
API endpoints for managing the trading mode.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal

from src.ultibot_backend.services.configuration_service import ConfigurationService
from src.ultibot_backend.dependencies import get_service
from src.ultibot_backend.app_config import settings

router = APIRouter(prefix="/trading-mode", tags=["Trading Mode"])
logger = logging.getLogger(__name__)

TradingMode = Literal["paper", "real"]

class TradingModePayload(BaseModel):
    mode: TradingMode

@router.post("/", status_code=status.HTTP_200_OK)
async def set_trading_mode(
    payload: TradingModePayload,
    config_service: ConfigurationService = Depends(get_service(ConfigurationService)),
):
    """
    Sets the application's trading mode (paper or real).
    """
    user_id = settings.FIXED_USER_ID
    try:
        if payload.mode == "real":
            await config_service.activate_real_trading_mode(user_id)
        else:
            await config_service.deactivate_real_trading_mode(user_id)
        
        logger.info(f"Trading mode for user {user_id} set to {payload.mode}")
        return {"message": f"Trading mode successfully set to {payload.mode}"}
    except Exception as e:
        logger.error(f"Failed to set trading mode to {payload.mode}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=TradingModePayload)
async def get_trading_mode(
    config_service: ConfigurationService = Depends(get_service(ConfigurationService)),
):
    """
    Gets the application's current trading mode.
    """
    user_id = settings.FIXED_USER_ID
    try:
        status_data = await config_service.get_real_trading_status(user_id)
        current_mode = "real" if status_data.get("is_active") else "paper"
        return {"mode": current_mode}
    except Exception as e:
        logger.error(f"Failed to get trading mode: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
