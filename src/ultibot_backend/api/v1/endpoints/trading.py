from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import Annotated

from src.shared.data_types import ConfirmRealTradeRequest, OpportunityStatus, Opportunity
from src.ultibot_backend.services.trading_engine_service import TradingEngineService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService

router = APIRouter()

@router.post("/real/confirm-opportunity/{opportunity_id}", status_code=status.HTTP_200_OK)
async def confirm_real_opportunity(
    opportunity_id: UUID,
    request: ConfirmRealTradeRequest,
    trading_engine_service: Annotated[TradingEngineService, Depends(TradingEngineService)],
    config_service: Annotated[ConfigService, Depends(ConfigService)],
    persistence_service: Annotated[SupabasePersistenceService, Depends(SupabasePersistenceService)]
):
    """
    Endpoint para que el usuario confirme explícitamente una oportunidad de trading real.
    """
    if opportunity_id != request.opportunity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Opportunity ID in path and request body do not match."
        )

    # 1. Validar que la oportunidad existe y está en el estado correcto
    opportunity = await persistence_service.get_opportunity_by_id(opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity with ID {opportunity_id} not found."
        )

    if opportunity.status != OpportunityStatus.PENDING_USER_CONFIRMATION_REAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Opportunity {opportunity_id} is not in 'pending_user_confirmation_real' status. Current status: {opportunity.status.value}"
        )
    
    # 2. Validar que el modo de operativa real limitada está activo y hay cupos disponibles
    user_config = await config_service.get_user_configuration(request.user_id)
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

    # 3. Si las validaciones son exitosas, llamar al TradingEngineService para iniciar la ejecución
    try:
        await trading_engine_service.execute_real_trade(opportunity_id, request.user_id)
        return {"message": "Real trade execution initiated successfully."}
    except Exception as e:
        # Aquí se podría añadir un logging más detallado del error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate real trade execution: {str(e)}"
        )
