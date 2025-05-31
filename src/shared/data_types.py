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
        use_enum_values=True,  # Para que los enums se serialicen como sus valores de string
        arbitrary_types_allowed=True # Permitir tipos arbitrarios si es necesario
    )

class TelegramConnectionStatus(BaseModel):
    """
    Representa el estado actual de la conexión de Telegram.
    """
    is_connected: bool = Field(..., description="True si la conexión con Telegram está activa y verificada.")
    last_verified_at: Optional[datetime] = Field(None, description="Marca de tiempo de la última verificación exitosa.")
    status_message: str = Field(..., description="Mensaje descriptivo del estado de la conexión (éxito o error).")
    status_code: Optional[str] = Field(None, description="Código de error si la conexión falló.")

class BinanceConnectionStatus(BaseModel):
    """
    Representa el estado actual de la conexión con Binance.
    """
    is_connected: bool = Field(..., description="True si la conexión con Binance está activa y verificada.")
    last_verified_at: Optional[datetime] = Field(None, description="Marca de tiempo de la última verificación exitosa.")
    status_message: str = Field(..., description="Mensaje descriptivo del estado de la conexión (éxito o error).")
    status_code: Optional[str] = Field(None, description="Código de error si la conexión falló.")
    account_permissions: Optional[List[str]] = Field(None, description="Lista de permisos de la API Key de Binance (ej. 'SPOT_TRADING', 'MARGIN_TRADING').")

class AssetBalance(BaseModel):
    """
    Representa el balance de un activo específico en una cuenta.
    """
    asset: str = Field(..., description="Símbolo del activo (ej. 'USDT', 'BTC').")
    free: float = Field(..., description="Cantidad disponible para trading.")
    locked: float = Field(..., description="Cantidad bloqueada en órdenes.")
    total: float = Field(..., description="Cantidad total (free + locked).")

class PortfolioAsset(BaseModel):
    """
    Representa un activo específico poseído en un portafolio (real o paper).
    """
    symbol: str = Field(..., description="Símbolo del activo (ej. 'BTC', 'ETH').")
    quantity: float = Field(..., description="Cantidad del activo poseído.")
    entry_price: Optional[float] = Field(None, description="Precio promedio de entrada del activo.")
    current_price: Optional[float] = Field(None, description="Precio actual de mercado del activo.")
    current_value_usd: Optional[float] = Field(None, description="Valor actual del activo en USD.")
    unrealized_pnl_usd: Optional[float] = Field(None, description="Ganancia/Pérdida no realizada en USD.")
    unrealized_pnl_percentage: Optional[float] = Field(None, description="Ganancia/Pérdida no realizada en porcentaje.")

class PortfolioSummary(BaseModel):
    """
    Representa un resumen del portafolio para un modo específico (paper o real).
    """
    available_balance_usdt: float = Field(..., description="Saldo disponible en USDT.")
    total_assets_value_usd: float = Field(..., description="Valor total de los activos poseídos en USD.")
    total_portfolio_value_usd: float = Field(..., description="Valor total del portafolio (saldo + valor de activos) en USD.")
    assets: List[PortfolioAsset] = Field(default_factory=list, description="Lista de activos poseídos.")
    error_message: Optional[str] = Field(None, description="Mensaje de error si hubo un problema al obtener el resumen.")

class PortfolioSnapshot(BaseModel):
    """
    Contiene el resumen del portafolio para paper trading y real.
    """
    paper_trading: PortfolioSummary = Field(..., description="Resumen del portafolio de Paper Trading.")
    real_trading: PortfolioSummary = Field(..., description="Resumen del portafolio Real.")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Marca de tiempo de la última actualización.")

# Sub-modelos para UserConfiguration
class NotificationPreference(BaseModel):
    eventType: str
    channel: str # 'telegram' | 'ui' | 'email'
    isEnabled: bool
    minConfidence: Optional[float] = None
    minProfitability: Optional[float] = None

