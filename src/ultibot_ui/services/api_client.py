import logging
from typing import Any, Dict, Optional, List
from uuid import UUID
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from src.shared.data_types import PerformanceMetrics, Trade

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Excepción personalizada para errores de la API."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self):
        if self.status_code:
            return f"Error de API ({self.status_code}): {self.message}"
        return f"Error de API: {self.message}"

def is_connection_error(exception: BaseException) -> bool:
    """Filtro para tenacity: reintentar solo si es un error de conexión, no un error HTTP."""
    return isinstance(exception, APIError) and exception.status_code is None

class UltiBotAPIClient:
    """Cliente para interactuar con la API del backend de UltiBot."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        logger.debug(f"API client initialized with shared httpx client.")
        
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = endpoint
        try:
            logger.debug(f"APIClient: _make_request invocado para {method} {url}")
            print(f"Intentando conectar a: {self._client.base_url}{url}")
            
            response = await self._client.request(method, url, **kwargs)
            
            logger.info(f"HTTP Request: {method} {url} \"HTTP/{response.http_version} {response.status_code} {response.reason_phrase}\"")
            print(f"Respuesta recibida: Estado {response.status_code} {response.reason_phrase}")

            response.raise_for_status()
            # Handle cases with no content
            if response.status_code == 204:
                return None
            data = response.json()
            logger.debug(f"Datos recibidos: {data}")
            return data
        except httpx.HTTPStatusError as e:
            error_msg = f"Error HTTP {e.response.status_code} para {method} {url}: {e.response.text}"
            logger.error(error_msg)
            print(f"ERROR API: {error_msg}")
            try:
                detail = e.response.json().get("detail", e.response.text)
            except ValueError:
                detail = e.response.text
            raise APIError(
                message=detail,
                status_code=e.response.status_code
            ) from e
        except httpx.RequestError as e:
            error_msg = f"Error de red para {method} {url}: {e}"
            logger.error(error_msg)
            print(f"ERROR DE CONEXIÓN: {error_msg}")
            raise APIError(f"Error de conexión: {e}") from e
        except Exception as e:
            error_msg = f"Error inesperado durante la petición a {url}: {str(e)}"
            logger.critical(error_msg, exc_info=True)
            print(f"ERROR CRÍTICO: {error_msg}")
            raise APIError(f"Error inesperado: {str(e)}") from e

    # ============================================
    # EXISTING METHODS
    # ============================================
    
    async def get_trading_mode(self) -> Dict[str, str]:
        """Gets the application's current trading mode."""
        logger.info("Getting trading mode from backend.")
        return await self._make_request("GET", "/api/v1/trading-mode")

    async def set_trading_mode(self, mode: str) -> Dict[str, Any]:
        """Sets the application's trading mode."""
        logger.info(f"Setting trading mode to {mode} via backend.")
        return await self._make_request("POST", "/api/v1/trading-mode", json={"mode": mode})

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(APIError),
        before_sleep=lambda retry_state: logger.info(f"Reintentando conexión al backend... intento {retry_state.attempt_number}")
    )
    async def get_user_configuration(self) -> Dict[str, Any]:
        logger.info("Obteniendo configuración de usuario.")
        print("Solicitando configuración de usuario al backend...")
        return await self._make_request("GET", "/api/v1/config")

    async def get_portfolio_snapshot(self, user_id: UUID, trading_mode: str) -> Dict[str, Any]:
        logger.info(f"Obteniendo snapshot del portafolio para {user_id}, modo: {trading_mode}")
        params = {"user_id": str(user_id), "trading_mode": trading_mode}
        return await self._make_request("GET", "/api/v1/portfolio/snapshot", params=params)

    async def get_trades(self, trading_mode: str, **kwargs) -> List[Dict[str, Any]]:
        params = {"trading_mode": trading_mode, **kwargs}
        logger.info(f"Obteniendo trades, modo: {trading_mode}, filtros: {params}")
        return await self._make_request("GET", "/api/v1/trades", params=params)

    async def get_trading_performance(self, trading_mode: str, **kwargs) -> Dict[str, Any]:
        params = {"trading_mode": trading_mode, **kwargs}
        return await self._make_request("GET", "/api/v1/performance/metrics", params=params)

    async def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        params = {"symbol": symbol, "interval": timeframe, "limit": limit}
        return await self._make_request("GET", "/api/v1/market/klines", params=params)

    async def get_market_history(self, symbol: str, interval: str, limit: int) -> List[Dict[str, Any]]:
        """Gets historical market data from the database."""
        logger.info(f"Getting market history for {symbol} from backend.")
        params = {"interval": interval, "limit": limit}
        return await self._make_request("GET", f"/api/v1/market/history/{symbol}", params=params)

    async def get_ai_opportunities(self) -> List[Dict[str, Any]]:
        return await self._make_request("GET", "/api/v1/opportunities/real-trading-candidates")

    async def get_strategies(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de estrategias de IA disponibles."""
        return await self._make_request("GET", "/api/v1/strategies/strategies")

    async def get_notification_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene el historial de notificaciones."""
        params = {"limit": limit}
        return await self._make_request("GET", "/api/v1/notifications/history", params=params)

    # ============================================
    # NEW MARKET CONFIGURATION METHODS
    # ============================================
    
    # Market Scan Methods
    
    async def execute_market_scan(self, scan_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ejecuta un escaneo de mercado con configuración específica.
        
        Args:
            scan_config: Configuración del escaneo de mercado.
            
        Returns:
            Lista de oportunidades de mercado que coinciden con los criterios.
        """
        logger.info("Ejecutando escaneo de mercado personalizado.")
        response = await self._make_request(
            "POST", 
            "/api/v1/market-configuration/scan/execute", 
            json=scan_config
        )
        return response.get("data", [])

    async def execute_preset_scan(self, preset_id: str) -> List[Dict[str, Any]]:
        """Ejecuta un escaneo de mercado usando un preset.
        
        Args:
            preset_id: ID del preset a ejecutar.
            
        Returns:
            Lista de oportunidades de mercado.
        """
        logger.info(f"Ejecutando escaneo con preset '{preset_id}'.")
        response = await self._make_request(
            "POST", 
            f"/api/v1/market-configuration/scan/preset/{preset_id}/execute"
        )
        return response.get("data", [])

    # Scan Presets Methods
    
    async def get_scan_presets(self, include_system: bool = True) -> List[Dict[str, Any]]:
        """Obtiene la lista de presets de escaneo disponibles.
        
        Args:
            include_system: Si incluir presets del sistema.
            
        Returns:
            Lista de presets de escaneo.
        """
        logger.info("Obteniendo presets de escaneo.")
        params = {"include_system": include_system}
        response = await self._make_request(
            "GET", 
            "/api/v1/market-configuration/presets", 
            params=params
        )
        return response.get("data", [])

    async def create_scan_preset(self, preset: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo preset de escaneo.
        
        Args:
            preset: Datos del preset a crear.
            
        Returns:
            Preset creado con ID y timestamps generados.
        """
        logger.info(f"Creando preset de escaneo '{preset.get('name', 'sin nombre')}'.")
        response = await self._make_request(
            "POST", 
            "/api/v1/market-configuration/presets", 
            json=preset
        )
        return response.get("data", {})

    async def get_scan_preset(self, preset_id: str) -> Dict[str, Any]:
        """Obtiene un preset específico por ID.
        
        Args:
            preset_id: ID del preset a obtener.
            
        Returns:
            Datos del preset solicitado.
        """
        logger.info(f"Obteniendo preset de escaneo '{preset_id}'.")
        response = await self._make_request(
            "GET", 
            f"/api/v1/market-configuration/presets/{preset_id}"
        )
        return response.get("data", {})

    async def update_scan_preset(self, preset_id: str, preset: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un preset de escaneo existente.
        
        Args:
            preset_id: ID del preset a actualizar.
            preset: Datos actualizados del preset.
            
        Returns:
            Preset actualizado.
        """
        logger.info(f"Actualizando preset de escaneo '{preset_id}'.")
        response = await self._make_request(
            "PUT", 
            f"/api/v1/market-configuration/presets/{preset_id}", 
            json=preset
        )
        return response.get("data", {})

    async def delete_scan_preset(self, preset_id: str) -> bool:
        """Elimina un preset de escaneo.
        
        Args:
            preset_id: ID del preset a eliminar.
            
        Returns:
            True si se eliminó exitosamente.
        """
        logger.info(f"Eliminando preset de escaneo '{preset_id}'.")
        response = await self._make_request(
            "DELETE", 
            f"/api/v1/market-configuration/presets/{preset_id}"
        )
        return response.get("status") == "success"

    async def get_system_presets(self) -> List[Dict[str, Any]]:
        """Obtiene los presets del sistema.
        
        Returns:
            Lista de presets del sistema.
        """
        logger.info("Obteniendo presets del sistema.")
        response = await self._make_request(
            "GET", 
            "/api/v1/market-configuration/system-presets"
        )
        return response.get("data", [])

    # Asset Trading Parameters Methods
    
    async def get_asset_trading_parameters(self) -> List[Dict[str, Any]]:
        """Obtiene todos los parámetros de trading por activo del usuario.
        
        Returns:
            Lista de parámetros de trading por activo.
        """
        logger.info("Obteniendo parámetros de trading por activo.")
        response = await self._make_request(
            "GET", 
            "/api/v1/market-configuration/asset-parameters"
        )
        return response.get("data", [])

    async def create_asset_trading_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Crea nuevos parámetros de trading para un activo.
        
        Args:
            parameters: Parámetros de trading a crear.
            
        Returns:
            Parámetros creados con ID generado.
        """
        logger.info(f"Creando parámetros de trading para activo '{parameters.get('name', 'sin nombre')}'.")
        response = await self._make_request(
            "POST", 
            "/api/v1/market-configuration/asset-parameters", 
            json=parameters
        )
        return response.get("data", {})

    async def get_asset_trading_parameter(self, parameter_id: str) -> Dict[str, Any]:
        """Obtiene parámetros específicos de trading por ID.
        
        Args:
            parameter_id: ID de los parámetros a obtener.
            
        Returns:
            Parámetros de trading solicitados.
        """
        logger.info(f"Obteniendo parámetros de trading '{parameter_id}'.")
        response = await self._make_request(
            "GET", 
            f"/api/v1/market-configuration/asset-parameters/{parameter_id}"
        )
        return response.get("data", {})

    async def update_asset_trading_parameters(self, parameter_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza parámetros de trading existentes.
        
        Args:
            parameter_id: ID de los parámetros a actualizar.
            parameters: Datos actualizados de los parámetros.
            
        Returns:
            Parámetros actualizados.
        """
        logger.info(f"Actualizando parámetros de trading '{parameter_id}'.")
        response = await self._make_request(
            "PUT", 
            f"/api/v1/market-configuration/asset-parameters/{parameter_id}", 
            json=parameters
        )
        return response.get("data", {})

    async def delete_asset_trading_parameters(self, parameter_id: str) -> bool:
        """Elimina parámetros de trading de un activo.
        
        Args:
            parameter_id: ID de los parámetros a eliminar.
            
        Returns:
            True si se eliminaron exitosamente.
        """
        logger.info(f"Eliminando parámetros de trading '{parameter_id}'.")
        response = await self._make_request(
            "DELETE", 
            f"/api/v1/market-configuration/asset-parameters/{parameter_id}"
        )
        return response.get("status") == "success"

    # Convenience Methods for Market Configuration
    
    async def get_available_market_cap_ranges(self) -> List[str]:
        """Obtiene los rangos de capitalización de mercado disponibles.
        
        Returns:
            Lista de rangos disponibles (MICRO_CAP, SMALL_CAP, etc.).
        """
        # Esta información está en los enums del backend, se puede hardcodear
        # o agregar un endpoint específico en el futuro
        return [
            "MICRO_CAP",     # < $300M
            "SMALL_CAP",     # $300M - $2B
            "MID_CAP",       # $2B - $10B
            "LARGE_CAP",     # $10B - $200B
            "MEGA_CAP"       # > $200B
        ]

    async def get_available_volume_filters(self) -> List[str]:
        """Obtiene los tipos de filtros de volumen disponibles.
        
        Returns:
            Lista de tipos de filtros (HIGH_VOLUME, ABOVE_AVERAGE, etc.).
        """
        return [
            "HIGH_VOLUME",      # Top 10% de volumen
            "ABOVE_AVERAGE",    # Por encima del promedio
            "MODERATE",         # Volumen moderado
            "LOW_VOLUME"        # Volumen bajo pero líquido
        ]

    async def get_available_trend_directions(self) -> List[str]:
        """Obtiene las direcciones de tendencia disponibles.
        
        Returns:
            Lista de direcciones (BULLISH, BEARISH, SIDEWAYS).
        """
        return [
            "BULLISH",    # Tendencia alcista
            "BEARISH",    # Tendencia bajista
            "SIDEWAYS"    # Tendencia lateral
        ]

    async def validate_scan_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida una configuración de escaneo antes de ejecutarla.
        
        Args:
            config: Configuración a validar.
            
        Returns:
            Resultado de la validación con errores si los hay.
        """
        errors = []
        warnings = []
        
        # Validaciones básicas del lado del cliente
        if config.get("min_price_change_24h_percent") is not None and config.get("max_price_change_24h_percent") is not None:
            if config["min_price_change_24h_percent"] > config["max_price_change_24h_percent"]:
                errors.append("El cambio mínimo de precio no puede ser mayor al máximo")
        
        if config.get("min_rsi") is not None and config.get("max_rsi") is not None:
            if config["min_rsi"] > config["max_rsi"]:
                errors.append("El RSI mínimo no puede ser mayor al máximo")
                
        if config.get("min_rsi") is not None and (config["min_rsi"] < 0 or config["min_rsi"] > 100):
            errors.append("El RSI debe estar entre 0 y 100")
            
        if config.get("max_rsi") is not None and (config["max_rsi"] < 0 or config["max_rsi"] > 100):
            errors.append("El RSI debe estar entre 0 y 100")

        # Advertencias para configuraciones restrictivas
        if (config.get("min_volume_24h_usd", 0) > 10_000_000):  # $10M
            warnings.append("Filtro de volumen muy restrictivo, puede resultar en pocos resultados")
            
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
