"""Market Configuration API Endpoints.

This module provides REST API endpoints for managing market scan configurations,
presets, and asset trading parameters.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ....core.domain_models.user_configuration_models import (
    MarketScanConfiguration,
    ScanPreset,
    AssetTradingParameters
)
from ....services.market_scan_service import MarketScanService
from ....dependencies import (
    get_market_scan_service,
    get_current_user_id
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market-configuration", tags=["market-configuration"])

@router.post("/scan/execute", response_model=List[Dict[str, Any]])
async def execute_market_scan(
    scan_config: MarketScanConfiguration,
    market_scan_service: MarketScanService = Depends(get_market_scan_service),
    user_id: str = Depends(get_current_user_id)
):
    """Execute a market scan with specified configuration.
    
    Args:
        scan_config: Market scan configuration to execute.
        market_scan_service: Injected market scan service.
        user_id: Current user identifier.
        
    Returns:
        List of market opportunities matching the scan criteria.
        
    Raises:
        HTTPException: If scan execution fails.
    """
    try:
        logger.info(f"Executing market scan for user {user_id}")
        
        results = await market_scan_service.scan_market_with_config(scan_config, user_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": results,
                "scan_config": scan_config.dict(),
                "total_results": len(results)
            }
        )
        
    except Exception as e:
        logger.error(f"Market scan execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Market scan failed: {str(e)}"
        )

@router.post("/configurations", response_model=MarketScanConfiguration)
async def create_market_scan_configuration(
    config: MarketScanConfiguration,
    market_scan_service: MarketScanService = Depends(get_market_scan_service),
    user_id: str = Depends(get_current_user_id)
):
    """Create a new market scan configuration.
    
    Args:
        config: Market scan configuration to create.
        market_scan_service: Injected market scan service.
        user_id: Current user identifier.
        
    Returns:
        Created market scan configuration with generated ID and timestamps.
        
    Raises:
        HTTPException: If creation fails.
    """
    try:
        logger.info(f"Creating market scan configuration '{config.name}' for user {user_id}")
        
        created_config = await market_scan_service.create_market_scan_configuration(config, user_id)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "data": created_config.dict(),
                "message": f"Market scan configuration '{created_config.name}' created successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create market scan configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create configuration: {str(e)}"
        )

@router.post("/scan/preset/{preset_id}/execute", response_model=List[Dict[str, Any]])
async def execute_preset_scan(
    preset_id: str,
    market_scan_service: MarketScanService = Depends(get_market_scan_service),
    user_id: str = Depends(get_current_user_id)
):
    """Execute a market scan using a preset configuration.
    
    Args:
        preset_id: ID of the preset to execute.
        market_scan_service: Injected market scan service.
        user_id: Current user identifier.
        
    Returns:
        List of market opportunities.
        
    Raises:
        HTTPException: If preset not found or scan fails.
    """
    try:
        logger.info(f"Executing preset scan '{preset_id}' for user {user_id}")
        
        results = await market_scan_service.scan_with_preset(preset_id, user_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": results,
                "preset_id": preset_id,
                "total_results": len(results)
            }
        )
        
    except ValueError as e:
        logger.warning(f"Preset not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Preset scan execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preset scan failed: {str(e)}"
        )

@router.get("/presets", response_model=List[ScanPreset])
async def list_scan_presets(
    include_system: bool = True,
    market_scan_service: MarketScanService = Depends(get_market_scan_service),
    user_id: str = Depends(get_current_user_id)
):
    """List all scan presets for the current user.
    
    Args:
        include_system: Whether to include system presets.
        market_scan_service: Injected market scan service.
        user_id: Current user identifier.
        
    Returns:
        List of scan presets.
    """
    try:
        logger.info(f"Listing scan presets for user {user_id}")
        
        # Get user presets
        user_presets = await market_scan_service.list_scan_presets(user_id)
        
        # Get system presets if requested
        all_presets = user_presets
        if include_system:
            system_presets = await market_scan_service.get_system_presets()
            all_presets.extend(system_presets)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": [preset.dict() for preset in all_presets],
                "total_count": len(all_presets),
                "user_presets_count": len(user_presets),
                "system_presets_count": len(all_presets) - len(user_presets)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to list scan presets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve presets: {str(e)}"
        )

@router.post("/presets", response_model=ScanPreset)
async def create_scan_preset(
    preset: ScanPreset,
    market_scan_service: MarketScanService = Depends(get_market_scan_service),
    user_id: str = Depends(get_current_user_id)
):
    """Create a new scan preset.
    
    Args:
        preset: Scan preset to create.
        market_scan_service: Injected market scan service.
        user_id: Current user identifier.
        
    Returns:
        Created scan preset with generated ID and timestamps.
        
    Raises:
        HTTPException: If creation fails.
    """
    try:
        logger.info(f"Creating scan preset '{preset.name}' for user {user_id}")
        
        # Ensure it's not marked as system preset
        preset.is_system_preset = False
        
        created_preset = await market_scan_service.create_scan_preset(preset, user_id)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "data": created_preset.dict(),
                "message": f"Scan preset '{created_preset.name}' created successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create scan preset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create preset: {str(e)}"
        )

@router.get("/presets/{preset_id}", response_model=ScanPreset)
async def get_scan_preset(
    preset_id: str,
    market_scan_service: MarketScanService = Depends(get_market_scan_service),
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific scan preset by ID.
    
    Args:
        preset_id: ID of the preset to retrieve.
        market_scan_service: Injected market scan service.
        user_id: Current user identifier.
        
    Returns:
        The requested scan preset.
        
    Raises:
        HTTPException: If preset not found.
    """
    try:
        logger.info(f"Getting scan preset '{preset_id}' for user {user_id}")
        
        preset = await market_scan_service.get_scan_preset(preset_id, user_id)
        
        if not preset:
            # Check system presets
            system_presets = await market_scan_service.get_system_presets()
            preset = next((p for p in system_presets if p.id == preset_id), None)
        
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan preset '{preset_id}' not found"
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": preset.dict()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan preset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve preset: {str(e)}"
        )

