"""
Módulo que define las interfaces (puertos) para la comunicación del núcleo de dominio
con el exterior. Estos puertos aseguran el desacoplamiento y la pureza del dominio,
siguiendo los principios de la Arquitectura Hexagonal.
"""

from abc import ABC, abstractmethod
from typing import Protocol, List, Optional, Any, Type, TypeVar, Dict
from datetime import datetime
from decimal import Decimal
from uuid import UUID

# Importaciones de modelos de dominio puros (sin frameworks externos)
from .domain_models.trade import Trade, TradeOrderDetails, OrderCategory
from .domain_models.portfolio import Portfolio, UserId, PortfolioSnapshot
from .domain_models.market import MarketData, TickerData, KlineData
from .domain_models.ai_models import AIAnalysisResult, TradingOpportunity, ToolExecutionResult, AIModelType, AISystemMetrics
from .domain_models.prompt_models import PromptTemplate
from .domain_models.user_configuration_models import UserConfiguration, ScanPreset
from shared.data_types import APICredential, ServiceName, Notification
from .domain_models.opportunity_models import Opportunity, OpportunityStatus

T = TypeVar("T")

class IRepository(Protocol):
    """
    Interfaz genérica para un repositorio de datos.
    """
    async def add(self, entity: T) -> None:
        ...

    async def get(self, entity_type: Type[T], id: Any) -> Optional[T]:
        ...

    async def find(self, entity_type: Type[T], **filters) -> List[T]:
        ...
    
    async def find_one(self, entity_type: Type[T], **filters) -> Optional[T]:
        ...

class IUnitOfWork(Protocol):
    """
    Interfaz para el patrón Unit of Work.
    """
    repository: IRepository

    async def __aenter__(self):
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ...

    async def commit(self):
        ...

    async def rollback(self):
        ...

class IPersistencePort(Protocol):
    """
    Interfaz para el puerto de persistencia de datos.
    Define los contratos para guardar y recuperar entidades del dominio.
    """
    async def get_user_configuration(self, user_id: UUID) -> Optional[Dict[str, Any]]: ...
    async def upsert_user_configuration(self, config_data: Dict[str, Any]): ...
    async def delete_user_configuration(self, user_id: str) -> bool: ...
    async def save_credential(self, credential: APICredential) -> APICredential: ...
    async def get_credentials_by_service(self, service_name: ServiceName) -> List[APICredential]: ...
    async def get_credential_by_id(self, credential_id: UUID) -> Optional[APICredential]: ...
    async def get_credential_by_service_label(self, service_name: ServiceName, credential_label: str) -> Optional[APICredential]: ...
    async def update_credential_status(self, credential_id: UUID, new_status: str, last_verified_at: Optional[datetime] = None) -> Optional[APICredential]: ...
    async def delete_credential(self, credential_id: UUID) -> bool: ...
    async def get_opportunity_by_id(self, opportunity_id: UUID) -> Optional[Opportunity]: ...
    async def update_opportunity_status(self, opportunity_id: UUID, new_status: OpportunityStatus, status_reason: Optional[str] = None) -> Optional[Opportunity]: ...
    async def upsert_opportunity(self, opportunity_data: Dict[str, Any]) -> Opportunity: ...
    async def get_opportunities_by_status(self, status: OpportunityStatus) -> List[Opportunity]: ...
    async def upsert_trade(self, trade_data: Dict[str, Any]): ...
    async def get_all_trades_for_user(self, mode: Optional[str] = None) -> List[Trade]: ...
    async def get_closed_trades_count(self, is_real_trade: bool) -> int: ...
    async def update_credential_permissions(self, credential_id: UUID, permissions: List[str], permissions_checked_at: datetime) -> Optional[APICredential]: ...
    async def save_notification(self, notification: Notification) -> Notification: ...
    async def get_notification_history(self, limit: int = 50) -> List[Notification]: ...
    async def mark_notification_as_read(self, notification_id: UUID) -> Optional[Notification]: ...
    async def get_open_paper_trades(self) -> List[Trade]: ...
    async def get_open_real_trades(self) -> List[Trade]: ...
    async def get_closed_trades(self, filters: Dict[str, Any], start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]: ...
    async def update_opportunity_analysis(self, opportunity_id: UUID, status: OpportunityStatus, ai_analysis: Optional[str] = None, confidence_score: Optional[float] = None, suggested_action: Optional[str] = None, status_reason: Optional[str] = None) -> Optional[Opportunity]: ...
    async def upsert_strategy_config(self, strategy_data: Dict[str, Any]) -> None: ...
    async def get_strategy_config_by_id(self, strategy_id: UUID) -> Optional[Dict[str, Any]]: ...
    async def list_strategy_configs_by_user(self) -> List[Dict[str, Any]]: ...
    async def delete_strategy_config(self, strategy_id: UUID) -> bool: ...
    async def get_trades_with_filters(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Trade]: ...
    async def list_scan_presets(self, include_system: bool = True) -> List[Dict[str, Any]]: ...
    async def create_scan_preset(self, preset_data: Dict[str, Any]) -> Dict[str, Any]: ...
    async def update_scan_preset(self, preset_id: str, preset_data: Dict[str, Any]) -> Dict[str, Any]: ...
    async def delete_scan_preset(self, preset_id: str) -> bool: ...
    async def get_scan_preset_by_id(self, preset_id: str) -> Optional[Dict[str, Any]]: ...
    async def get_market_scan_configuration(self, config_id: UUID) -> Optional[Dict[str, Any]]: ...
    async def upsert_market_scan_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]: ...
    async def delete_market_scan_configuration(self, config_id: UUID) -> bool: ...
    async def list_market_scan_configurations(self) -> List[Dict[str, Any]]: ...


