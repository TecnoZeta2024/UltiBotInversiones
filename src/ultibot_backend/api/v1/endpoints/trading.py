from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field

from src.shared.data_types import ConfirmRealTradeRequest, OpportunityStatus, Opportunity, TradeOrderDetails
from src.ultibot_backend.services.trading_engine_service import TradingEngineService
from src.ultibot_backend.services.config_service import ConfigurationService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.unified_order_execution_service import UnifiedOrderExecutionService
from src.ultibot_backend import dependencies as deps
from src.ultibot_backend.app_config import settings

router = APIRouter()

@router.post("/real/confirm-opportunity/{opportunity_id}", status_code=status.HTTP_200_OK)
async def confirm_real_opportunity(
    opportunity_id: UUID,
    request: ConfirmRealTradeRequest,
    trading_engine_service: Annotated[TradingEngineService, Depends(deps.get_trading_engine_service)],
    config_service: Annotated[ConfigurationService, Depends(deps.get_config_service)],
    persistence_service: Annotated[SupabasePersistenceService, Depends(deps.get_persistence_service)]
):
    """
    Endpoint para que el usuario fijo confirme explícitamente una oportunidad de trading real.
    """
    user_id = settings.FIXED_USER_ID

    if opportunity_id != request.opportunity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Opportunity ID in path and request body do not match."
        )
    
    if user_id != request.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID in settings does not match user ID in request body."
        )

    opportunity = await persistence_service.get_opportunity_by_id(opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with ID {opportunity_id} not found."
        )

    if opportunity.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized to confirm this opportunity."
        )

    if opportunity.status != OpportunityStatus.PENDING_USER_CONFIRMATION_REAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Opportunity {opportunity_id} is not in 'pending_user_confirmation_real' status. Current status: {opportunity.status.value}"
        )
    
    user_config = await config_service.get_user_configuration(str(user_id))
    if not user_config or not user_config.realTradingSettings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User configuration or real trading settings not found."
        )

    real_trading_settings = user_config.realTradingSettings
    if not real_trading_settings.real_trading_mode_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Real trading mode is not active for this user."
        )
    
    if real_trading_settings.real_trades_executed_count >= real_trading_settings.max_real_trades:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Maximum number of real trades reached for this user."
        )

    try:
        trade_details = await trading_engine_service.execute_trade_from_confirmed_opportunity(opportunity)
        if not trade_details:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create trade from confirmed opportunity."
            )
        return {"message": "Real trade execution initiated successfully.", "trade_details": trade_details.model_dump()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

TradingMode = Literal["paper", "real"]

class MarketOrderRequest(BaseModel):
    """Request model for market order execution."""
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTCUSDT')")
    side: str = Field(..., description="Order side ('BUY' or 'SELL')")
    quantity: float = Field(..., gt=0, description="Order quantity (must be positive)")
    trading_mode: TradingMode = Field(..., description="Trading mode ('paper' or 'real')")
    api_key: Optional[str] = Field(None, description="API key for real trading (required for real mode)")
    api_secret: Optional[str] = Field(None, description="API secret for real trading (required for real mode)")

@router.post("/market-order", response_model=TradeOrderDetails, status_code=status.HTTP_200_OK)
async def execute_market_order(
    request: MarketOrderRequest,
    unified_execution_service: Annotated[UnifiedOrderExecutionService, Depends(deps.get_unified_order_execution_service)]
):
    """
    Execute a market order in the specified trading mode for the fixed user.
    """
    user_id = settings.FIXED_USER_ID
    try:
        if not unified_execution_service.validate_trading_mode(request.trading_mode):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid trading mode: {request.trading_mode}. Must be 'paper' or 'real'"
            )
        
        order_details = await unified_execution_service.execute_market_order(
            user_id=user_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            trading_mode=request.trading_mode,
            api_key=request.api_key,
            api_secret=request.api_secret
        )
        
        return order_details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute market order: {str(e)}"
        )

@router.get("/paper-balances", status_code=status.HTTP_200_OK)
async def get_paper_trading_balances(
    unified_execution_service: Annotated[UnifiedOrderExecutionService, Depends(deps.get_unified_order_execution_service)]
):
    """
    Get current virtual balances for paper trading for the fixed user.
    """
    user_id = settings.FIXED_USER_ID
    try:
        balances = await unified_execution_service.get_virtual_balances()
        return {
            "user_id": user_id,
            "trading_mode": "paper",
            "balances": balances
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve paper trading balances: {str(e)}"
        )

@router.post("/paper-balances/reset", status_code=status.HTTP_200_OK)
async def reset_paper_trading_balances(
    unified_execution_service: Annotated[UnifiedOrderExecutionService, Depends(deps.get_unified_order_execution_service)],
    initial_capital: float = Query(..., gt=0, description="Initial capital amount (must be positive)")
):
    """
    Reset paper trading balances to initial capital for the fixed user.
    """
    user_id = settings.FIXED_USER_ID
    try:
        unified_execution_service.reset_virtual_balances(initial_capital=initial_capital)
        return {
            "user_id": user_id,
            "trading_mode": "paper",
            "message": f"Paper trading balances reset to {initial_capital} USDT",
            "new_balance": initial_capital
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset paper trading balances: {str(e)}"
        )

@router.get("/supported-modes", status_code=status.HTTP_200_OK)
async def get_supported_trading_modes(
    unified_execution_service: Annotated[UnifiedOrderExecutionService, Depends(deps.get_unified_order_execution_service)]
):
    """
    Get list of supported trading modes.
    """
    try:
        supported_modes = unified_execution_service.get_supported_trading_modes()
        return {
            "supported_trading_modes": supported_modes,
            "description": {
                "paper": "Simulated trading with virtual funds",
                "real": "Live trading with real funds via Binance API"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve supported trading modes: {str(e)}"
        )
