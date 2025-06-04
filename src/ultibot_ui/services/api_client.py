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
    def __init__(self, message: str, status_code: Optional[int] = None, response_json: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message # El mensaje general del error
        self.status_code = status_code
        self.response_json = response_json # El cuerpo JSON de la respuesta de error, si existe

    def __str__(self):
        return f"APIError(status_code={self.status_code}, message='{self.message}', response_json={self.response_json})"

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
        
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Any: # Cambiado a Any
        """
        Hace una petición HTTP al backend.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint relativo a la API
            **kwargs: Argumentos adicionales para httpx
            
        Returns:
            Respuesta JSON deserializada (puede ser Dict o List)
            
        Raises:
            APIError: Si la petición falla
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status() # Lanza HTTPStatusError para 4xx/5xx
                
                # Para 204 No Content, response.json() fallaría
                if response.status_code == 204:
                    return None 
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {method} {url}: {e.response.text}")
            response_body_json = None
            try:
                response_body_json = e.response.json()
            except Exception: # No es JSON o está vacío
                pass # response_body_json permanece None
            raise APIError(
                message=f"API request failed with status {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
                response_json=response_body_json
            )
        except httpx.RequestError as e: # Errores de red, DNS, timeout de conexión, etc.
            logger.error(f"Request error for {method} {url}: {e}")
            raise APIError(message=f"Failed to connect to API: {str(e)}")
        except Exception as e: # Otros errores inesperados (ej. al parsear JSON de respuesta exitosa)
            logger.error(f"Unexpected error for {method} {url}: {e}", exc_info=True)
            raise APIError(message=f"Unexpected error: {str(e)}")
    
    async def get_paper_trading_history(
        self,
        user_id: UUID, # Añadido user_id
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]: # El backend devuelve List[Trade]
        """
        Obtiene el historial de operaciones de paper trading.
        
        Args:
            user_id: ID del usuario.
            symbol: Filtrar por par de trading (ej. BTCUSDT)
            start_date: Fecha de inicio para filtrar
            end_date: Fecha de fin para filtrar
            limit: Número máximo de trades a devolver
            offset: Número de trades a saltar (para paginación)
            
        Returns:
            Lista de trades.
        """
        params: Dict[str, Any] = {
            "trading_mode": "paper", # Añadido trading_mode
            "limit": limit,
            "offset": offset
        }
        
        if symbol:
            # El endpoint del backend espera 'symbol_filter' según trades.py, no 'symbol'
            params["symbol_filter"] = symbol 
        if start_date:
            # El endpoint del backend espera 'date_from' y 'date_to' como YYYY-MM-DD
            params["date_from"] = start_date.date().isoformat()
        if end_date:
            params["date_to"] = end_date.date().isoformat()
            
        logger.info(f"Obteniendo historial de paper trading para user {user_id} con filtros: {params}")
        
        # El endpoint correcto es /api/v1/trades/{user_id}
        # Asumiendo que el modelo de respuesta del backend es una lista de trades directamente
        return await self._make_request(
            "GET", 
            f"/api/v1/trades/{user_id}", 
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
        params: Dict[str, Any] = {}
        
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
        params: Dict[str, Any] = {
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
        params: Dict[str, Any] = {}
        
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

    async def confirm_real_trade_opportunity(self, opportunity_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Envía una solicitud al backend para confirmar una oportunidad de trading real.
        """
        logger.info(f"Confirmando oportunidad de trading real {opportunity_id} para usuario {user_id}.")
        return await self._make_request(
            "POST",
            f"/api/v1/trading/real/confirm-opportunity/{opportunity_id}",
            json={"opportunity_id": str(opportunity_id), "user_id": str(user_id)}
        )

    async def get_real_trading_candidates(self) -> List[Dict[str, Any]]:
        """
        Obtiene una lista de oportunidades de muy alta confianza pendientes de confirmación
        para operativa real.
        """
        logger.info("Obteniendo oportunidades de trading real pendientes de confirmación.")
        return await self._make_request("GET", "/api/v1/opportunities/real-trading-candidates")

    async def get_open_trades(self, mode: str = "all") -> List[Dict[str, Any]]:
        """
        Obtiene la lista de trades abiertos (paper y/o real).
        
        Args:
            mode: 'paper', 'real', o 'all' para filtrar por modo de trading
            
        Returns:
            Lista de trades abiertos con detalles de TSL/TP
        """
        params = {}
        if mode != "all":
            params["mode"] = mode
            
        logger.info(f"Obteniendo trades abiertos con modo: {mode}")
        return await self._make_request("GET", "/api/v1/trades/open", params=params)

    async def get_capital_management_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual de la gestión de capital para operaciones reales.
        
        Returns:
            Estado de gestión de capital incluyendo:
            - Capital total disponible
            - Capital ya comprometido hoy
            - Límites configurados
            - Capital disponible para nuevas operaciones
        """
        logger.info("Obteniendo estado de gestión de capital.")
        return await self._make_request("GET", "/api/v1/trading/capital-management/status")

    async def get_portfolio_snapshot_with_capital_info(self) -> Dict[str, Any]:
        """
        Obtiene un snapshot completo del portafolio incluyendo información de gestión de capital.
        
        Returns:
            Snapshot del portafolio extendido con información de gestión de capital
        """
        logger.info("Obteniendo snapshot del portafolio con información de capital.")
        return await self._make_request("GET", "/api/v1/portfolio/snapshot/extended")

    async def get_strategies(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las configuraciones de estrategias de trading.
        """
        logger.info("Obteniendo todas las configuraciones de estrategias.")
        return await self._make_request("GET", "/api/v1/strategies")

    async def create_strategy(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una nueva configuración de estrategia de trading.
        
        Args:
            strategy_data: Datos de la estrategia a crear.
            
        Returns:
            La configuración de la estrategia creada.
        """
        logger.info(f"Creando nueva estrategia: {strategy_data}")
        return await self._make_request("POST", "/api/v1/strategies", json=strategy_data)

    async def update_strategy(self, strategy_id: str, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza una configuración de estrategia de trading existente.
        
        Args:
            strategy_id: ID de la estrategia a actualizar.
            strategy_data: Datos para actualizar la estrategia.
            
        Returns:
            La configuración de la estrategia actualizada.
        """
        logger.info(f"Actualizando estrategia {strategy_id}: {strategy_data}")
        return await self._make_request("PUT", f"/api/v1/strategies/{strategy_id}", json=strategy_data)

    async def get_strategy_details(self, strategy_id: str) -> Dict[str, Any]:
        """
        Obtiene los detalles de una configuración de estrategia específica.
        
        Args:
            strategy_id: ID de la estrategia a obtener.
            
        Returns:
            La configuración de la estrategia.
        """
        logger.info(f"Obteniendo detalles para estrategia {strategy_id}")
        return await self._make_request("GET", f"/api/v1/strategies/{strategy_id}")

    async def delete_strategy(self, strategy_id: str) -> None:
        """
        Elimina una configuración de estrategia de trading.
        
        Args:
            strategy_id: ID de la estrategia a eliminar.
            
        Returns:
            None si la eliminación es exitosa (respuesta 204).
        """
        logger.info(f"Eliminando estrategia {strategy_id}")
        # Esperamos un 204 No Content, que _make_request manejará devolviendo None
        await self._make_request("DELETE", f"/api/v1/strategies/{strategy_id}")
        return None

    async def update_strategy_activation_status(self, strategy_id: str, mode: str, active: bool) -> Dict[str, Any]:
        """
        Activa o desactiva una estrategia para un modo de operación específico.
        
        Args:
            strategy_id: ID de la estrategia.
            mode: Modo de operación ('paper' o 'real').
            active: True para activar, False para desactivar.
            
        Returns:
            La configuración de la estrategia actualizada.
        """
        endpoint = f"/api/v1/strategies/{strategy_id}/activate" # Usamos /activate como base
        # El backend debería interpretar active=false como desactivación.
        # Si la historia implica estrictamente dos endpoints diferentes, esto necesitaría ajuste.
        params = {"mode": mode, "active": str(active).lower()} # 'true' o 'false' como strings
        
        action = "activando" if active else "desactivando"
        logger.info(f"Solicitando {action} estrategia {strategy_id} para modo {mode}.")
        
        # Un PATCH usualmente no tiene cuerpo si los cambios se pasan por query params,
        # pero si el backend espera un cuerpo vacío o específico, se ajustaría aquí.
        # Por ahora, asumimos que los query params son suficientes.
        return await self._make_request("PATCH", endpoint, params=params)

    # ===== New Trading Mode Aware Methods =====
    
    async def get_portfolio_snapshot(
        self, 
        user_id: UUID, 
        trading_mode: str = "both"
    ) -> Dict[str, Any]:
        """
        Obtiene snapshot del portafolio para el modo de trading especificado.
        
        Args:
            user_id: ID del usuario
            trading_mode: 'paper', 'real', o 'both'
            
        Returns:
            PortfolioSnapshot filtrado por modo de trading
        """
        params = {"trading_mode": trading_mode}
        logger.info(f"Obteniendo snapshot de portafolio para usuario {user_id}, modo: {trading_mode}")
        return await self._make_request("GET", f"/api/v1/portfolio/snapshot/{user_id}", params=params)
    
    async def get_portfolio_summary(
        self, 
        user_id: UUID, 
        trading_mode: str = "paper"
    ) -> Dict[str, Any]:
        """
        Obtiene resumen del portafolio para un modo específico.
        
        Args:
            user_id: ID del usuario
            trading_mode: 'paper' o 'real'
            
        Returns:
            PortfolioSummary para el modo especificado
        """
        params = {"trading_mode": trading_mode}
        logger.info(f"Obteniendo resumen de portafolio para usuario {user_id}, modo: {trading_mode}")
        return await self._make_request("GET", f"/api/v1/portfolio/summary/{user_id}", params=params)
    
    async def get_available_balance(
        self, 
        user_id: UUID, 
        trading_mode: str = "paper"
    ) -> Dict[str, Any]:
        """
        Obtiene saldo disponible para trading en el modo especificado.
        
        Args:
            user_id: ID del usuario
            trading_mode: 'paper', 'real', o 'both'
            
        Returns:
            Información del saldo disponible
        """
        params = {"trading_mode": trading_mode}
        logger.info(f"Obteniendo saldo disponible para usuario {user_id}, modo: {trading_mode}")
        return await self._make_request("GET", f"/api/v1/portfolio/balance/{user_id}", params=params)
    
    async def get_user_trades(
        self,
        user_id: UUID,
        trading_mode: str = "both",
        status_filter: Optional[str] = None,
        symbol_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtiene trades del usuario filtrados por modo de trading y otros criterios.
        
        Args:
            user_id: ID del usuario
            trading_mode: 'paper', 'real', o 'both'
            status_filter: Filtrar por estado de posición
            symbol_filter: Filtrar por símbolo
            date_from: Fecha de inicio
            date_to: Fecha de fin
            limit: Límite de resultados
            offset: Offset para paginación
            
        Returns:
            Lista de trades que coinciden con los criterios
        """
        params = {
            "trading_mode": trading_mode,
            "limit": limit,
            "offset": offset
        }
        
        if status_filter:
            params["status_filter"] = status_filter
        if symbol_filter:
            params["symbol_filter"] = symbol_filter
        if date_from:
            params["date_from"] = date_from.date().isoformat()
        if date_to:
            params["date_to"] = date_to.date().isoformat()
            
        logger.info(f"Obteniendo trades para usuario {user_id}, modo: {trading_mode}, filtros: {params}")
        return await self._make_request("GET", f"/api/v1/trades/trades/{user_id}", params=params)
    
    async def get_open_trades_by_mode(
        self,
        user_id: UUID,
        trading_mode: str = "both"
    ) -> List[Dict[str, Any]]:
        """
        Obtiene solo las operaciones abiertas para el modo especificado.
        
        Args:
            user_id: ID del usuario
            trading_mode: 'paper', 'real', o 'both'
            
        Returns:
            Lista de trades abiertos
        """
        params = {"trading_mode": trading_mode}
        logger.info(f"Obteniendo trades abiertos para usuario {user_id}, modo: {trading_mode}")
        return await self._make_request("GET", f"/api/v1/trades/{user_id}/open", params=params)
    
    async def execute_market_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str,
        quantity: float,
        trading_mode: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta una orden de mercado en el modo especificado.
        
        Args:
            user_id: ID del usuario
            symbol: Símbolo de trading (ej. 'BTCUSDT')
            side: Lado de la orden ('BUY' o 'SELL')
            quantity: Cantidad de la orden
            trading_mode: 'paper' o 'real'
            api_key: Clave API para trading real (requerida para modo real)
            api_secret: Secreto API para trading real (requerida para modo real)
            
        Returns:
            TradeOrderDetails con los resultados de la ejecución
        """
        request_data = {
            "user_id": str(user_id),
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "trading_mode": trading_mode
        }
        
        if trading_mode == "real":
            if not api_key or not api_secret:
                raise ValueError("API key and secret are required for real trading mode")
            request_data["api_key"] = api_key
            request_data["api_secret"] = api_secret
            
        logger.info(f"Ejecutando orden de mercado {side} {quantity} {symbol} en modo {trading_mode}")
        return await self._make_request("POST", "/api/v1/trading/market-order", json=request_data)

    async def get_strategy_performance(
        self,
        user_id: UUID, # Asumiendo que el performance es por usuario
        mode: Optional[str] = None  # 'paper', 'real', o None para 'all'
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el resumen de desempeño por estrategia.

        Args:
            user_id: ID del usuario para el cual obtener el desempeño.
            mode: Modo de operación para filtrar ('paper', 'real'). 
                  Si es None, el backend podría devolver todos los modos o un default.

        Returns:
            Lista de diccionarios, cada uno con el desempeño de una estrategia.
            Ej: [{"strategyName": "Scalping BTC", "mode": "paper", "totalOperations": 10, ...}]
        """
        # El user_id se maneja implícitamente en el backend para este endpoint.
        endpoint = "/api/v1/performance/strategies" 
        params: Dict[str, Any] = {}
        if mode:
            params["mode"] = mode
        
        logger.info(f"Obteniendo desempeño de estrategias (usuario implícito por backend) con modo: {mode if mode else 'todos'}")
        return await self._make_request("GET", endpoint, params=params)

    async def get_ticker_data(self, user_id: UUID, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Obtiene datos de ticker para una lista de símbolos.
        Endpoint: GET /api/v1/market/tickers?user_id=<user_id>&symbols=BTCUSDT,ETHUSDT

        Args:
            user_id: ID del usuario.
            symbols: Lista de símbolos de trading (ej. ["BTCUSDT", "ETHUSDT"])

        Returns:
            Lista de diccionarios, cada uno representando datos de ticker para un símbolo.
            Ej: [{"symbol": "BTCUSDT", "lastPrice": "60000.0", ...}, ...]
        """
        if not symbols:
            return []

        params = {
            "user_id": str(user_id),
            "symbols": ",".join(symbols)
        }
        logger.info(f"Obteniendo datos de ticker para usuario {user_id} y símbolos: {symbols}")
        # Assuming the backend returns a list of ticker data directly
        return await self._make_request("GET", "/api/v1/market/tickers", params=params)

    async def get_candlestick_data(
        self,
        user_id: UUID,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene datos de velas (k-lines) para un símbolo y temporalidad específicos.

        Args:
            user_id: ID del usuario (obligatorio para el backend)
            symbol: Símbolo de trading (ej. "BTCUSDT")
            interval: Temporalidad de las velas (ej. "1h", "1d", "5m")
            start_time: Fecha de inicio opcional para los datos (datetime)
            end_time: Fecha de fin opcional para los datos (datetime)
            limit: Número máximo opcional de velas a devolver

        Returns:
            Lista de diccionarios, cada uno representando una vela (OHLCV).
            Ejemplo: [{"open_time": ..., "open": ..., ...}, ...]
        """
        params: Dict[str, Any] = {
            "user_id": str(user_id),
            "symbol": symbol,
            "interval": interval
        }
        if start_time is not None:
            params["start_time"] = int(start_time.timestamp() * 1000)
        if end_time is not None:
            params["end_time"] = int(end_time.timestamp() * 1000)
        if limit is not None:
            params["limit"] = limit

        logger.info(f"Obteniendo datos de velas para {symbol} ({interval}) con parámetros: {params}")
        return await self._make_request("GET", "/api/v1/market/klines", params=params)

    async def get_notification_history(
        self,
        user_id: UUID, # Assuming user_id might be part of the path or a query param based on backend design
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]: # Return type changed to Dict to match get_paper_trading_history
        """
        Obtiene el historial de notificaciones para el usuario.
        Assumed Endpoint: GET /api/v1/users/{user_id}/notifications/history or /api/v1/notifications/history?user_id=...
        For this implementation, let's assume user_id is part of the path.
        If user_id is implicitly handled by backend context (e.g. from auth token), it can be removed.

        Args:
            user_id: ID del usuario para el cual obtener las notificaciones.
            limit: Número máximo de notificaciones a devolver.
            offset: Número de notificaciones a saltar (para paginación).

        Returns:
            Un diccionario conteniendo una lista de notificaciones y detalles de paginación.
            Ej: {"notifications": [{"id": "...", "title": "...", ...}], "total_count": 10, "has_more": false}
        """
        params: Dict[str, Any] = {
            "user_id": str(user_id), # Añadido user_id como parámetro query
            "limit": limit,
            "offset": offset
        }
        # Path could be /api/v1/notifications/history and user_id passed as query param if not implicit
        # Or, if user_id is part of the path:
        # endpoint = f"/api/v1/users/{user_id}/notifications/history"
        # For now, assuming a general endpoint and user_id is handled by backend context or not strictly enforced for this call.
        # Let's use /api/v1/notifications/history as per front-end-api-interaction.md.
        # El error 422 confirma que user_id es esperado como query param.

        logger.info(f"Obteniendo historial de notificaciones para usuario {user_id} con paginación: limit={limit}, offset={offset}")
        # Assuming the backend returns a dict with 'notifications' list and pagination details
        return await self._make_request("GET", "/api/v1/notifications/history", params=params)

    async def get_gemini_opportunities(self) -> List[Dict[str, Any]]:
        """
        Obtiene oportunidades detectadas por la IA Gemini (mock/demo).
        """
        logger.info("Obteniendo oportunidades IA Gemini (demo/mock).")
        return await self._make_request("GET", "/api/v1/gemini/opportunities")
