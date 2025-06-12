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
from .domain_models.trading import (
    TickerData, KlineData, Trade, Order, OrderSide, OrderType, Opportunity, TradeResult,
    CommandResult, TradingSignal
)
from .domain_models.portfolio import Portfolio, UserId, PortfolioSnapshot
from .domain_models.market import MarketData
from .domain_models.ai_models import AIAnalysisResult, TradingOpportunity, ToolExecutionResult
from .domain_models.prompt_models import PromptTemplate, PromptVersion
from .domain_models.scan_presets import ScanResult, ScanPreset
from .domain_models.events import BaseEvent
from .domain_models.user_configuration_models import UserConfiguration

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
    async def get_user_configuration(self, user_id: str) -> Optional[UserConfiguration]:
        ...

    async def upsert_user_configuration(self, config: UserConfiguration) -> None:
        ...
    
    async def save_trade(self, trade: Trade) -> None:
        ...

    async def get_portfolio(self, user_id: str, trading_mode: str) -> Optional[Portfolio]:
        ...
        
    async def save_portfolio(self, portfolio: Portfolio) -> None:
        ...

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
    async def execute_order(self, symbol: str, order_type: OrderType, side: OrderSide, quantity: Decimal, price: Optional[Decimal] = None) -> Order:
        ...

    async def cancel_order(self, order_id: str) -> bool:
        ...

class IEventBroker(Protocol):
    """
    Interfaz para el broker de eventos del dominio.
    """
    async def publish(self, event: BaseEvent) -> None:
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
    async def execute_order(self, symbol: str, order_type: OrderType, side: OrderSide, quantity: Decimal, price: Optional[Decimal], trading_mode: str, user_id: UUID) -> Order:
        ...

    async def cancel_order(self, order_id: str, user_id: UUID) -> bool:
        ...

class IPortfolioManager(Protocol):
    """
    Interfaz para el gestor de portafolios.
    """
    async def update_portfolio_snapshot(self, user_id: UUID, trading_mode: str) -> Portfolio:
        ...

class IAIOrchestrator(Protocol):
    """
    Interfaz para el orquestador de IA.
    """
    async def analyze_opportunity(self, opportunity_id: str, market_data: dict) -> AIAnalysisResult:
        ...

class IAIModelAdapter(Protocol):
    """
    Interfaz para un adaptador de modelo de IA.
    """
    async def generate(self, prompt: str, context: Optional[dict] = None) -> dict:
        ...
    
    def get_model_name(self) -> str:
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
    async def add_credential(self, user_id: str, credential_type: str, credential_data: dict) -> None:
        ...

    async def get_credential(self, user_id: str, credential_type: str) -> Optional[dict]:
        ...

# Alias táctico para compatibilidad
ICredentialProvider = ICredentialService