@router.put("/presets/{preset_id}", response_model=ScanPreset)
async def update_scan_preset(
    preset_id: str,
    preset: ScanPreset,
    market_scan_service: MarketScanService = Depends(get_market_scan_service),
    user_id: str = Depends(get_current_user_id)
):
    """Update an existing scan preset.
    
    Args:
        preset_id: ID of the preset to update.
        preset: Updated preset data.
        market_scan_service: Injected market scan service.
        user_id: Current user identifier.
        
    Returns:
        Updated scan preset.
        
    Raises:
        HTTPException: If preset not found or update fails.
    """
    try:
        logger.info(f"Updating scan preset '{preset_id}' for user {user_id}")
        
        # Ensure the ID matches
        preset.id = preset_id
        
        # Ensure it's not marked as system preset
        preset.is_system_preset = False
        
        updated_preset = await market_scan_service.update_scan_preset(preset, user_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": updated_preset.dict(),
                "message": f"Scan preset '{updated_preset.name}' updated successfully"
            }
        )
        
    except ValueError as e:
        logger.warning(f"Preset not found for update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update scan preset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preset: {str(e)}"
        )

@router.delete("/presets/{preset_id}")
async def delete_scan_preset(
    preset_id: str,
    market_scan_service: MarketScanService = Depends(get_market_scan_service),
    user_id: str = Depends(get_current_user_id)
):
    """Delete a scan preset.
    
    Args:
        preset_id: ID of the preset to delete.
        market_scan_service: Injected market scan service.
        user_id: Current user identifier.
        
    Returns:
        Success confirmation.
        
    Raises:
        HTTPException: If preset not found or deletion fails.
    """
    try:
        logger.info(f"Deleting scan preset '{preset_id}' for user {user_id}")
        
        success = await market_scan_service.delete_scan_preset(preset_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan preset '{preset_id}' not found"
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"Scan preset '{preset_id}' deleted successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete scan preset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete preset: {str(e)}"
        )

@router.get("/system-presets", response_model=List[ScanPreset])
async def get_system_presets(
    market_scan_service: MarketScanService = Depends(get_market_scan_service)
):
    """Get system-provided scan presets.
    
    Args:
        market_scan_service: Injected market scan service.
        
    Returns:
        List of system scan presets.
    """
    try:
        logger.info("Getting system scan presets")
        
        system_presets = await market_scan_service.get_system_presets()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": [preset.dict() for preset in system_presets],
                "total_count": len(system_presets)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get system presets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system presets: {str(e)}"
        )

