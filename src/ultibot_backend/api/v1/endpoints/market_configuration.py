"""
Endpoints de la API para la configuración y ejecución de escaneos de mercado.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from ...services.market_scan_service import MarketScanService
from ...dependencies import MarketScanServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market-configuration", tags=["Market Configuration"])

@router.post("/scan/execute/{preset_name}", response_model=List[Dict[str, Any]])
async def execute_market_scan(
    preset_name: str,
    market_scanner = MarketScanServiceDep,
):
    """
    Ejecuta un escaneo de mercado utilizando un preset de configuración específico.
    """
    try:
        logger.info(f"Ejecutando escaneo de mercado con el preset: {preset_name}")
        # Use scan_with_preset method with user_id (for now use default)
        results = await market_scanner.scan_with_preset(preset_name, user_id="default_user")
        if not results:
            logger.warning(f"El escaneo con el preset '{preset_name}' no arrojó resultados.")
        return results
    except ValueError as e:
        logger.error(f"Error al ejecutar el escaneo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error inesperado durante el escaneo de mercado: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocurrió un error inesperado al procesar el escaneo: {str(e)}"
        )

@router.get("/scan/presets", response_model=List[Dict[str, Any]])
async def get_scan_presets(
    market_scanner = MarketScanServiceDep,
):
    """
    Obtiene la lista de todos los presets de escaneo de mercado disponibles.
    """
    try:
        logger.info("Obteniendo la lista de presets de escaneo de mercado.")
        # Get system presets and user presets
        system_presets = await market_scanner.get_system_presets()
        user_presets = await market_scanner.list_scan_presets(user_id="default_user")
        
        # Convert to dict format for response
        all_presets = []
        for preset in system_presets + user_presets:
            preset_dict = {
                "id": preset.id,
                "name": preset.name,
                "description": preset.description,
                "category": preset.category,
                "is_system_preset": getattr(preset, 'is_system_preset', False),
                "recommended_strategies": getattr(preset, 'recommended_strategies', [])
            }
            all_presets.append(preset_dict)
        
        return all_presets
    except Exception as e:
        logger.error(f"Error inesperado al obtener los presets de escaneo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocurrió un error inesperado al obtener los presets: {str(e)}"
        )
