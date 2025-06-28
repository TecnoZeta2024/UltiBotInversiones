"""
Este archivo contendrá definiciones de tipos de datos compartidos,
por ejemplo, modelos Pydantic comunes si la UI los consume directamente
o si hay tipos de datos que tanto el backend como la UI necesitan conocer.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal

# Importar modelos de dominio para mantener una única fuente de verdad
from core.domain_models.trade_models import (
    Trade,
    TradeOrderDetails,
    OrderCategory,
    OrderType, # Añadido para exportar
    OrderStatus, # Añadido para exportar
    PositionStatus, # Añadido para exportar
)
from core.domain_models.user_configuration_models import (
    UserConfiguration,
    RealTradingSettings,
    RiskProfileSettings,
    NotificationPreference,
    Watchlist,
    AIStrategyConfiguration,
    MCPServerPreference,
    DashboardLayoutProfile,
    CloudSyncPreferences,
    ConfidenceThresholds as AIAnalysisConfidenceThresholds,
)
from core.domain_models.opportunity_models import Opportunity, AIAnalysis, OpportunityStatus, SourceType as OpportunitySourceType # Importar Opportunity y AIAnalysis del backend


class Kline(BaseModel):
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_asset_volume: float
    number_of_trades: int
    taker_buy_base_asset_volume: float
    taker_buy_quote_asset_volume: float

class MarketData(BaseModel):
    id: Optional[int] = None
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class Ticker(BaseModel):
    symbol: str
    price: float = Field(..., alias='lastPrice')
    price_change_percent_24h: Optional[float] = Field(default=None, alias='priceChangePercent')
    high_24h: Optional[float] = Field(default=None, alias='highPrice')
    low_24h: Optional[float] = Field(default=None, alias='lowPrice')
    volume_24h: Optional[float] = Field(default=None, alias='volume')
    quote_volume_24h: Optional[float] = Field(default=None, alias='quoteVolume')
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class ServiceName(str, Enum):
    BINANCE_SPOT = "BINANCE_SPOT"
    BINANCE_FUTURES = "BINANCE_FUTURES"
    TELEGRAM_BOT = "TELEGRAM_BOT"
    GEMINI_API = "GEMINI_API"
    MOBULA_API = "MOBULA_API"
    N8N_WEBHOOK = "N8N_WEBHOOK"
    SUPABASE_CLIENT = "SUPABASE_CLIENT"
    MCP_GENERIC = "MCP_GENERIC"
    MCP_DOGGYBEE_CCXT = "MCP_DOGGYBEE_CCXT"
    MCP_METATRADER_BRIDGE = "MCP_METATRADER_BRIDGE"
    MCP_WEB3_RESEARCH = "MCP_WEB3_RESEARCH"
    CUSTOM_SERVICE = "CUSTOM_SERVICE"

class APICredential(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    service_name: ServiceName
    credential_label: str

    encrypted_api_key: str
    encrypted_api_secret: Optional[str] = None
    encrypted_other_details: Optional[str] = None # JSON encriptado para detalles adicionales

    status: str = "verification_pending" # 'active' | 'inactive' | 'revoked' | 'verification_pending' | 'verification_failed' | 'expired'
    last_verified_at: Optional[datetime] = None
    
    permissions: Optional[List[str]] = None
    permissions_checked_at: Optional[datetime] = None

    expires_at: Optional[datetime] = None
    rotation_reminder_policy_days: Optional[int] = None

    usage_count: int = 0
    last_used_at: Optional[datetime] = None

    purpose_description: Optional[str] = None
    tags: Optional[List[str]] = None

    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        use_enum_values=True,
        arbitrary_types_allowed=True
    )

class TelegramConnectionStatus(BaseModel):
    is_connected: bool = Field(..., description="True si la conexión con Telegram está activa y verificada.")
    last_verified_at: Optional[datetime] = Field(None, description="Marca de tiempo de la última verificación exitosa.")
    status_message: str = Field(..., description="Mensaje descriptivo del estado de la conexión (éxito o error).")
    status_code: Optional[str] = Field(None, description="Código de error si la conexión falló.")

class BinanceConnectionStatus(BaseModel):
    is_connected: bool = Field(..., description="True si la conexión con Binance está activa y verificada.")
    last_verified_at: Optional[datetime] = Field(None, description="Marca de tiempo de la última verificación exitosa.")
    status_message: str = Field(..., description="Mensaje descriptivo del estado de la conexión (éxito o error).")
    status_code: Optional[str] = Field(None, description="Código de error si la conexión falló.")
    account_permissions: Optional[List[str]] = Field(None, description="Lista de permisos de la API Key de Binance (ej. 'SPOT_TRADING', 'MARGIN_TRADING').")

class AssetBalance(BaseModel):
    asset: str = Field(..., description="Símbolo del activo (ej. 'USDT', 'BTC').")
    free: Decimal = Field(..., description="Cantidad disponible para trading.")
    locked: Decimal = Field(..., description="Cantidad bloqueada en órdenes.")
    total: Decimal = Field(..., description="Cantidad total (free + locked).")

class PortfolioAsset(BaseModel):
    symbol: str = Field(..., description="Símbolo del activo (ej. 'BTC', 'ETH').")
    quantity: Decimal = Field(..., description="Cantidad del activo poseído.")
    entry_price: Optional[Decimal] = Field(None, description="Precio promedio de entrada del activo.")
    current_price: Optional[Decimal] = Field(None, description="Precio actual de mercado del activo.")
    current_value_usd: Optional[Decimal] = Field(None, description="Valor actual del activo en USD.")
    unrealized_pnl_usd: Optional[Decimal] = Field(None, description="Ganancia/Pérdida no realizada en USD.")
    unrealized_pnl_percentage: Optional[Decimal] = Field(None, description="Ganancia/Pérdida no realizada en porcentaje.")

class PortfolioSummary(BaseModel):
    available_balance_usdt: Decimal = Field(..., description="Saldo disponible en USDT.")
    total_assets_value_usd: Decimal = Field(..., description="Valor total de los activos poseídos en USD.")
    total_portfolio_value_usd: Decimal = Field(..., description="Valor total del portafolio (saldo + valor de activos) en USD.")
    assets: List[PortfolioAsset] = Field(default_factory=list, description="Lista de activos poseídos.")
    error_message: Optional[str] = Field(None, description="Mensaje de error si hubo un problema al obtener el resumen.")

class PortfolioSnapshot(BaseModel):
    paper_trading: PortfolioSummary = Field(..., description="Resumen del portafolio de Paper Trading.")
    real_trading: PortfolioSummary = Field(..., description="Resumen del portafolio Real.")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Marca de tiempo de la última actualización.")

# The classes previously defined here are now imported from the core domain models
# to ensure a single source of truth.

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationAction(BaseModel):
    label: str
    actionType: str
    actionValue: Optional[Any] = None
    requiresConfirmation: Optional[bool] = False
    confirmationMessage: Optional[str] = None

class Notification(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    userId: Optional[UUID] = None
    eventType: str
    channel: str
    titleKey: Optional[str] = None
    messageKey: Optional[str] = None
    messageParams: Optional[Dict[str, Any]] = None
    title: str
    message: str
    priority: Optional[NotificationPriority] = NotificationPriority.MEDIUM
    status: str = "new"
    snoozedUntil: Optional[datetime] = None
    dataPayload: Optional[Dict[str, Any]] = None
    actions: Optional[List[NotificationAction]] = None
    correlationId: Optional[str] = None
    isSummary: Optional[bool] = False
    summarizedNotificationIds: Optional[List[UUID]] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    readAt: Optional[datetime] = None
    sentAt: Optional[datetime] = None
    statusHistory: Optional[List[Dict[str, Any]]] = None
    generatedBy: Optional[str] = None

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class PerformanceMetrics(BaseModel):
    total_trades: int = Field(0, description="Número total de operaciones cerradas")
    winning_trades: int = Field(0, description="Número de operaciones con ganancia")
    losing_trades: int = Field(0, description="Número de operaciones con pérdida")
    win_rate: Decimal = Field(Decimal("0.0"), description="Porcentaje de operaciones ganadoras sobre el total (excluyendo break-even)")
    total_pnl: Decimal = Field(Decimal("0.0"), description="Ganancia/Pérdida neta total")
    avg_pnl_per_trade: Decimal = Field(Decimal("0.0"), description="Ganancia/Pérdida promedio por operación")
    best_trade_pnl: Decimal = Field(Decimal("0.0"), description="PnL de la mejor operación")
    worst_trade_pnl: Decimal = Field(Decimal("0.0"), description="PnL de la peor operación")
    best_trade_symbol: Optional[str] = Field(None, description="Símbolo de la mejor operación")
    worst_trade_symbol: Optional[str] = Field(None, description="Símbolo de la peor operación")
    period_start: Optional[datetime] = Field(None, description="Fecha de inicio del periodo analizado")
    period_end: Optional[datetime] = Field(None, description="Fecha de fin del periodo analizado")
    total_volume_traded: Decimal = Field(Decimal("0.0"), description="Volumen total operado (en USDT)")

    model_config = ConfigDict(
        populate_by_name=True
    )

class ConfirmRealTradeRequest(BaseModel):
    opportunity_id: UUID = Field(..., description="ID de la oportunidad de trading a confirmar.")
    user_id: UUID = Field(..., description="ID del usuario que confirma la operación.")

class CapitalManagementStatus(BaseModel):
    total_capital_usd: float = Field(0.0, description="Capital total gestionado en USD.")
    available_for_new_trades_usd: float = Field(0.0, description="Capital disponible para nuevas operaciones.")
    daily_capital_committed_usd: float = Field(0.0, description="Capital ya comprometido en el día actual.")
    daily_capital_limit_usd: float = Field(0.0, description="Límite de capital diario que se puede arriesgar.")
    high_risk_positions_count: int = Field(0, description="Número de posiciones consideradas de alto riesgo.")

# Exportar los modelos de dominio para que otros módulos puedan usarlos
__all__ = [
    "Trade",
    "TradeOrderDetails",
    "OrderCategory",
    "OrderType",
    "OrderStatus",
    "PositionStatus",
    "Kline",
    "MarketData",
    "Ticker",
    "ServiceName",
    "APICredential",
    "TelegramConnectionStatus",
    "BinanceConnectionStatus",
    "AssetBalance",
    "PortfolioAsset",
    "PortfolioSummary",
    "PortfolioSnapshot",
    "NotificationPreference",
    "Watchlist",
    "RiskProfileSettings",
    "RealTradingSettings",
    "AIAnalysisConfidenceThresholds",
    "AIStrategyConfiguration",
    "MCPServerPreference",
    "DashboardLayoutProfile",
    "CloudSyncPreferences",
    "UserConfiguration",
    "NotificationPriority",
    "NotificationAction",
    "Notification",
    "OpportunitySourceType",
    "AIAnalysis",
    "Opportunity", # Exportar Opportunity del backend
    "PerformanceMetrics",
    "ConfirmRealTradeRequest",
    "CapitalManagementStatus",
]
