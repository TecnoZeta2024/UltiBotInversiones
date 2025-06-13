"""API endpoints for trading strategy management."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID

from src.ultibot_backend.api.v1.models.strategy_models import (
    CreateTradingStrategyRequest,
    UpdateTradingStrategyRequest,
    TradingStrategyResponse,
    StrategyListResponse,
    ActivateStrategyRequest,
    StrategyActivationResponse,
)
from src.ultibot_backend.dependencies import TradingEngineDep
from src.ultibot_backend.app_config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategies", tags=["Strategies"])

@router.post(
    "/",
    response_model=TradingStrategyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new trading strategy",
)
async def create_strategy(
    strategy_request: CreateTradingStrategyRequest,
    trading_engine = TradingEngineDep,
) -> TradingStrategyResponse:
    """Create a new trading strategy configuration for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Creating new strategy: {strategy_request.config_name} for user {user_id}")
        strategy_data = strategy_request.model_dump(exclude_unset=True)
        created_strategy = await trading_engine.create_strategy(
            user_id=str(user_id),
            strategy_data=strategy_data
        )
        return TradingStrategyResponse.model_validate(created_strategy)
    except Exception as e:
        logger.error(f"Unexpected error creating strategy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create strategy configuration"
        )

@router.get(
    "/",
    response_model=StrategyListResponse,
    summary="List trading strategies",
)
async def list_strategies(
    trading_engine = TradingEngineDep,
) -> StrategyListResponse:
    """List all trading strategy configurations for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Listing strategies for user {user_id}")
        strategies = await trading_engine.get_strategies_by_user(user_id=str(user_id))
        strategy_responses = [
            TradingStrategyResponse.model_validate(strategy)
            for strategy in strategies
        ]
        return StrategyListResponse(
            strategies=strategy_responses,
            total_count=len(strategy_responses)
        )
    except Exception as e:
        logger.error(f"Unexpected error listing strategies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve strategy configurations"
        )

@router.get(
    "/{strategy_id}",
    response_model=TradingStrategyResponse,
    summary="Get trading strategy by ID",
)
async def get_strategy(
    strategy_id: str,
    trading_engine = TradingEngineDep,
) -> TradingStrategyResponse:
    """Get a trading strategy configuration by ID for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Getting strategy {strategy_id} for user {user_id}")
        strategy = await trading_engine.get_strategy(strategy_id=strategy_id, user_id=str(user_id))
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        return TradingStrategyResponse.model_validate(strategy)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting strategy {strategy_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve strategy configuration"
        )

@router.put(
    "/{strategy_id}",
    response_model=TradingStrategyResponse,
    summary="Update trading strategy",
)
async def update_strategy(
    strategy_id: str,
    strategy_request: UpdateTradingStrategyRequest,
    trading_engine = TradingEngineDep,
) -> TradingStrategyResponse:
    """Update a trading strategy configuration for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Updating strategy {strategy_id} for user {user_id}")
        strategy_data = strategy_request.model_dump(exclude_unset=True)
        updated_strategy = await trading_engine.update_strategy(
            strategy_id=strategy_id,
            user_id=str(user_id),
            strategy_data=strategy_data
        )
        return TradingStrategyResponse.model_validate(updated_strategy)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating strategy {strategy_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update strategy configuration"
        )

@router.delete(
    "/{strategy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete trading strategy",
)
async def delete_strategy(
    strategy_id: str,
    trading_engine = TradingEngineDep,
) -> None:
    """Delete a trading strategy configuration for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Deleting strategy {strategy_id} for user {user_id}")
        await trading_engine.delete_strategy(strategy_id=strategy_id, user_id=str(user_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting strategy {strategy_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete strategy configuration"
        )

@router.patch(
    "/{strategy_id}/activate",
    response_model=StrategyActivationResponse,
    summary="Activate trading strategy",
)
async def activate_strategy(
    strategy_id: str,
    activation_request: ActivateStrategyRequest,
    trading_engine = TradingEngineDep,
) -> StrategyActivationResponse:
    """Activate a trading strategy in the specified mode for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Activating strategy {strategy_id} in {activation_request.mode} mode for user {user_id}")
        updated_strategy = await trading_engine.set_strategy_activation(
            strategy_id=strategy_id,
            user_id=str(user_id),
            mode=activation_request.mode,
            is_active=True
        )
        return StrategyActivationResponse(
            strategy_id=updated_strategy.id,
            mode=activation_request.mode,
            is_active=True,
            message=f"Strategy activated in {activation_request.mode} mode"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error activating strategy {strategy_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate strategy in {activation_request.mode} mode"
        )

@router.patch(
    "/{strategy_id}/deactivate",
    response_model=StrategyActivationResponse,
    summary="Deactivate trading strategy",
)
async def deactivate_strategy(
    strategy_id: str,
    deactivation_request: ActivateStrategyRequest,
    trading_engine = TradingEngineDep,
) -> StrategyActivationResponse:
    """Deactivate a trading strategy in the specified mode for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Deactivating strategy {strategy_id} in {deactivation_request.mode} mode for user {user_id}")
        updated_strategy = await trading_engine.set_strategy_activation(
            strategy_id=strategy_id,
            user_id=str(user_id),
            mode=deactivation_request.mode,
            is_active=False
        )
        return StrategyActivationResponse(
            strategy_id=updated_strategy.id,
            mode=deactivation_request.mode,
            is_active=False,
            message=f"Strategy deactivated in {deactivation_request.mode} mode"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deactivating strategy {strategy_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate strategy in {deactivation_request.mode} mode"
        )
