"""
Módulo que define los modelos de datos utilizados por la interfaz de usuario.
Estos modelos reflejan las estructuras de datos del backend para asegurar la coherencia
en la comunicación entre el frontend y el backend.
"""

from PyQt6.QtCore import QObject
import asyncio
from typing import Callable, Coroutine, Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

# Modelos de dominio puros (reflejan los del backend para tipado)

class TradeId(QObject):
    """Identificador único para un trade."""
    def __init__(self, value: UUID = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._value = value if value is not None else uuid4()

    @property
    def value(self) -> UUID:
        return self._value

    def __str__(self) -> str:
        return str(self._value)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TradeId):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)

class OrderSide(str, Enum):
    """Lado de la orden (compra o venta)."""
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    """Tipo de orden (mercado, límite, etc.)."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"

class TickerData(QObject):
    """Datos de un ticker de mercado."""
    def __init__(self, symbol: str, price: Decimal, volume_24h: Decimal, price_change_24h: Decimal, timestamp: datetime = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.symbol = symbol
        self.price = price
        self.volume_24h = volume_24h
        self.price_change_24h = price_change_24h
        self.timestamp = timestamp if timestamp is not None else datetime.utcnow()

class KlineData(QObject):
    """Datos de una vela (kline)."""
    def __init__(self, timestamp: datetime, open: Decimal, high: Decimal, low: Decimal, close: Decimal, volume: Decimal, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

class Trade(QObject):
    """Representación de un trade ejecutado."""
    def __init__(self, id: TradeId, symbol: str, side: OrderSide, quantity: Decimal, price: Decimal, timestamp: datetime, order_type: OrderType, strategy_id: Optional[str] = None, fee: Optional[Decimal] = None, fee_asset: Optional[str] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.id = id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp
        self.strategy_id = strategy_id
        self.order_type = order_type
        self.fee = fee
        self.fee_asset = fee_asset

class Portfolio(QObject):
    """Representa el portfolio de un usuario."""
    def __init__(self, user_id: UUID, balances: Dict[str, Decimal], total_value_usd: Decimal, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.balances = balances
        self.total_value_usd = total_value_usd

class Opportunity(QObject):
    """Representa una oportunidad de trading detectada."""
    def __init__(self, symbol: str, opportunity_type: str, confidence: Decimal, details: Dict[str, Any], timestamp: datetime = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.symbol = symbol
        self.opportunity_type = opportunity_type
        self.confidence = confidence
        self.details = details
        self.timestamp = timestamp if timestamp is not None else datetime.utcnow()

class TradeResult(QObject):
    """Resultado de una operación de trading."""
    def __init__(self, success: bool, trade_id: Optional[TradeId] = None, message: Optional[str] = None, executed_price: Optional[Decimal] = None, executed_quantity: Optional[Decimal] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.success = success
        self.trade_id = trade_id
        self.message = message
        self.executed_price = executed_price
        self.executed_quantity = executed_quantity

class CommandResult(QObject):
    """Resultado de la ejecución de un comando."""
    def __init__(self, success: bool, message: Optional[str] = None, data: Optional[Any] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.success = success
        self.message = message
        self.data = data

class TradingSignal(QObject):
    """Señal de trading generada por una estrategia."""
    def __init__(self, symbol: str, side: OrderSide, quantity: Decimal, order_type: OrderType, strategy_name: str, price: Optional[Decimal] = None, signal_id: UUID = None, timestamp: datetime = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.price = price
        self.order_type = order_type
        self.strategy_name = strategy_name
        self.signal_id = signal_id if signal_id is not None else uuid4()
        self.timestamp = timestamp if timestamp is not None else datetime.utcnow()

class StrategyParameters(QObject):
    """Base para los parámetros de configuración de una estrategia."""
    def __init__(self, name: str, description: Optional[str] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.name = name
        self.description = description

class AnalysisResult(QObject):
    """Resultado del análisis de una estrategia."""
    def __init__(self, confidence: Decimal, indicators: Dict[str, Any], signal: Optional[TradingSignal] = None, timestamp: datetime = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.confidence = confidence
        self.indicators = indicators
        self.signal = signal
        self.timestamp = timestamp if timestamp is not None else datetime.utcnow()

class MarketSnapshot(QObject):
    """
    Representa una instantánea del estado actual del mercado para un símbolo dado.
    Contiene los datos más recientes del ticker y las velas.
    """
    def __init__(self, symbol: str, ticker: TickerData, klines: List[KlineData], timestamp: datetime = None, additional_data: Dict[str, Any] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.symbol = symbol
        self.ticker = ticker
        self.klines = klines
        self.timestamp = timestamp if timestamp is not None else datetime.utcnow()
        self.additional_data = additional_data if additional_data is not None else {}

class PromptTemplateModel(QObject):
    """Modelo para templates de prompts del AI Studio."""
    def __init__(self, name: str, template: str, variables: Dict[str, Any] = None, 
                 description: str = "", category: str = "general", version: int = 1,
                 is_active: bool = True, created_at: datetime = None, updated_at: datetime = None,
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self.name = name
        self.template = template
        self.variables = variables if variables is not None else {}
        self.description = description
        self.category = category
        self.version = version
        self.is_active = is_active
        self.created_at = created_at if created_at is not None else datetime.utcnow()
        self.updated_at = updated_at if updated_at is not None else datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario."""
        return {
            "name": self.name,
            "template": self.template,
            "variables": self.variables,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplateModel':
        """Crea el modelo desde un diccionario."""
        created_at = None
        updated_at = None
        
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
            except:
                pass
        
        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
            except:
                pass
        
        return cls(
            name=data.get("name", ""),
            template=data.get("template", ""),
            variables=data.get("variables", {}),
            description=data.get("description", ""),
            category=data.get("category", "general"),
            version=data.get("version", 1),
            is_active=data.get("is_active", True),
            created_at=created_at,
            updated_at=updated_at
        )

class PromptVersionModel(QObject):
    """Modelo para versiones de prompts."""
    def __init__(self, prompt_name: str, version: int, template: str, 
                 variables: Dict[str, Any] = None, is_active: bool = False,
                 created_at: datetime = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.prompt_name = prompt_name
        self.version = version
        self.template = template
        self.variables = variables if variables is not None else {}
        self.is_active = is_active
        self.created_at = created_at if created_at is not None else datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario."""
        return {
            "prompt_name": self.prompt_name,
            "version": self.version,
            "template": self.template,
            "variables": self.variables,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptVersionModel':
        """Crea el modelo desde un diccionario."""
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
            except:
                pass
        
        return cls(
            prompt_name=data.get("prompt_name", ""),
            version=data.get("version", 1),
            template=data.get("template", ""),
            variables=data.get("variables", {}),
            is_active=data.get("is_active", False),
            created_at=created_at
        )

class PromptRenderResultModel(QObject):
    """Modelo para resultados de renderizado de prompts."""
    def __init__(self, content: str, variables_used: Dict[str, Any] = None,
                 render_time: float = 0.0, success: bool = True, 
                 error_message: str = "", parent: Optional[QObject] = None):
        super().__init__(parent)
        self.content = content
        self.variables_used = variables_used if variables_used is not None else {}
        self.render_time = render_time
        self.success = success
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario."""
        return {
            "content": self.content,
            "variables_used": self.variables_used,
            "render_time": self.render_time,
            "success": self.success,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptRenderResultModel':
        """Crea el modelo desde un diccionario."""
        return cls(
            content=data.get("content", ""),
            variables_used=data.get("variables_used", {}),
            render_time=data.get("render_time", 0.0),
            success=data.get("success", True),
            error_message=data.get("error_message", "")
        )

class AIStudioStateModel(QObject):
    """Modelo para el estado interno del AI Studio."""
    def __init__(self, current_prompt: Optional[PromptTemplateModel] = None,
                 selected_category: str = "all", search_query: str = "",
                 is_editing: bool = False, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.current_prompt = current_prompt
        self.selected_category = selected_category
        self.search_query = search_query
        self.is_editing = is_editing

class BaseMainWindow(QObject):
    """
    Clase base para type hinting de MainWindow y evitar importaciones circulares.
    Define la interfaz esperada que otros componentes pueden usar.
    """
    def submit_task(self, coro: Coroutine, on_success: Callable, on_error: Callable):
        """
        Envía una corutina para ser ejecutada en el pool de hilos.

        Args:
            coro: La corutina a ejecutar.
            on_success: Callback a ejecutar en caso de éxito. Recibe el futuro completado.
            on_error: Callback a ejecutar en caso de error. Recibe el futuro completado.
        """
        raise NotImplementedError

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """
        Retorna el bucle de eventos de asyncio en uso.
        """
        raise NotImplementedError
