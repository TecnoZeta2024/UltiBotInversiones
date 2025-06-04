from __future__ import annotations

from typing import Optional

from .adapters.binance_adapter import BinanceAdapter
from .adapters.persistence_service import SupabasePersistenceService
from .services.config_service import ConfigService
from .services.credential_service import CredentialService
from .services.market_data_service import MarketDataService
from .services.notification_service import NotificationService
from .services.portfolio_service import PortfolioService
from .services.strategy_service import StrategyService
from .services.performance_service import PerformanceService
from .services.unified_order_execution_service import UnifiedOrderExecutionService
from .services.trading_report_service import TradingReportService # Nueva importación
from .services.trading_engine_service import TradingEngine # Nueva importación

# Se asume que estas variables globales son establecidas en main.py durante el lifespan.
# Considerar un patrón de registro/recuperación de servicios más robusto si esto se vuelve complejo.
# Por ahora, para mantener la estructura similar, las referenciamos como si fueran accesibles.
# Esto podría requerir que main.py las "registre" en un módulo accesible o pase instancias.

# Placeholder para las instancias de servicio que serían inicializadas en main.py
# En un escenario real, estas serían inyectadas o recuperadas de un contenedor de dependencias.
persistence_service_instance: Optional[SupabasePersistenceService] = None
credential_service_instance: Optional[CredentialService] = None
binance_adapter_instance: Optional[BinanceAdapter] = None
market_data_service_instance: Optional[MarketDataService] = None
portfolio_service_instance: Optional[PortfolioService] = None
notification_service_instance: Optional[NotificationService] = None
config_service_instance: Optional[ConfigService] = None
unified_order_execution_service_instance: Optional[UnifiedOrderExecutionService] = None
strategy_service_instance: Optional[StrategyService] = None
performance_service_instance: Optional[PerformanceService] = None
trading_report_service_instance: Optional[TradingReportService] = None # Nueva instancia global
trading_engine_instance: Optional[TradingEngine] = None # Nueva instancia global

# --- Funciones de dependencia para inyección en FastAPI ---
def get_persistence_service() -> SupabasePersistenceService:
    """Obtiene la instancia global del servicio de persistencia."""
    if persistence_service_instance is None:
        # Esta es una simplificación. En main.py, estas variables globales se llenan.
        # Para que esto funcione directamente, main.py necesitaría actualizar estas _instance vars.
        raise RuntimeError("PersistenceService no inicializado en dependencies.py. Revisar flujo de inicialización.")
    return persistence_service_instance


def get_credential_service() -> CredentialService:
    """Obtiene la instancia global del servicio de credenciales."""
    if credential_service_instance is None:
        raise RuntimeError("CredentialService no inicializado en dependencies.py.")
    return credential_service_instance


def get_binance_adapter() -> BinanceAdapter:
    """Obtiene la instancia global del adaptador de Binance."""
    if binance_adapter_instance is None:
        raise RuntimeError("BinanceAdapter no inicializado en dependencies.py.")
    return binance_adapter_instance


def get_market_data_service() -> MarketDataService:
    """Obtiene la instancia global del servicio de datos de mercado."""
    if market_data_service_instance is None:
        raise RuntimeError("MarketDataService no inicializado en dependencies.py.")
    return market_data_service_instance


def get_portfolio_service() -> PortfolioService:
    """Obtiene la instancia global del servicio de portafolio."""
    if portfolio_service_instance is None:
        raise RuntimeError("PortfolioService no inicializado en dependencies.py.")
    return portfolio_service_instance


def get_notification_service() -> NotificationService:
    """Obtiene la instancia global del servicio de notificaciones."""
    if notification_service_instance is None:
        raise RuntimeError("NotificationService no inicializado en dependencies.py.")
    return notification_service_instance


def get_config_service() -> ConfigService:
    """Obtiene la instancia global del servicio de configuración."""
    if config_service_instance is None:
        raise RuntimeError("ConfigService no inicializado en dependencies.py.")
    return config_service_instance


def get_unified_order_execution_service() -> UnifiedOrderExecutionService:
    """Obtiene la instancia global del servicio unificado de ejecución de órdenes."""
    if unified_order_execution_service_instance is None:
        raise RuntimeError("UnifiedOrderExecutionService no inicializado en dependencies.py.")
    return unified_order_execution_service_instance


def get_strategy_service() -> StrategyService:
    """Obtiene la instancia global del servicio de estrategias."""
    if strategy_service_instance is None:
        raise RuntimeError("StrategyService no inicializado en dependencies.py.")
    return strategy_service_instance


def get_performance_service() -> PerformanceService:
    """Obtiene la instancia global del servicio de rendimiento."""
    if performance_service_instance is None:
        raise RuntimeError("PerformanceService no inicializado en dependencies.py.")
    return performance_service_instance


def get_trading_report_service() -> TradingReportService:
    """Obtiene la instancia global del servicio de informes de trading."""
    if trading_report_service_instance is None:
        raise RuntimeError("TradingReportService no inicializado en dependencies.py.")
    return trading_report_service_instance


def get_trading_engine_service() -> TradingEngine:
    """Obtiene la instancia global del servicio del motor de trading."""
    global trading_engine_instance
    if trading_engine_instance is None:
        # Aquí deberías inicializar TradingEngine con los servicios requeridos
        # Por ejemplo:
        # from .services.strategy_service import StrategyService
        # from .services.config_service import ConfigService
        # from .services.ai_orchestrator_service import AIOrchestrator
        # trading_engine_instance = TradingEngine(StrategyService(), ConfigService(), AIOrchestrator())
        raise RuntimeError("TradingEngine no inicializado en dependencies.py. Debe ser registrado en main.py o inicializado aquí.")
    return trading_engine_instance

# Funciones para que main.py actualice las instancias
def set_persistence_service(instance: SupabasePersistenceService):
    global persistence_service_instance
    persistence_service_instance = instance

def set_credential_service(instance: CredentialService):
    global credential_service_instance
    credential_service_instance = instance

def set_binance_adapter(instance: BinanceAdapter):
    global binance_adapter_instance
    binance_adapter_instance = instance

def set_market_data_service(instance: MarketDataService):
    global market_data_service_instance
    market_data_service_instance = instance

def set_portfolio_service(instance: PortfolioService):
    global portfolio_service_instance
    portfolio_service_instance = instance

def set_notification_service(instance: NotificationService):
    global notification_service_instance
    notification_service_instance = instance

def set_config_service(instance: ConfigService):
    global config_service_instance
    config_service_instance = instance

def set_unified_order_execution_service(instance: UnifiedOrderExecutionService):
    global unified_order_execution_service_instance
    unified_order_execution_service_instance = instance

def set_strategy_service(instance: StrategyService):
    global strategy_service_instance
    strategy_service_instance = instance

def set_performance_service(instance: PerformanceService):
    global performance_service_instance
    performance_service_instance = instance

def set_trading_report_service(instance: TradingReportService):
    global trading_report_service_instance
    trading_report_service_instance = instance

def set_trading_engine_service(instance: TradingEngine):
    global trading_engine_instance
    trading_engine_instance = instance
