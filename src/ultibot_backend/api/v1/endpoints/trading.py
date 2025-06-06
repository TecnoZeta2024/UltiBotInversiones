from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field

from src.shared.data_types import ConfirmRealTradeRequest, OpportunityStatus, Opportunity, TradeOrderDetails
from src.ultibot_backend.services.trading_engine_service import TradingEngine
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.unified_order_execution_service import UnifiedOrderExecutionService
from src.ultibot_backend import dependencies as deps
from src.ultibot_backend.security import core as security_core
from src.ultibot_backend.security import schemas as security_schemas

router = APIRouter()

@router.post("/real/confirm-opportunity/{opportunity_id}", status_code=status.HTTP_200_OK)
async def confirm_real_opportunity(
    opportunity_id: UUID,
    request: ConfirmRealTradeRequest,
    trading_engine_service: Annotated[TradingEngine, Depends(deps.get_trading_engine_service)],
    config_service: Annotated[ConfigService, Depends(deps.get_config_service)],
    persistence_service: Annotated[SupabasePersistenceService, Depends(deps.get_persistence_service)],
    current_user: security_schemas.User = Depends(security_core.get_current_active_user)
):
    """
    Endpoint para que el usuario autenticado confirme explícitamente una oportunidad de trading real.
    """
    if not isinstance(current_user.id, UUID):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")

    if opportunity_id != request.opportunity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Opportunity ID in path and request body do not match."
        )
    
    if current_user.id != request.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID in token does not match user ID in request body."
        )

    # 1. Validar que la oportunidad existe y está en el estado correcto
    opportunity = await persistence_service.get_opportunity_by_id(opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with ID {opportunity_id} not found."
        )

    # Verificar que la oportunidad pertenece al usuario autenticado
    if opportunity.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized to confirm this opportunity."
        )

    if opportunity.status != OpportunityStatus.PENDING_USER_CONFIRMATION_REAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Opportunity {opportunity_id} is not in 'pending_user_confirmation_real' status. Current status: {opportunity.status.value}"
        )
    
    # 2. Validar que el modo de operativa real limitada está activo y hay cupos disponibles
    user_config = await config_service.get_user_configuration(str(current_user.id))
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

    # 3. Si las validaciones son exitosas, simplemente retorna éxito (placeholder real)
    return {"message": "Real trade execution confirmed (placeholder, implement logic)."}

# Trading mode type alias
TradingMode = Literal["paper", "real"]

class MarketOrderRequest(BaseModel):
    """Request model for market order execution."""
    user_id: UUID = Field(..., description="User identifier")
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTCUSDT')")
    side: str = Field(..., description="Order side ('BUY' or 'SELL')")
    quantity: float = Field(..., gt=0, description="Order quantity (must be positive)")
    trading_mode: TradingMode = Field(..., description="Trading mode ('paper' or 'real')")
    api_key: Optional[str] = Field(None, description="API key for real trading (required for real mode)")
    api_secret: Optional[str] = Field(None, description="API secret for real trading (required for real mode)")

@router.post("/market-order", response_model=TradeOrderDetails, status_code=status.HTTP_200_OK)
async def execute_market_order(
    request: MarketOrderRequest,
    unified_execution_service: Annotated[UnifiedOrderExecutionService, Depends(deps.get_unified_order_execution_service)],
    current_user: security_schemas.User = Depends(security_core.get_current_active_user)
):
    """
    Execute a market order in the specified trading mode for the authenticated user.
    
    This endpoint allows execution of market orders in either paper trading or real trading mode.
    For real trading, API credentials must be provided in the request.
    """
    try:
        # Validate trading mode
        if not unified_execution_service.validate_trading_mode(request.trading_mode):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid trading mode: {request.trading_mode}. Must be 'paper' or 'real'"
            )

        if current_user.id != request.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User ID in token does not match user ID in request body."
            )
        
        # Ensure current_user.id is a UUID before passing it
        if not isinstance(current_user.id, UUID):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authenticated user ID is not a valid UUID."
            )
        
        # Execute the order
        order_details = await unified_execution_service.execute_market_order(
            user_id=current_user.id, # Use authenticated user's ID
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            trading_mode=request.trading_mode,
            api_key=request.api_key,
            api_secret=request.api_secret
        )
        
        return order_details
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute market order: {str(e)}"
        )

@router.get("/paper-balances", status_code=status.HTTP_200_OK) # Path parameter user_id removed
async def get_paper_trading_balances(
    unified_execution_service: Annotated[UnifiedOrderExecutionService, Depends(deps.get_unified_order_execution_service)],
    current_user: security_schemas.User = Depends(security_core.get_current_active_user) # Added current_user
):
    """
    Get current virtual balances for paper trading for the authenticated user.
    
    Returns the current virtual balances maintained by the paper trading service.
    """
    try:
        if not isinstance(current_user.id, UUID): # Added check for current_user.id
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")

        balances = await unified_execution_service.get_virtual_balances() # This service might need user_id in the future
        return {
            "user_id": current_user.id, # Use current_user.id
            "trading_mode": "paper",
            "balances": balances
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve paper trading balances: {str(e)}"
        )

@router.post("/paper-balances/reset", status_code=status.HTTP_200_OK) # Path parameter user_id removed
async def reset_paper_trading_balances(
    unified_execution_service: Annotated[UnifiedOrderExecutionService, Depends(deps.get_unified_order_execution_service)],
    current_user: security_schemas.User = Depends(security_core.get_current_active_user), # Added current_user
    initial_capital: float = Query(..., gt=0, description="Initial capital amount (must be positive)")
):
    """
    Reset paper trading balances to initial capital for the authenticated user.
    
    This endpoint allows resetting the virtual balances for paper trading to a new initial capital amount.
    """
    try:
        if not isinstance(current_user.id, UUID): # Added check for current_user.id
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")

        unified_execution_service.reset_virtual_balances(initial_capital) # This service might need user_id in the future
        return {
            "user_id": current_user.id, # Use current_user.id
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
    
    Returns the available trading modes supported by the system.
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
