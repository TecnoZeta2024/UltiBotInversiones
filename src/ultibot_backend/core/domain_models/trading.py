"""
Módulo que define los modelos de dominio puros relacionados con el trading.
Estos modelos son agnósticos a la infraestructura y no deben importar frameworks externos.
Utilizan Pydantic para la validación y serialización de datos.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Any, Dict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

class TradingMode(str, Enum):
    """Define los modos de operación de trading."""
    SIMULATED = "SIMULATED"
    REAL = "REAL"

class TradeId(BaseModel):
    """Identificador único para un trade."""
    value: UUID = Field(default_factory=uuid4)

    model_config = ConfigDict(frozen=True)

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

class OrderStatus(str, Enum):
    """Estado de una orden."""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class TickerData(BaseModel):
    """Datos de un ticker de mercado."""
    symbol: str
    price: Decimal
    volume_24h: Decimal
    price_change_24h: Decimal
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)

class KlineData(BaseModel):
    """Datos de una vela (kline)."""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    model_config = ConfigDict(frozen=True)

class MarketSnapshot(BaseModel):
    """Snapshot de datos de mercado en un momento dado."""
    symbol: str
    timestamp: datetime
    ticker_data: TickerData
    klines: List[KlineData]
    timeframe: str
    indicators: Dict[str, Any]
    volume_data: Dict[str, Any]

    model_config = ConfigDict(frozen=True)

class Order(BaseModel):
    """Representación de una orden de trading."""
    id: UUID = Field(default_factory=uuid4)
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)

class Trade(BaseModel):
    """Representación de un trade ejecutado."""
    id: TradeId = Field(default_factory=TradeId)
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    strategy_id: Optional[str] = None
    order_type: OrderType
    fee: Optional[Decimal] = None
    fee_asset: Optional[str] = None

    model_config = ConfigDict(frozen=True)

class TradeResult(BaseModel):
    """Resultado de una operación de trading."""
    success: bool
    trade_id: Optional[TradeId] = None
    message: Optional[str] = None
    executed_price: Optional[Decimal] = None
    executed_quantity: Optional[Decimal] = None

    model_config = ConfigDict(frozen=True)

class CommandResult(BaseModel):
    """Resultado de la ejecución de un comando."""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None

    model_config = ConfigDict(frozen=True)

class TradingSignal(BaseModel):
    """Señal de trading generada por una estrategia."""
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Optional[Decimal] = None  # Para órdenes límite
    order_type: OrderType
    strategy_name: str
    signal_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)

class StrategyParameters(BaseModel):
    """Base para los parámetros de configuración de una estrategia."""
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(frozen=True)

class AnalysisResult(BaseModel):
    """Resultado del análisis de una estrategia."""
    confidence: Decimal = Field(ge=0, le=1)
    indicators: Dict[str, Any]
    signal: Optional[TradingSignal] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)

class ScanResult(BaseModel):
    """Resultado de un escaneo de mercado."""
    symbol: str
    score: float
    preset: str

    model_config = ConfigDict(frozen=True)

class TradingOpportunity(BaseModel):
    """Representa una oportunidad de trading detectada."""
    symbol: str
    opportunity_type: str
    confidence: Decimal = Field(ge=0, le=1)
    details: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)

class TradingDecision(BaseModel):
    """Representa una decisión de trading tomada por un servicio."""
    decision_id: UUID = Field(default_factory=uuid4)
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    confidence: Decimal = Field(ge=0, le=1)
    rationale: str
    source: str  # e.g., "Strategy:MACD_RSI", "AI_Orchestrator"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)

# Alias táctico para resolver ImportError por refactorización incompleta
Opportunity = TradingOpportunity
