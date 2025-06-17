"""API endpoints for trading strategy management."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from uuid import UUID

from ultibot_backend.api.v1.models.strategy_models import (
    CreateTradingStrategyRequest,
    UpdateTradingStrategyRequest,
    TradingStrategyResponse,
    StrategyListResponse,
    ActivateStrategyRequest,
    StrategyActivationResponse,
    ErrorResponse,
)
from ultibot_backend.core.domain_models.trading_strategy_models import BaseStrategyType
from ultibot_backend.services.strategy_service import StrategyService
from ultibot_backend import dependencies as deps
from ultibot_backend.app_config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/strategies",
    response_model=TradingStrategyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new trading strategy",
    description="Create a new trading strategy configuration",
    responses={
        201: {"description": "Strategy created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid strategy data"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def create_strategy(
    strategy_request: CreateTradingStrategyRequest,
    request: Request,
    strategy_service: StrategyService = Depends(deps.get_strategy_service)
) -> TradingStrategyResponse:
    """Create a new trading strategy configuration for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Creating new strategy: {strategy_request.config_name} for user {user_id}")
        strategy_data = strategy_request.dict(exclude_unset=True)
        created_strategy = await strategy_service.create_strategy_config(
            user_id=str(user_id),
            strategy_data=strategy_data
        )
        response = TradingStrategyResponse.from_strategy_config(created_strategy)
        logger.info(f"Successfully created strategy {created_strategy.id}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create strategy configuration"
        )

@router.get(
    "/strategies",
    response_model=StrategyListResponse,
    summary="List trading strategies",
    description="Get all trading strategy configurations for the user",
)
async def list_strategies(
    request: Request,
    strategy_service: StrategyService = Depends(deps.get_strategy_service)
) -> StrategyListResponse:
    """List all trading strategy configurations for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Listing strategies for user {user_id}")
        strategies = await strategy_service.list_strategy_configs(
            user_id=str(user_id)
        )
        strategy_responses = [
            TradingStrategyResponse.from_strategy_config(strategy)
            for strategy in strategies
        ]
        response = StrategyListResponse(
            strategies=strategy_responses,
            total_count=len(strategy_responses)
        )
        logger.info(f"Retrieved {len(strategies)} strategies")
        return response
    except Exception as e:
        logger.error(f"Unexpected error listing strategies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve strategy configurations"
        )

@router.get(
    "/strategies/{strategy_id}",
    response_model=TradingStrategyResponse,
    summary="Get trading strategy by ID",
)
async def get_strategy(
    strategy_id: str,
    request: Request,
    strategy_service: StrategyService = Depends(deps.get_strategy_service)
) -> TradingStrategyResponse:
    """Get a trading strategy configuration by ID for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Getting strategy {strategy_id} for user {user_id}")
        strategy = await strategy_service.get_strategy_config(
            strategy_id=strategy_id,
            user_id=str(user_id)
        )
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        response = TradingStrategyResponse.from_strategy_config(strategy)
        logger.info(f"Retrieved strategy {strategy_id}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve strategy configuration"
        )

