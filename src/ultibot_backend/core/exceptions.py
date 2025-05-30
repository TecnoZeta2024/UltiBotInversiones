from typing import Optional, Dict, Any

class UltiBotError(Exception):
    """Excepción base para errores de UltiBotInversiones."""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.details = details if details is not None else {}

class CredentialError(UltiBotError):
    """Excepción para errores relacionados con credenciales."""
    pass

class NotificationError(UltiBotError):
    """Excepción base para errores en el servicio de notificaciones."""
    pass

class TelegramNotificationError(NotificationError):
    """Excepción específica para errores al enviar notificaciones de Telegram."""
    def __init__(self, message: str, code: Optional[str] = None, telegram_response: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, code)
        self.telegram_response = telegram_response
        self.original_exception = original_exception

class ExternalAPIError(UltiBotError):
    """Excepción para errores al interactuar con APIs externas."""
    def __init__(self, message: str, service_name: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, code=f"{service_name.upper()}_API_ERROR")
        self.service_name = service_name
        self.status_code = status_code
        self.response_data = response_data
        self.original_exception = original_exception

class BinanceAPIError(ExternalAPIError):
    """Excepción específica para errores al interactuar con la API de Binance."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, service_name="BINANCE", status_code=status_code, response_data=response_data, original_exception=original_exception)

class ConfigurationError(UltiBotError):
    """Excepción para errores relacionados con la configuración de la aplicación."""
    pass

class OrderExecutionError(UltiBotError):
    """Excepción para errores durante la ejecución de órdenes de trading."""
    pass
