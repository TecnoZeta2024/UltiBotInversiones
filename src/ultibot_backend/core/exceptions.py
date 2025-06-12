from typing import Optional, Dict, Any

class UltiBotError(Exception):
    """Excepción base para errores de UltiBotInversiones."""
    def __init__(self, message: str, status_code: int = 500, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details if details is not None else {}

class CredentialError(UltiBotError):
    """Excepción para errores relacionados con credenciales."""
    def __init__(self, message: str, code: Optional[str] = "CREDENTIAL_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, code=code, details=details)

class PersistenceError(UltiBotError):
    """Excepción para errores relacionados con la capa de persistencia."""
    def __init__(self, message: str, code: Optional[str] = "PERSISTENCE_ERROR", details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, status_code=500, code=code, details=details)
        self.original_exception = original_exception

class NotificationError(UltiBotError):
    """Excepción base para errores en el servicio de notificaciones."""
    pass

class TelegramNotificationError(NotificationError):
    """Excepción específica para errores al enviar notificaciones de Telegram."""
    def __init__(self, message: str, code: Optional[str] = None, telegram_response: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, code=code)
        self.telegram_response = telegram_response
        self.original_exception = original_exception

class ExternalAPIError(UltiBotError):
    """Excepción para errores al interactuar con APIs externas."""
    def __init__(self, message: str, service_name: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        # Aseguramos que siempre se pase un int a la clase base
        final_status_code = status_code if status_code is not None else 502
        super().__init__(message, status_code=final_status_code, code=f"{service_name.upper()}_API_ERROR")
        self.service_name = service_name
        self.response_data = response_data
        self.original_exception = original_exception

class BinanceAPIError(ExternalAPIError):
    """Excepción específica para errores al interactuar con la API de Binance."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, service_name="BINANCE", status_code=status_code, response_data=response_data, original_exception=original_exception)

class ConfigurationError(UltiBotError):
    """Excepción para errores relacionados con la configuración de la aplicación."""
    def __init__(self, message: str, code: Optional[str] = "CONFIG_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, code=code, details=details)

class InvalidParameterError(UltiBotError):
    """Excepción para parámetros inválidos o faltantes en una solicitud."""
    def __init__(self, message: str, code: Optional[str] = "INVALID_PARAMETER", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, code=code, details=details)

class OrderExecutionError(UltiBotError):
    """Excepción para errores durante la ejecución de órdenes de trading."""
    def __init__(self, message: str, code: Optional[str] = "ORDER_EXECUTION_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, code=code, details=details)

class TradeExecutionError(UltiBotError):
    """Excepción para errores durante la ejecución de un trade completo."""
    def __init__(self, message: str, code: Optional[str] = "TRADE_EXECUTION_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, code=code, details=details)


class MCPError(ExternalAPIError):
    """Excepción específica para errores al interactuar con un Servidor de Contexto de Modelo (MCP)."""
    def __init__(self, message: str, mcp_id: str, mcp_url: Optional[str] = None, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, service_name=f"MCP_{mcp_id}", status_code=status_code, response_data=response_data, original_exception=original_exception)
        self.mcp_id = mcp_id
        self.mcp_url = mcp_url

class AIAnalysisError(UltiBotError):
    """Excepción para errores durante el proceso de análisis de IA (ej. con Gemini)."""
    def __init__(self, message: str, llm_provider: Optional[str] = "GEMINI", details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, status_code=500, code=f"{llm_provider.upper()}_ANALYSIS_ERROR" if llm_provider else "AI_ANALYSIS_ERROR", details=details)
        self.llm_provider = llm_provider
        self.original_exception = original_exception

class AIServiceError(UltiBotError):
    """Excepción para errores generales en los servicios de IA."""
    def __init__(self, message: str, service_name: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, status_code=500, code=f"{service_name.upper()}_SERVICE_ERROR", details=details)
        self.service_name = service_name
        self.original_exception = original_exception

class MarketDataError(UltiBotError):
    """Excepción para errores al obtener datos de mercado."""
    def __init__(self, message: str, code: Optional[str] = "MARKET_DATA_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=502, code=code, details=details)


class PortfolioError(UltiBotError):
    """Excepción para errores relacionados con la gestión del portafolio."""
    def __init__(self, message: str, code: Optional[str] = "PORTFOLIO_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, code=code, details=details)

class InsufficientFundsError(PortfolioError):
    """Excepción para cuando el saldo de un activo es insuficiente para una operación."""
    def __init__(self, message: str = "Fondos insuficientes.", asset: Optional[str] = None, available: Optional[float] = None, required: Optional[float] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="INSUFFICIENT_FUNDS", details={
            "asset": asset,
            "available_balance": available,
            "required_amount": required,
            **(details if details else {})
        })
        self.asset = asset
        self.available = available
        self.required = required

class InsufficientUSDTBalanceError(InsufficientFundsError):
    """Excepción para cuando el saldo de USDT es insuficiente para una operación."""
    def __init__(self, message: str = "Saldo de USDT insuficiente.", available_balance: Optional[float] = None, required_amount: Optional[float] = None, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, asset="USDT", available=available_balance, required=required_amount, details=details)
        self.original_exception = original_exception

class RealTradeLimitReachedError(ConfigurationError):
    """Excepción para cuando se ha alcanzado el límite de operaciones reales permitidas."""
    def __init__(self, message: str = "Límite de operaciones reales alcanzado.", executed_count: Optional[int] = None, limit: Optional[int] = None, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, code="REAL_TRADE_LIMIT_REACHED", details={
            "executed_count": executed_count,
            "limit": limit,
            **(details if details else {})
        })
        self.executed_count = executed_count
        self.limit = limit
        self.original_exception = original_exception

class MobulaAPIError(ExternalAPIError):
    """Excepción específica para errores al interactuar con la API de Mobula."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, service_name="MOBULA", status_code=status_code, response_data=response_data, original_exception=original_exception)

class ReportError(UltiBotError):
    """Excepción para errores relacionados con la generación o procesamiento de reportes."""
    def __init__(self, message: str, code: Optional[str] = "REPORT_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, code=code, details=details)


class ServiceUnavailableError(UltiBotError):
    """Excepción para cuando un servicio no está disponible."""
    def __init__(self, message: str, service_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=503, code="SERVICE_UNAVAILABLE", details=details)
        self.service_name = service_name

class TimeoutError(UltiBotError):
    """Excepción para operaciones que exceden el tiempo límite."""
    def __init__(self, message: str, timeout: Optional[float] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=408, code="OPERATION_TIMEOUT", details=details)
        self.timeout = timeout

class ToolNotFoundError(UltiBotError):
    """Excepción para cuando una herramienta solicitada no se encuentra en el MCPToolHub."""
    def __init__(self, tool_name: str, message: Optional[str] = None):
        if message is None:
            message = f"La herramienta '{tool_name}' no fue encontrada."
        super().__init__(message, status_code=404, code="TOOL_NOT_FOUND", details={"tool_name": tool_name})
        self.tool_name = tool_name

class ToolExecutionError(UltiBotError):
    """Excepción para errores durante la ejecución de una herramienta en el MCPToolHub."""
    def __init__(self, tool_name: str, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(
            message,
            status_code=500,
            code="TOOL_EXECUTION_ERROR",
            details={
                "tool_name": tool_name,
                **(details if details else {})
            }
        )
        self.tool_name = tool_name
        self.original_exception = original_exception

class DataProviderError(ExternalAPIError):
    """Excepción para errores de proveedores de datos como Mobula."""
    def __init__(self, message: str, provider_name: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, service_name=provider_name, status_code=status_code, response_data=response_data, original_exception=original_exception)

class PromptNotFoundError(UltiBotError):
    """Excepción para cuando un prompt no se encuentra."""
    def __init__(self, message: str, code: Optional[str] = "PROMPT_NOT_FOUND", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, code=code, details=details)

class RateLimitError(ExternalAPIError):
    """Excepción para errores de rate limiting."""
    def __init__(self, message: str, service_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, service_name=service_name, status_code=429, details=details)

class TemplateRenderError(UltiBotError):
    """Excepción para errores al renderizar plantillas de prompts."""
    def __init__(self, message: str, template_name: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, status_code=500, code="TEMPLATE_RENDER_ERROR", details=details)
        self.template_name = template_name
        self.original_exception = original_exception

class HandlerNotFoundError(UltiBotError):
    """Excepción para cuando no se encuentra un manejador para un comando o consulta."""
    def __init__(self, message: str, code: Optional[str] = "HANDLER_NOT_FOUND", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, code=code, details=details)

class InvalidHandlerError(UltiBotError):
    """Excepción para cuando se intenta registrar un manejador inválido."""
    def __init__(self, message: str, code: Optional[str] = "INVALID_HANDLER", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, code=code, details=details)