@router.put(
    "/strategies/{strategy_id}",
    response_model=TradingStrategyResponse,
    summary="Update trading strategy",
)
async def update_strategy(
    strategy_id: str,
    strategy_request: UpdateTradingStrategyRequest,
    request: Request,
    strategy_service: StrategyService = Depends(deps.get_strategy_service)
) -> TradingStrategyResponse:
    """Update a trading strategy configuration for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Updating strategy {strategy_id} for user {user_id}")
        strategy_data = strategy_request.dict(exclude_unset=True)
        updated_strategy = await strategy_service.update_strategy_config(
            strategy_id=strategy_id,
            user_id=str(user_id),
            strategy_data=strategy_data
        )
        if not updated_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        response = TradingStrategyResponse.from_strategy_config(updated_strategy)
        logger.info(f"Successfully updated strategy {strategy_id}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update strategy configuration"
        )

@router.delete(
    "/strategies/{strategy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete trading strategy",
)
async def delete_strategy(
    strategy_id: str,
    request: Request,
    strategy_service: StrategyService = Depends(deps.get_strategy_service)
) -> None:
    """Delete a trading strategy configuration for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Deleting strategy {strategy_id} for user {user_id}")
        deleted = await strategy_service.delete_strategy_config(
            strategy_id=strategy_id,
            user_id=str(user_id)
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        logger.info(f"Successfully deleted strategy {strategy_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete strategy configuration"
        )

@router.patch(
    "/strategies/{strategy_id}/activate",
    response_model=StrategyActivationResponse,
    summary="Activate trading strategy",
)
async def activate_strategy(
    strategy_id: str,
    activation_request: ActivateStrategyRequest,
    request: Request,
    strategy_service: StrategyService = Depends(deps.get_strategy_service)
) -> StrategyActivationResponse:
    """Activate a trading strategy in the specified mode for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Activating strategy {strategy_id} in {activation_request.mode} mode for user {user_id}")
        updated_strategy = await strategy_service.activate_strategy(
            strategy_id=strategy_id,
            user_id=str(user_id),
            mode=activation_request.mode
        )
        if not updated_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        is_active = (
            updated_strategy.is_active_paper_mode 
            if activation_request.mode == "paper" 
            else updated_strategy.is_active_real_mode
        )
        response = StrategyActivationResponse(
            strategy_id=strategy_id,
            mode=activation_request.mode,
            is_active=is_active,
            message=f"Strategy activated in {activation_request.mode} mode"
        )
        logger.info(f"Successfully activated strategy {strategy_id} in {activation_request.mode} mode")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error activating strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate strategy in {activation_request.mode} mode"
        )

@router.patch(
    "/strategies/{strategy_id}/deactivate",
    response_model=StrategyActivationResponse,
    summary="Deactivate trading strategy",
)
async def deactivate_strategy(
    strategy_id: str,
    deactivation_request: ActivateStrategyRequest,
    request: Request,
    strategy_service: StrategyService = Depends(deps.get_strategy_service)
) -> StrategyActivationResponse:
    """Deactivate a trading strategy in the specified mode for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Deactivating strategy {strategy_id} in {deactivation_request.mode} mode for user {user_id}")
        updated_strategy = await strategy_service.deactivate_strategy(
            strategy_id=strategy_id,
            user_id=str(user_id),
            mode=deactivation_request.mode
        )
        if not updated_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        is_active = (
            updated_strategy.is_active_paper_mode 
            if deactivation_request.mode == "paper" 
            else updated_strategy.is_active_real_mode
        )
        response = StrategyActivationResponse(
            strategy_id=strategy_id,
            mode=deactivation_request.mode,
            is_active=is_active,
            message=f"Strategy deactivated in {deactivation_request.mode} mode"
        )
        logger.info(f"Successfully deactivated strategy {strategy_id} in {deactivation_request.mode} mode")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deactivating strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate strategy in {deactivation_request.mode} mode"
        )

@router.get(
    "/strategies/active/{mode}",
    response_model=StrategyListResponse,
    summary="Get active strategies by mode",
)
async def get_active_strategies_by_mode(
    mode: str,
    request: Request,
    strategy_service: StrategyService = Depends(deps.get_strategy_service)
) -> StrategyListResponse:
    """Get all active strategies for a specific trading mode for the fixed user."""
    user_id = settings.FIXED_USER_ID
    try:
        logger.info(f"Getting active {mode} strategies for user {user_id}")
        strategies = await strategy_service.get_active_strategies(
            user_id=str(user_id),
            mode=mode
        )
        strategy_responses = [
            TradingStrategyResponse.from_strategy_config(strategy)
            for strategy in strategies
        ]
        response = StrategyListResponse(
            strategies=strategy_responses,
            total_count=len(strategy_responses)
        )
        logger.info(f"Retrieved {len(strategies)} active {mode} strategies")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting active {mode} strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active {mode} strategies"
        )