# Asset Trading Parameters Endpoints

@router.get("/asset-parameters", response_model=List[AssetTradingParameters])
async def list_asset_trading_parameters(
    user_id: str = Depends(get_current_user_id)
):
    """List all asset trading parameters for the current user.
    
    Args:
        user_id: Current user identifier.
        
    Returns:
        List of asset trading parameters.
    """
    try:
        logger.info(f"Listing asset trading parameters for user {user_id}")
        
        # This would be implemented with the persistence service
        # For now, return empty list as placeholder
        parameters = []
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": [param.dict() for param in parameters],
                "total_count": len(parameters)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to list asset trading parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve asset parameters: {str(e)}"
        )

@router.post("/asset-parameters", response_model=AssetTradingParameters)
async def create_asset_trading_parameters(
    parameters: AssetTradingParameters,
    user_id: str = Depends(get_current_user_id)
):
    """Create new asset trading parameters.
    
    Args:
        parameters: Asset trading parameters to create.
        user_id: Current user identifier.
        
    Returns:
        Created asset trading parameters.
    """
    try:
        logger.info(f"Creating asset trading parameters '{parameters.name}' for user {user_id}")
        
        # This would be implemented with the persistence service
        # For now, return the parameters as-is with generated ID
        if not parameters.id:
            from uuid import uuid4
            parameters.id = str(uuid4())
        
        from datetime import datetime
        parameters.created_at = datetime.utcnow()
        parameters.updated_at = parameters.created_at
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "data": parameters.dict(),
                "message": f"Asset trading parameters '{parameters.name}' created successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create asset trading parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create asset parameters: {str(e)}"
        )

@router.get("/asset-parameters/{parameter_id}", response_model=AssetTradingParameters)
async def get_asset_trading_parameters(
    parameter_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get specific asset trading parameters by ID.
    
    Args:
        parameter_id: ID of the parameters to retrieve.
        user_id: Current user identifier.
        
    Returns:
        The requested asset trading parameters.
        
    Raises:
        HTTPException: If parameters not found.
    """
    try:
        logger.info(f"Getting asset trading parameters '{parameter_id}' for user {user_id}")
        
        # This would be implemented with the persistence service
        # For now, return 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset trading parameters '{parameter_id}' not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get asset trading parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve asset parameters: {str(e)}"
        )

@router.put("/asset-parameters/{parameter_id}", response_model=AssetTradingParameters)
async def update_asset_trading_parameters(
    parameter_id: str,
    parameters: AssetTradingParameters,
    user_id: str = Depends(get_current_user_id)
):
    """Update existing asset trading parameters.
    
    Args:
        parameter_id: ID of the parameters to update.
        parameters: Updated parameters data.
        user_id: Current user identifier.
        
    Returns:
        Updated asset trading parameters.
        
    Raises:
        HTTPException: If parameters not found.
    """
    try:
        logger.info(f"Updating asset trading parameters '{parameter_id}' for user {user_id}")
        
        # Ensure the ID matches
        parameters.id = parameter_id
        
        # This would be implemented with the persistence service
        # For now, return the parameters with updated timestamp
        from datetime import datetime
        parameters.updated_at = datetime.utcnow()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": parameters.dict(),
                "message": f"Asset trading parameters '{parameters.name}' updated successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to update asset trading parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update asset parameters: {str(e)}"
        )

@router.delete("/asset-parameters/{parameter_id}")
async def delete_asset_trading_parameters(
    parameter_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete asset trading parameters.
    
    Args:
        parameter_id: ID of the parameters to delete.
        user_id: Current user identifier.
        
    Returns:
        Success confirmation.
        
    Raises:
        HTTPException: If parameters not found.
    """
    try:
        logger.info(f"Deleting asset trading parameters '{parameter_id}' for user {user_id}")
        
        # This would be implemented with the persistence service
        # For now, return success
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"Asset trading parameters '{parameter_id}' deleted successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to delete asset trading parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete asset parameters: {str(e)}"
        )
