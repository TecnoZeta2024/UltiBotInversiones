"""
Servicio para interactuar con la API del backend de UltiBotInversiones.
"""

import logging
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Excepción personalizada para errores de API."""
    pass

class UltiBotAPIClient:
    """
    Cliente para interactuar con la API REST del backend de UltiBotInversiones.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Inicializa el cliente API.
        
        Args:
            base_url: URL base del backend API
        """
        self.base_url = base_url
        self.timeout = 30.0  # Timeout por defecto
        
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Hace una petición HTTP al backend.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint relativo a la API
            **kwargs: Argumentos adicionales para httpx
            
        Returns:
            Respuesta JSON deserializada
            
        Raises:
            APIError: Si la petición falla
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {method} {url}: {e.response.text}")
            raise APIError(f"API request failed with status {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error for {method} {url}: {e}")
            raise APIError(f"Failed to connect to API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error for {method} {url}: {e}", exc_info=True)
            raise APIError(f"Unexpected error: {str(e)}")
    
    async def get_paper_trading_history(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Obtiene el historial de operaciones de paper trading.
        
        Args:
            symbol: Filtrar por par de trading (ej. BTCUSDT)
            start_date: Fecha de inicio para filtrar
            end_date: Fecha de fin para filtrar
            limit: Número máximo de trades a devolver
            offset: Número de trades a saltar (para paginación)
            
        Returns:
            Respuesta con trades, total_count y has_more
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if symbol:
            params["symbol"] = symbol
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        logger.info(f"Obteniendo historial de paper trading con filtros: {params}")
        
        return await self._make_request(
            "GET", 
            "/api/v1/trades/history/paper",
            params=params
        )
    
    async def get_paper_trading_performance(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene las métricas de rendimiento de paper trading.
        
        Args:
            symbol: Filtrar por par de trading (ej. BTCUSDT)
            start_date: Fecha de inicio para filtrar
            end_date: Fecha de fin para filtrar
            
        Returns:
            Métricas de rendimiento (PerformanceMetrics)
        """
        params = {}
        
        if symbol:
            params["symbol"] = symbol
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        logger.info(f"Obteniendo métricas de rendimiento de paper trading con filtros: {params}")
        
        return await self._make_request(
            "GET",
            "/api/v1/portfolio/paper/performance_summary",
            params=params
        )
    
    async def get_real_trading_history(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Obtiene el historial de operaciones de trading real.
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if symbol:
            params["symbol"] = symbol
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        return await self._make_request(
            "GET", 
            "/api/v1/trades/history/real",
            params=params
        )
    
    async def get_real_trading_performance(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene las métricas de rendimiento de trading real.
        """
        params = {}
        
        if symbol:
            params["symbol"] = symbol
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        return await self._make_request(
            "GET",
            "/api/v1/portfolio/real/performance_summary",
            params=params
        )
    
    async def test_connection(self) -> bool:
        """
        Prueba la conexión con el backend.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            await self._make_request("GET", "/")
            return True
        except APIError:
            return False

    async def get_user_configuration(self) -> Dict[str, Any]:
        """
        Obtiene la configuración actual del usuario.
        """
        logger.info("Obteniendo configuración de usuario.")
        return await self._make_request("GET", "/api/v1/config")

    async def update_user_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza parcialmente la configuración del usuario.
        """
        logger.info(f"Actualizando configuración de usuario: {config_data}")
        return await self._make_request("PATCH", "/api/v1/config", json=config_data)

    async def activate_real_trading_mode(self) -> Dict[str, Any]:
        """
        Activa el modo de operativa real limitada.
        """
        logger.info("Activando modo de operativa real limitada.")
        return await self._make_request("POST", "/api/v1/config/real-trading-mode/activate")

    async def deactivate_real_trading_mode(self) -> Dict[str, Any]:
        """
        Desactiva el modo de operativa real limitada.
        """
        logger.info("Desactivando modo de operativa real limitada.")
        return await self._make_request("POST", "/api/v1/config/real-trading-mode/deactivate")

    async def get_real_trading_mode_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del modo de operativa real limitada y el contador.
        """
        logger.info("Obteniendo estado del modo de operativa real limitada.")
        return await self._make_request("GET", "/api/v1/config/real-trading-mode/status")