class Watchlist(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    pairs: List[str]
    defaultAlertProfileId: Optional[str] = None
    defaultAiAnalysisProfileId: Optional[str] = None

class RiskProfileSettings(BaseModel):
    dailyCapitalRiskPercentage: Optional[float] = None
    perTradeCapitalRiskPercentage: Optional[float] = None
    maxDrawdownPercentage: Optional[float] = None

class RealTradingSettings(BaseModel):
    maxConcurrentOperations: Optional[int] = None
    dailyLossLimitAbsolute: Optional[float] = None
    dailyProfitTargetAbsolute: Optional[float] = None
    assetSpecificStopLoss: Optional[Dict[str, Dict[str, float]]] = None
    autoPauseTradingConditions: Optional[Dict[str, Any]] = None

class AiStrategyConfiguration(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    appliesToStrategies: Optional[List[str]] = None
    appliesToPairs: Optional[List[str]] = None
    geminiModelName: Optional[str] = None # Nombre del modelo Gemini a usar (ej. "gemini-1.5-pro")
    geminiPromptTemplate: Optional[str] = None
    indicatorWeights: Optional[Dict[str, float]] = None
    confidenceThresholds: Optional[Dict[str, float]] = None
    maxContextWindowTokens: Optional[int] = None

class McpServerPreference(BaseModel):
    id: str # Identificador del servidor MCP (ej. "doggybee-ccxt")
    type: str # Tipo de MCP (ej. "ccxt", "web3")
    url: Optional[str] = None
    credentialId: Optional[UUID] = None # Referencia a APICredential.id
    isEnabled: Optional[bool] = None
    queryFrequencySeconds: Optional[int] = None
    reliabilityWeight: Optional[float] = None
    customParameters: Optional[Dict[str, Any]] = None

class DashboardLayoutProfile(BaseModel):
    name: str
    configuration: Any # Estructura específica del layout

class CloudSyncPreferences(BaseModel):
    isEnabled: Optional[bool] = None
    lastSuccessfulSync: Optional[datetime] = None

class UserConfiguration(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID

    # Preferencias de Notificaciones
    telegramChatId: Optional[str] = None
    notificationPreferences: Optional[List[NotificationPreference]] = None
    enableTelegramNotifications: Optional[bool] = True

    # Preferencias de Trading
    defaultPaperTradingCapital: Optional[float] = None
    paperTradingActive: Optional[bool] = False # Estado de activación del modo paper trading
    watchlists: Optional[List[Watchlist]] = None
    favoritePairs: Optional[List[str]] = None
    riskProfile: Optional[str] = None # 'conservative' | 'moderate' | 'aggressive' | 'custom'
    riskProfileSettings: Optional[RiskProfileSettings] = None
    realTradingSettings: Optional[RealTradingSettings] = None

    # Preferencias de IA y Análisis
    aiStrategyConfigurations: Optional[List[AiStrategyConfiguration]] = None
    aiAnalysisConfidenceThresholds: Optional[Dict[str, float]] = None
    mcpServerPreferences: Optional[List[McpServerPreference]] = None

    # Preferencias de UI
    selectedTheme: Optional[str] = 'dark' # 'dark' | 'light'
    dashboardLayoutProfiles: Optional[Dict[str, DashboardLayoutProfile]] = None
    activeDashboardLayoutProfileId: Optional[str] = None
    dashboardLayoutConfig: Optional[Any] = None

    # Configuración de Persistencia y Sincronización
    cloudSyncPreferences: Optional[CloudSyncPreferences] = None

    # Timestamps
    createdAt: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updatedAt: Optional[datetime] = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,  # Permite usar alias para los nombres de campo si es necesario
        arbitrary_types_allowed=True  # Para el campo 'configuration: Any' en DashboardLayoutProfile
    )

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationAction(BaseModel):
    label: str
    actionType: str # Ej. "NAVIGATE", "API_CALL", "DISMISS", "SNOOZE_NOTIFICATION"
    actionValue: Optional[Any] = None # Puede ser string o dict
    requiresConfirmation: Optional[bool] = False
    confirmationMessage: Optional[str] = None

class Notification(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    userId: Optional[UUID] = None

    eventType: str
    channel: str # 'telegram' | 'ui' | 'email'

    titleKey: Optional[str] = None
    messageKey: Optional[str] = None
    messageParams: Optional[Dict[str, Any]] = None
    
    title: str
    message: str

    priority: Optional[NotificationPriority] = NotificationPriority.MEDIUM

    status: str = "new" # 'new' | 'read' | 'archived' | 'error_sending' | 'snoozed' | 'processing_action'
    snoozedUntil: Optional[datetime] = None

    dataPayload: Optional[Dict[str, Any]] = None
    actions: Optional[List[NotificationAction]] = None

    correlationId: Optional[str] = None
    isSummary: Optional[bool] = False
    summarizedNotificationIds: Optional[List[UUID]] = None

    createdAt: datetime = Field(default_factory=datetime.utcnow)
    readAt: Optional[datetime] = None
    sentAt: Optional[datetime] = None

    statusHistory: Optional[List[Dict[str, Any]]] = None # Simplificado para v1.0
    generatedBy: Optional[str] = None

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

# --- Tipos para Oportunidades de Trading ---
class OpportunitySourceType(str, Enum):
    MCP_SIGNAL = "mcp_signal"
    MANUAL_ENTRY = "manual_entry"
    AI_GENERATED = "ai_generated" # Si la IA genera oportunidades directamente
    STRATEGY_TRIGGER = "strategy_trigger" # Si una estrategia predefinida la genera

class OpportunityStatus(str, Enum):
    NEW = "new" # Recién creada, antes de cualquier procesamiento.
    PENDING_AI_ANALYSIS = "pending_ai_analysis"
    AI_ANALYSIS_IN_PROGRESS = "ai_analysis_in_progress"
    AI_ANALYSIS_COMPLETE = "ai_analysis_complete"
    AI_ANALYSIS_FAILED = "ai_analysis_failed"
    REJECTED_BY_AI = "rejected_by_ai"
    PENDING_EXECUTION = "pending_execution" # Aprobada por IA, lista para que el motor de trading la considere
    EXECUTING = "executing" # El motor de trading está intentando ejecutarla
    EXECUTED_PARTIALLY = "executed_partially"
    EXECUTED_FULLY = "executed_fully"
    EXECUTION_FAILED = "execution_failed"
    EXPIRED = "expired" # No se ejecutó a tiempo o ya no es válida
    CANCELLED = "cancelled" # Cancelada manualmente o por el sistema
    COMPLETED_PROFIT = "completed_profit" # Cerrada con ganancia
    COMPLETED_LOSS = "completed_loss" # Cerrada con pérdida
    COMPLETED_BREAKEVEN = "completed_breakeven" # Cerrada en punto de equilibrio

class AIAnalysis(BaseModel):
    calculatedConfidence: Optional[float] = Field(None, description="Nivel de confianza numérico (0.0 a 1.0) de la IA.")
    suggestedAction: Optional[str] = Field(None, description="Dirección sugerida por la IA (ej. 'BUY', 'SELL', 'HOLD', 'REJECT').")
    reasoning_ai: Optional[str] = Field(None, description="Justificación del análisis de la IA.")
    rawAiOutput: Optional[str] = Field(None, description="Salida cruda completa del modelo de IA.")
    dataVerification: Optional[Dict[str, Any]] = Field(None, description="Resultados de la verificación de datos de activos.")
    ai_model_used: Optional[str] = Field(None, description="Nombre del modelo de IA utilizado para el análisis.")

class Opportunity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    
    source_type: OpportunitySourceType
    source_name: Optional[str] = None # Ej. ID del MCP, nombre de la estrategia, "manual"
    source_data: Optional[str] = None # JSON string con los datos originales de la fuente

    status: OpportunityStatus = OpportunityStatus.NEW
    status_reason: Optional[str] = None # Razón para el estado actual (ej. error de análisis)

    # Detalles de la oportunidad (pueden ser llenados por la fuente o por el análisis IA)
    symbol: Optional[str] = None # Ej. "BTC/USDT"
    asset_type: Optional[str] = None # Ej. "SPOT", "FUTURES"
    exchange: Optional[str] = None # Ej. "BINANCE"
    
    # Campos relacionados con la señal/predicción
    predicted_direction: Optional[str] = None # 'UP', 'DOWN', 'SIDEWAYS'
    predicted_price_target: Optional[float] = None
    predicted_stop_loss: Optional[float] = None
    prediction_timeframe: Optional[str] = None # Ej. "1h", "4h", "1d"
    
    # Análisis de IA
    ai_analysis: Optional[AIAnalysis] = None # Objeto AIAnalysis con el resultado del análisis de IA
    confidence_score: Optional[float] = None # 0.0 a 1.0 (redundante si está en ai_analysis, pero se mantiene por compatibilidad)
    suggested_action: Optional[str] = None # Ej. 'BUY', 'SELL', 'HOLD', 'REJECT' (redundante si está en ai_analysis)
    ai_model_used: Optional[str] = None # Ej. "gemini-1.5-pro" (redundante si está en ai_analysis)

    # Detalles de ejecución (si aplica)
    executed_at: Optional[datetime] = None
    executed_price: Optional[float] = None
    executed_quantity: Optional[float] = None
    related_order_id: Optional[str] = None # ID de la orden en el exchange
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None # Si la oportunidad tiene una ventana de validez

    model_config = ConfigDict(use_enum_values=True)

class TradeOrderDetails(BaseModel):
    """
    Detalles de una orden de trading ejecutada o simulada.
    """
    orderId_internal: UUID = Field(default_factory=uuid4, description="ID interno único de la orden.")
    exchangeOrderId: Optional[str] = Field(None, description="ID de la orden en el exchange (si es una orden real).")
    type: str = Field(..., description="Tipo de orden (ej. 'market', 'limit').")
    status: str = Field(..., description="Estado de la orden (ej. 'filled', 'partial_fill', 'new', 'canceled', 'rejected').")
    requestedQuantity: float = Field(..., description="Cantidad solicitada en la orden.")
    executedQuantity: float = Field(..., description="Cantidad ejecutada de la orden.")
    executedPrice: float = Field(..., description="Precio promedio de ejecución de la orden.")
    commission: Optional[float] = Field(None, description="Comisión pagada por la orden.")
    commissionAsset: Optional[str] = Field(None, description="Activo en el que se pagó la comisión.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Marca de tiempo de la ejecución/actualización de la orden.")
    rawResponse: Optional[Dict[str, Any]] = Field(None, description="Respuesta cruda del exchange (para órdenes reales).")

class Trade(BaseModel):
    """
    Representa una operación de trading completa (entrada y salida).
    """
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    
    mode: str = Field(..., description="Modo de trading: 'paper' o 'real'.")
    symbol: str = Field(..., description="Símbolo del par de trading (ej. 'BTCUSDT').")
    side: str = Field(..., description="Dirección de la operación: 'BUY' o 'SELL'.")
    
    entryOrder: TradeOrderDetails = Field(..., description="Detalles de la orden de entrada.")
    exitOrders: List[TradeOrderDetails] = Field(default_factory=list, description="Lista de órdenes de salida (ej. TSL, TP).")
    
    positionStatus: str = Field(..., description="Estado de la posición: 'open', 'closed', 'liquidated'.")
    
    opportunityId: Optional[UUID] = Field(None, description="ID de la oportunidad de trading que originó este trade.")
    aiAnalysisConfidence: Optional[float] = Field(None, description="Confianza de la IA en la oportunidad (si aplica).")
    
    pnl_usd: Optional[float] = Field(None, description="Ganancia o pérdida en USD (para posiciones cerradas).")
    pnl_percentage: Optional[float] = Field(None, description="Ganancia o pérdida en porcentaje (para posiciones cerradas).")
    closingReason: Optional[str] = Field(None, description="Razón del cierre de la posición (ej. 'TP_HIT', 'SL_HIT', 'MANUAL_CLOSE').")

    # Campos para Trailing Stop Loss y Take Profit
    takeProfitPrice: Optional[float] = Field(None, description="Precio objetivo para Take Profit.")
    trailingStopActivationPrice: Optional[float] = Field(None, description="Precio al que se activa el Trailing Stop.")
    trailingStopCallbackRate: Optional[float] = Field(None, description="Porcentaje de retroceso para el Trailing Stop (ej. 0.01 para 1%).")
    currentStopPrice_tsl: Optional[float] = Field(None, description="Precio actual del Trailing Stop Loss.")
    
    # Para registrar ajustes del TSL (opcional, si se desea trazabilidad detallada)
    riskRewardAdjustments: List[Dict[str, Any]] = Field(default_factory=list, description="Historial de ajustes de TSL/TP.")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    opened_at: datetime = Field(default_factory=datetime.utcnow) # Timestamp de la apertura de la posición
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = Field(None, description="Timestamp del cierre de la posición.")

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
