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
    ErrorResponse,
)
from src.ultibot_backend.core.domain_models.trading_strategy_models import BaseStrategyType
from src.ultibot_backend.services.strategy_service import StrategyService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService

logger = logging.getLogger(__name__)

router = APIRouter()

# Fixed user ID for v1.0 (single user application)
FIXED_USER_ID = "00000000-0000-0000-0000-000000000001"


def get_persistence_service() -> SupabasePersistenceService:
    """Dependency to get persistence service instance."""
    return SupabasePersistenceService()


def get_strategy_service(
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service)
) -> StrategyService:
    """Dependency to get strategy service instance."""
    return StrategyService(persistence_service)


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
    strategy_service: StrategyService = Depends(get_strategy_service)
) -> TradingStrategyResponse:
    """Create a new trading strategy configuration.
    
    Args:
        strategy_request: The strategy configuration data.
        strategy_service: The strategy service dependency.
        
    Returns:
        The created strategy configuration.
        
    Raises:
        HTTPException: If creation fails or data is invalid.
    """
    try:
        logger.info(f"Creating new strategy: {strategy_request.config_name}")
        
        # Convert request to dict for service
        strategy_data = strategy_request.dict(exclude_unset=True)
        
        # Create strategy through service
        created_strategy = await strategy_service.create_strategy_config(
            user_id=FIXED_USER_ID,
            strategy_data=strategy_data
        )
        
        # Convert to response model
        response = TradingStrategyResponse.from_strategy_config(created_strategy)
        
        logger.info(f"Successfully created strategy {created_strategy.id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions from service
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
    responses={
        200: {"description": "Strategies retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def list_strategies(
    active_only: bool = Query(
        False, 
        description="Return only active strategies"
    ),
    strategy_type: Optional[BaseStrategyType] = Query(
        None, 
        description="Filter by strategy type"
    ),
    strategy_service: StrategyService = Depends(get_strategy_service)
) -> StrategyListResponse:
    """List all trading strategy configurations.
    
    Args:
        active_only: Whether to return only active strategies.
        strategy_type: Optional filter by strategy type.
        strategy_service: The strategy service dependency.
        
    Returns:
        List of strategy configurations.
        
    Raises:
        HTTPException: If retrieval fails.
    """
    logger.debug(f"list_strategies endpoint invoked for user {FIXED_USER_ID}")
    try:
        logger.info(f"Listing strategies for user {FIXED_USER_ID}")
        
        logger.debug("Calling strategy_service.list_strategy_configs...")
        # Get strategies from service
        strategies = await strategy_service.list_strategy_configs(
            user_id=FIXED_USER_ID,
            active_only=active_only,
            strategy_type=strategy_type
        )
        logger.debug(f"strategy_service.list_strategy_configs returned {len(strategies)} strategies.")
        
        # Convert to response models
        strategy_responses = [
            TradingStrategyResponse.from_strategy_config(strategy)
            for strategy in strategies
        ]
        
        response = StrategyListResponse(
            strategies=strategy_responses,
            total_count=len(strategy_responses)
        )
        
        logger.info(f"Retrieved {len(strategies)} strategies")
        logger.debug("list_strategies endpoint finished successfully.")
        return response
        
    except HTTPException as e:
        # Re-raise HTTP exceptions from service
        logger.error(f"HTTPException in list_strategies: {e.detail}")
        raise
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
    description="Retrieve a specific trading strategy configuration by ID",
    responses={
        200: {"description": "Strategy retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Strategy not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def get_strategy(
    strategy_id: str,
    strategy_service: StrategyService = Depends(get_strategy_service)
) -> TradingStrategyResponse:
    """Get a trading strategy configuration by ID.
    
    Args:
        strategy_id: The strategy configuration ID.
        strategy_service: The strategy service dependency.
        
    Returns:
        The strategy configuration.
        
    Raises:
        HTTPException: If strategy not found or retrieval fails.
    """
    try:
        logger.info(f"Getting strategy {strategy_id}")
        
        # Get strategy from service
        strategy = await strategy_service.get_strategy_config(
            strategy_id=strategy_id,
            user_id=FIXED_USER_ID
        )
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Convert to response model
        response = TradingStrategyResponse.from_strategy_config(strategy)
        
        logger.info(f"Retrieved strategy {strategy_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
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
    description="Update a trading strategy configuration",
    responses={
        200: {"description": "Strategy updated successfully"},
        404: {"model": ErrorResponse, "description": "Strategy not found"},
        400: {"model": ErrorResponse, "description": "Invalid strategy data"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def update_strategy(
    strategy_id: str,
    strategy_request: UpdateTradingStrategyRequest,
    strategy_service: StrategyService = Depends(get_strategy_service)
) -> TradingStrategyResponse:
    """Update a trading strategy configuration.
    
    Args:
        strategy_id: The strategy configuration ID.
        strategy_request: The updated strategy data.
        strategy_service: The strategy service dependency.
        
    Returns:
        The updated strategy configuration.
        
    Raises:
        HTTPException: If strategy not found, data invalid, or update fails.
    """
    try:
        logger.info(f"Updating strategy {strategy_id}")
        
        # Convert request to dict for service
        strategy_data = strategy_request.dict(exclude_unset=True)
        
        # Update strategy through service
        updated_strategy = await strategy_service.update_strategy_config(
            strategy_id=strategy_id,
            user_id=FIXED_USER_ID,
            strategy_data=strategy_data
        )
        
        if not updated_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Convert to response model
        response = TradingStrategyResponse.from_strategy_config(updated_strategy)
        
        logger.info(f"Successfully updated strategy {strategy_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions from service
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
    description="Delete a trading strategy configuration",
    responses={
        204: {"description": "Strategy deleted successfully"},
        404: {"model": ErrorResponse, "description": "Strategy not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def delete_strategy(
    strategy_id: str,
    strategy_service: StrategyService = Depends(get_strategy_service)
) -> None:
    """Delete a trading strategy configuration.
    
    Args:
        strategy_id: The strategy configuration ID.
        strategy_service: The strategy service dependency.
        
    Raises:
        HTTPException: If strategy not found or deletion fails.
    """
    try:
        logger.info(f"Deleting strategy {strategy_id}")
        
        # Delete strategy through service
        deleted = await strategy_service.delete_strategy_config(
            strategy_id=strategy_id,
            user_id=FIXED_USER_ID
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        logger.info(f"Successfully deleted strategy {strategy_id}")
        
    except HTTPException:
        # Re-raise HTTP exceptions from service
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
    description="Activate a trading strategy in the specified mode",
    responses={
        200: {"description": "Strategy activated successfully"},
        404: {"model": ErrorResponse, "description": "Strategy not found"},
        400: {"model": ErrorResponse, "description": "Invalid mode"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def activate_strategy(
    strategy_id: str,
    activation_request: ActivateStrategyRequest,
    strategy_service: StrategyService = Depends(get_strategy_service)
) -> StrategyActivationResponse:
    """Activate a trading strategy in the specified mode.
    
    Args:
        strategy_id: The strategy configuration ID.
        activation_request: The activation request with mode.
        strategy_service: The strategy service dependency.
        
    Returns:
        Strategy activation response.
        
    Raises:
        HTTPException: If strategy not found, mode invalid, or activation fails.
    """
    try:
        logger.info(f"Activating strategy {strategy_id} in {activation_request.mode} mode")
        
        # Activate strategy through service
        updated_strategy = await strategy_service.activate_strategy(
            strategy_id=strategy_id,
            user_id=FIXED_USER_ID,
            mode=activation_request.mode
        )
        
        if not updated_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Determine new activation status
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
        # Re-raise HTTP exceptions from service
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
    description="Deactivate a trading strategy in the specified mode",
    responses={
        200: {"description": "Strategy deactivated successfully"},
        404: {"model": ErrorResponse, "description": "Strategy not found"},
        400: {"model": ErrorResponse, "description": "Invalid mode"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def deactivate_strategy(
    strategy_id: str,
    deactivation_request: ActivateStrategyRequest,
    strategy_service: StrategyService = Depends(get_strategy_service)
) -> StrategyActivationResponse:
    """Deactivate a trading strategy in the specified mode.
    
    Args:
        strategy_id: The strategy configuration ID.
        deactivation_request: The deactivation request with mode.
        strategy_service: The strategy service dependency.
        
    Returns:
        Strategy deactivation response.
        
    Raises:
        HTTPException: If strategy not found, mode invalid, or deactivation fails.
    """
    try:
        logger.info(f"Deactivating strategy {strategy_id} in {deactivation_request.mode} mode")
        
        # Deactivate strategy through service
        updated_strategy = await strategy_service.deactivate_strategy(
            strategy_id=strategy_id,
            user_id=FIXED_USER_ID,
            mode=deactivation_request.mode
        )
        
        if not updated_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Determine new activation status
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
        # Re-raise HTTP exceptions from service
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
    description="Get all active strategies for a specific trading mode",
    responses={
        200: {"description": "Active strategies retrieved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid mode"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def get_active_strategies_by_mode(
    mode: str,
    strategy_service: StrategyService = Depends(get_strategy_service)
) -> StrategyListResponse:
    """Get all active strategies for a specific trading mode.
    
    Args:
        mode: The trading mode ("paper" or "real").
        strategy_service: The strategy service dependency.
        
    Returns:
        List of active strategy configurations.
        
    Raises:
        HTTPException: If mode invalid or retrieval fails.
    """
    try:
        logger.info(f"Getting active {mode} strategies for user {FIXED_USER_ID}")
        
        # Get active strategies from service
        strategies = await strategy_service.get_active_strategies(
            user_id=FIXED_USER_ID,
            mode=mode
        )
        
        # Convert to response models
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
        # Re-raise HTTP exceptions from service
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting active {mode} strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active {mode} strategies"
        )