class IMarketDataProvider(Protocol):
    """
    Interfaz para proveedores de datos de mercado.
    """
    async def get_ticker(self, symbol: str) -> TickerData:
        ...

    async def get_klines(self, symbol: str, interval: str) -> List[KlineData]:
        ...

    async def get_all_symbols(self) -> List[str]:
        ...

class IOrderExecutionPort(Protocol):
    """
    Interfaz para el puerto de ejecución de órdenes.
    """
    async def execute_order(self, symbol: str, order_type: str, side: str, quantity: Decimal, price: Optional[Decimal] = None) -> TradeOrderDetails:
        ...

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        ...

class IEventBroker(Protocol):
    """
    Interfaz para el broker de eventos del dominio.
    """
    async def publish(self, event: Any) -> None:
        ...

# Alias táctico para compatibilidad durante la refactorización
IEventPublisher = IEventBroker

class INotificationPort(Protocol):
    """
    Interfaz para el puerto de notificaciones.
    """
    async def send_alert(self, message: str, priority: str) -> None:
        ...

class ITradingEngine(Protocol):
    """
    Interfaz para el motor de trading.
    """
    async def execute_order(self, symbol: str, order_type: str, side: str, quantity: Decimal, price: Optional[Decimal], trading_mode: str, user_id: UUID) -> TradeOrderDetails:
        ...

    async def cancel_order(self, order_id: str, user_id: UUID) -> bool:
        ...

class IPortfolioManager(Protocol):
    """
    Interfaz para el gestor de portafolios.
    """
    async def update_portfolio_snapshot(self, user_id: UUID, trading_mode: str) -> Portfolio:
        ...
    
    async def get_full_portfolio_snapshot(self, user_id: UUID, trading_mode: str) -> PortfolioSnapshot:
        ...


class IAIOrchestrator(Protocol):
    """
    Interfaz para el orquestador de IA.
    """
    async def analyze_opportunity(self, opportunity: TradingOpportunity) -> AIAnalysisResult:
        ...

class IAIModelAdapter(Protocol):
    """
    Interfaz para un adaptador de modelo de IA.
    """
    async def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        ...
    
    def get_metrics(self) -> AISystemMetrics:
        ...
        
    def get_status(self) -> Dict[str, Any]:
        ...

class IAIProvider(Protocol):
    """
    Interfaz para un proveedor de servicios de IA.
    """
    async def generate_analysis(self, prompt: str, context: Dict[str, Any]) -> AIAnalysisResult:
        ...

class IMCPToolHub(Protocol):
    """
    Interfaz para el hub de herramientas MCP.
    """
    async def list_available_tools(self) -> List[dict]:
        ...

    async def execute_tool(self, name: str, parameters: dict) -> ToolExecutionResult:
        ...

class IPromptManager(Protocol):
    """
    Interfaz para el gestor de prompts.
    """
    async def get_prompt(self, name: str) -> str:
        ...

    async def render_prompt(self, template: str, variables: dict) -> str:
        ...

class IPromptRepository(Protocol):
    """
    Interfaz para el repositorio de persistencia de prompts.
    """
    async def get_latest_prompt(self, name: str) -> Optional[PromptTemplate]:
        ...

    async def get_prompt_version(self, name: str, version: int) -> Optional[PromptTemplate]:
        ...

    async def list_prompts(self, category: Optional[str] = None, include_inactive: bool = False) -> List[PromptTemplate]:
        ...

    async def create_prompt_version(self, name: str, template: str, variables: Dict[str, str], description: Optional[str], category: str, creator: str) -> PromptTemplate:
        ...

class ILoggingPort(Protocol):
    """
    Interfaz para el puerto de logging.
    """
    async def log_info(self, message: str, extra: Optional[dict] = None) -> None:
        ...

    async def log_warning(self, message: str, extra: Optional[dict] = None) -> None:
        ...

    async def log_error(self, message: str, extra: Optional[dict] = None) -> None:
        ...

    async def log_debug(self, message: str, extra: Optional[dict] = None) -> None:
        ...

class ICredentialService(Protocol):
    """
    Interfaz para el servicio de gestión de credenciales.
    """
    async def add_credential(self, service_name: ServiceName, credential_label: str, api_key: str, api_secret: Optional[str] = None, other_details: Optional[Dict[str, Any]] = None) -> APICredential:
        ...

    async def get_credential(self, service_name: ServiceName, credential_label: str) -> Optional[APICredential]:
        ...

    async def update_credential(self, credential_id: UUID, api_key: Optional[str] = None, api_secret: Optional[str] = None, other_details: Optional[Dict[str, Any]] = None, status: Optional[str] = None) -> Optional[APICredential]:
        ...

    async def delete_credential(self, credential_id: UUID) -> bool:
        ...

    async def get_decrypted_credential_by_id(self, credential_id: UUID) -> Optional[APICredential]:
        ...

    async def get_first_decrypted_credential_by_service(self, service_name: ServiceName) -> Optional[APICredential]:
        ...

    async def verify_credential(self, credential: APICredential, notification_service: Optional[INotificationPort] = None) -> bool:
        ...

    async def verify_binance_api_key(self) -> bool:
        ...


# Alias táctico para compatibilidad
ICredentialProvider = ICredentialService
