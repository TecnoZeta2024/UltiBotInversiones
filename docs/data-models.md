## Data Models

### Core Application Entities / Domain Objects

#### UserConfiguration

// Entidad: UserConfiguration
export interface UserConfiguration {
  id: string; // Identificador único para el registro de configuración del usuario (PK)
  userId: string; // Identificador del usuario (podría ser un valor fijo para v1 local)

  // --- Preferencias de Notificaciones ---
  telegramChatId?: string; // ID del chat de Telegram para notificaciones
  notificationPreferences?: Array<{
    eventType: string; // Ej: "REAL_TRADE_EXECUTED", "PAPER_OPPORTUNITY_HIGH_CONFIDENCE", "MCP_SIGNAL_RECEIVED", "DAILY_SUMMARY"
    channel: 'telegram' | 'ui' | 'email'; // 'email' como futura expansión
    isEnabled: boolean;
    minConfidence?: number; // Para eventos de oportunidad/señal
    minProfitability?: number; // Para eventos de oportunidad
  }>;
  enableTelegramNotifications?: boolean; // Mantener para simplicidad inicial o como master switch

  // --- Preferencias de Trading ---
  defaultPaperTradingCapital?: number; // Capital inicial por defecto para el modo paper trading
  
  watchlists?: Array<{
    id: string; // Identificador único de la lista de observación
    name: string; // Ej: "Volátiles Alto Riesgo", "Proyectos DeFi Nuevos", "Arbitraje BTC-ETH"
    pairs: string[]; // Pares de esta lista
    defaultAlertProfileId?: string; // Enlace a un perfil de alertas específico
    defaultAiAnalysisProfileId?: string; // Enlace a un perfil de análisis de IA específico para esta lista
  }>;
  favoritePairs?: string[]; // Lista de pares de criptomonedas favoritos (podría migrarse a una watchlist default o ser deprecado)

  riskProfile?: 'conservative' | 'moderate' | 'aggressive' | 'custom'; // Perfil de riesgo general
  riskProfileSettings?: {
    dailyCapitalRiskPercentage?: number; // Porcentaje máximo del capital total a arriesgar en un día
    perTradeCapitalRiskPercentage?: number; // Porcentaje máximo del capital a arriesgar por operación
    maxDrawdownPercentage?: number; // Límite de pérdida total antes de una pausa automática, por ejemplo
  };
  
  realTradingSettings?: {
    maxConcurrentOperations?: number; // Límite de operaciones concurrentes en modo real
    dailyLossLimitAbsolute?: number; // Límite de pérdida diaria en la moneda base (ej. USDT)
    dailyProfitTargetAbsolute?: number; // Objetivo de ganancia diaria en la moneda base (ej. USDT)
    assetSpecificStopLoss?: Record<string, { percentage?: number; absolute?: number; }>; // Ej: {"BTC/USDT": { percentage: 0.02 }}
    autoPauseTradingConditions?: {
      onMaxDailyLossReached?: boolean;
      onMaxDrawdownReached?: boolean;
      onConsecutiveLosses?: number; // Pausar después de X pérdidas consecutivas
      onMarketVolatilityIndexExceeded?: {
        source: string; // ej. "VIX_CRYPTO_MCP"
        threshold: number;
      };
    };
  };

  // --- Preferencias de IA y Análisis ---
  aiStrategyConfigurations?: Array<{
    id: string; // Identificador del perfil de estrategia de IA
    name: string; // Ej: "Scalping Agresivo BTC", "Day Trading ETH Conservador"
    appliesToStrategies?: string[]; // Nombres de estrategias de trading a las que aplica (ej. ["scalping", "momentum_trading"])
    appliesToPairs?: string[]; // Opcional: solo aplicar a ciertos pares.
    geminiPromptTemplate?: string; // Plantilla de prompt específica para esta configuración
    indicatorWeights?: Record<string, number>; // Ponderación de indicadores: {"RSI": 0.7, "MACD_Signal": 0.5}
    confidenceThresholds?: { // Umbrales específicos para esta configuración de IA
      paperTrading?: number; 
      realTrading?: number;  
    };
    maxContextWindowTokens?: number; // Límite de tokens para el contexto de esta estrategia
  }>;
  // Fallback general si no hay configuración específica de aiStrategyConfigurations
  aiAnalysisConfidenceThresholds?: { 
    paperTrading?: number; 
    realTrading?: number;
  };

  mcpServerPreferences?: Array<{
    id: string; // Identificador del servidor MCP (ej. "doggybee-ccxt", "web3-research-mainnet")
    type: string; // Tipo de MCP (ej. "ccxt", "web3", "sentiment_analysis")
    url?: string; // URL si es configurable
    apiKey?: string; // Si el MCP requiere una API key específica del usuario (almacenar de forma segura)
    isEnabled?: boolean;
    queryFrequencySeconds?: number; // Frecuencia de consulta si aplica
    reliabilityWeight?: number; // Ponderación de 0 a 1 para la IA al considerar señales de este MCP
    customParameters?: Record<string, any>; // Parámetros específicos del MCP
  }>;

  // --- Preferencias de UI ---
  selectedTheme?: 'dark' | 'light'; // Tema de la interfaz de usuario
  
  dashboardLayoutProfiles?: Record<string, {
    name: string;
    configuration: any; // Estructura específica del layout
  }>;
  activeDashboardLayoutProfileId?: string; // ID del perfil de layout activo
  dashboardLayoutConfig?: any; // Layout por defecto o último usado si no hay perfiles

  // --- Configuración de Persistencia y Sincronización ---
  cloudSyncPreferences?: {
    isEnabled?: boolean;
    lastSuccessfulSync?: Date;
  };

  // Timestamps
  createdAt?: Date;
  updatedAt?: Date;
}

#### Notification 

// Entidad: Notification
export interface Notification {
  id: string; // Identificador único de la notificación (PK)
  
  userId?: string; // Identificador del usuario (opcional para notificaciones globales)

  eventType: string; // Tipo de evento (ej. "REAL_TRADE_EXECUTED", "OPPORTUNITY_ANALYZED", "SYSTEM_MAINTENANCE")
  channel: 'telegram' | 'ui' | 'email'; // Canal

  // Para Internacionalización (Opción con claves de traducción)
  titleKey?: string; // Ej: "notification.tradeExecuted.title"
  messageKey?: string; // Ej: "notification.tradeExecuted.message"
  messageParams?: Record<string, any>; // Parámetros para la plantilla: { symbol: "BTC/USDT", pnl: "25.50" }
  
  title: string; // Título breve (fallback si titleKey no se resuelve o para idioma por defecto)
  message: string; // Contenido del mensaje (fallback si messageKey no se resuelve o para idioma por defecto)

  priority?: 'low' | 'medium' | 'high' | 'critical';

  status: 
    | 'new' 
    | 'read' 
    | 'archived' 
    | 'error_sending'
    | 'snoozed' // Notificación pospuesta
    | 'processing_action'; // Acción en curso
  snoozedUntil?: Date; // Fecha hasta la que está pospuesta

  dataPayload?: Record<string, any>; // Datos contextuales del evento. Esquemas recomendados por eventType en la lógica de negocio.

  actions?: Array<{
    label: string;
    actionType: string; // Ej. "NAVIGATE", "API_CALL", "DISMISS", "SNOOZE_NOTIFICATION"
    actionValue?: string | Record<string, any>;
    requiresConfirmation?: boolean; // True si la acción es crítica
    confirmationMessage?: string; // Mensaje para el diálogo de confirmación
  }>;

  correlationId?: string; // Para agrupar notificaciones relacionadas

  isSummary?: boolean; // True si esta notificación resume otras
  summarizedNotificationIds?: string[]; // IDs de las notificaciones resumidas

  createdAt: Date;
  readAt?: Date;
  sentAt?: Date;

  // Opcional para auditoría detallada
  statusHistory?: Array<{
    status: string;
    changedAt: Date;
    changedBy?: 'user' | 'system' | string; 
    notes?: string;
  }>;
  generatedBy?: string; // Módulo/proceso que generó la notificación
}

#### APICredential 

// Entidad: APICredential

export enum ServiceName {
  BINANCE_SPOT = "BINANCE_SPOT",
  BINANCE_FUTURES = "BINANCE_FUTURES",
  TELEGRAM_BOT = "TELEGRAM_BOT",
  GEMINI_API = "GEMINI_API",
  MOBULA_API = "MOBULA_API",
  N8N_WEBHOOK = "N8N_WEBHOOK",
  SUPABASE_CLIENT = "SUPABASE_CLIENT",
  MCP_GENERIC = "MCP_GENERIC",
  MCP_DOGGYBEE_CCXT = "MCP_DOGGYBEE_CCXT",
  MCP_METATRADER_BRIDGE = "MCP_METATRADER_BRIDGE",
  MCP_WEB3_RESEARCH = "MCP_WEB3_RESEARCH",
  CUSTOM_SERVICE = "CUSTOM_SERVICE"
}

export interface APICredential {
  id: string; // Identificador único de la credencial (PK)
  userId: string; // Identificador del usuario

  serviceName: ServiceName | string; // Nombre del servicio
  credentialLabel?: string; // Etiqueta definida por el usuario

  // Campos encriptados
  encryptedApiKey: string; 
  encryptedApiSecret?: string;
  encryptedOtherDetails?: string; // JSON encriptado para detalles adicionales

  status: 'active' | 'inactive' | 'revoked' | 'verification_pending' | 'verification_failed' | 'expired';
  lastVerifiedAt?: Date;
  
  permissions?: string[]; // Permisos de la API Key (ej. ["readOnly", "enableSpotTrading"])
  permissionsCheckedAt?: Date; // Cuándo se verificaron los permisos

  expiresAt?: Date; // Fecha de expiración de la clave API
  rotationReminderPolicyDays?: number; // Días antes de expiresAt para un recordatorio

  usageCount?: number; // Contador de uso
  lastUsedAt?: Date; // Fecha del último uso exitoso

  purposeDescription?: string; // Descripción del propósito
  tags?: string[]; // Etiquetas para organizar/filtrar

  notes?: string; // Notas opcionales del usuario

  createdAt: Date;
  updatedAt: Date;
}

#### TradeOrderDetails

// Entidad: TradeOrderDetails
export interface TradeOrderDetails {
  orderId_internal: string; 
  orderId_exchange?: string; 
  clientOrderId_exchange?: string;
  type: 'market' | 'limit' | 'stop_loss' | 'take_profit' | 'trailing_stop_loss' | 'manual_close' | 'oco' | 'conditional_entry';
  status: 
    | 'new' 
    | 'pending_submit' 
    | 'submitted' 
    | 'pending_open' 
    | 'open' 
    | 'partially_filled'
    | 'filled'
    | 'pending_cancel'
    | 'cancelling'
    | 'cancelled'
    | 'rejected'
    | 'expired'
    | 'triggered'
    | 'error_submission';
  exchangeStatusRaw?: string; // Estado original devuelto por el exchange
  rejectionReasonCode?: string;
  rejectionReasonMessage?: string;

  requestedPrice?: number;
  stopPrice?: number; 
  executedPrice?: number; // Precio promedio de ejecución
  
  slippageAmount?: number;
  slippagePercentage?: number;

  requestedQuantity: number;
  executedQuantity?: number;
  cumulativeQuoteQty?: number;

  commissions?: Array<{
    amount: number;
    asset: string;
    timestamp?: Date;
  }>;

  timestamp: Date; // Creación de la orden en nuestro sistema
  submittedAt?: Date; // Cuándo se envió al exchange
  lastUpdateTimestamp?: Date; // Última actualización desde el exchange
  fillTimestamp?: Date; // Cuándo se completó (totalmente)

  trailingStopActivationPrice?: number;
  trailingStopCallbackRate?: number;
  currentStopPrice_tsl?: number;

  ocoGroupId_exchange?: string; 
  // linkedOrderIds_internal?: string[]; 
  // conditionDefinition?: Record<string, any>; 
}

#### Trade

// Entidad: Trade
export interface Trade {
  id: string; 
  userId: string; 
  mode: 'paper' | 'real' | 'backtest';

  symbol: string; 
  side: 'buy' | 'sell'; 
  
  strategyId?: string; 
  opportunityId?: string; 
  aiAnalysisConfidence?: number; 

  strategyExecutionInstanceId?: string; // Para agrupar Trades (ej. DCA, grid)
  // sequenceInStrategy?: number; 

  positionStatus: 'opening' | 'open' | 'partially_closed' | 'closing' | 'closed' | 'error' | 'pending_entry_conditions';

  entryOrder: TradeOrderDetails; 
  exitOrders?: TradeOrderDetails[]; 
  // adjustmentOrders?: TradeOrderDetails[];

  initialRiskQuoteAmount?: number; // Riesgo inicial en moneda de cotización
  initialRewardToRiskRatio?: number; 
  riskRewardAdjustments?: Array<{
    timestamp: Date;
    newStopLossPrice?: number;
    newTakeProfitPrice?: number;
    updatedRiskQuoteAmount?: number;
    updatedRewardToRiskRatio?: number;
    reason?: string; 
  }>;
  currentRiskQuoteAmount?: number; 
  currentRewardToRiskRatio?: number; 

  pnl?: number; 
  pnlPercentage?: number;
  closingReason?: string; 

  marketContextSnapshots?: {
    onEntry?: Record<string, any>; 
    onExit?: Record<string, any>; 
  };

  externalEventOrAnalysisLink?: {
    type: 'news_event' | 'custom_analysis_note' | 'mcp_signal_detail';
    referenceId?: string; 
    description?: string; 
  };

  backtestDetails?: {
    backtestRunId: string; 
    iterationId?: string; 
    parametersSnapshot: Record<string, any>; 
  };

  notes?: string; 
  createdAt: Date; 
  openedAt?: Date; 
  closedAt?: Date; 
  updatedAt: Date; 
}

#### AssetHolding (para PortfolioSnapshot)

// Entidad: AssetHolding (para PortfolioSnapshot)
export interface AssetHolding {
  assetSymbol: string; 
  quantity: number; 
  lockedQuantity?: number;

  averageBuyPrice?: number; // Mantenido para simplicidad
  taxLots?: Array<{ // Opcional: Para cálculos fiscales o P&L detallado por lote
    purchaseDate: Date;
    purchasePrice: number;
    quantity: number;
    // originalTradeId?: string; 
  }>;
  
  currentMarketPrice?: number;
  currentValue_quoteCurrency?: number; // Calculado en la primaryQuoteCurrency del Snapshot
  unrealizedPnl_quoteCurrency?: number; // Calculado en la primaryQuoteCurrency del Snapshot

  assetCategory?: string; // Ej. "Layer 1", "DeFi", (de Mobula o config. usuario)
  userDefinedRiskRating?: 1 | 2 | 3 | 4 | 5;
  // sourceExchange?: string; // Si el portafolio es multi-exchange
}

#### DerivativePositionHolding

// Entidad: DerivativePositionHolding (para PortfolioSnapshot)
export interface DerivativePositionHolding {
  id: string; // Identificador único de la posición derivada
  assetSymbol: string; // Símbolo del subyacente (ej. "BTCUSDT Perpetual")
  positionType: 'future' | 'option';
  side: 'long' | 'short';
  quantity: number; // Tamaño de la posición (ej. número de contratos)
  entryPrice: number;
  currentMarkPrice: number;
  liquidationPrice?: number;
  leverage?: number;
  marginUsed_quoteCurrency?: number; // En la primaryQuoteCurrency del Snapshot
  unrealizedPnl_quoteCurrency?: number; // En la primaryQuoteCurrency del Snapshot
  realizedPnl_quoteCurrency?: number; // P&L realizado en esta posición si se cierra parcialmente
  expiryDate?: Date;
  optionType?: 'call' | 'put';
  strikePrice?: number;
  // fundingRate?: number;
  // initialMargin_quoteCurrency?: number;
}

#### PortfolioSnapshot

// Entidad: PortfolioSnapshot
export interface PortfolioSnapshot {
  id: string; 
  userId: string; 
  timestamp: Date;
  mode: 'paper' | 'real' | 'backtest'; 

  primaryQuoteCurrency: string; // Ej. "USDT", "USD". Todos los valores monetarios se expresan aquí.

  totalPortfolioValue: number; // Valor total en primaryQuoteCurrency
  totalCashBalance: number; // Suma de cashBalances convertidos a primaryQuoteCurrency
  totalSpotAssetsValue: number; // Suma de AssetHoldings en primaryQuoteCurrency
  totalDerivativesValue?: number; // Valor de posiciones de derivados en primaryQuoteCurrency
  
  cashConversionRatesUsed?: Record<string, number>; // Tasas usadas para convertir a primaryQuoteCurrency
  cashBalances: Array<{ 
    assetSymbol: string; 
    amount: number;
    // valueInPrimaryQuoteCurrency?: number;
  }>;
  assetHoldings: AssetHolding[];
  derivativePositionHoldings?: DerivativePositionHolding[];

  capitalInflowSinceLastSnapshot?: number; // En primaryQuoteCurrency
  capitalOutflowSinceLastSnapshot?: number; // En primaryQuoteCurrency
  // capitalFlows?: Array<{ type: 'deposit' | 'withdrawal', amount: number, currency: string, timestamp: Date }>;

  cumulativePnl?: number; 
  cumulativePnlPercentage?: number; 
  pnlSinceLastSnapshot?: number;
  
  sharpeRatioPeriod?: number;
  sortinoRatioPeriod?: number;
  maxDrawdownPeriodPercentage?: number;
  // volatilityPeriodPercentage?: number;

  totalValueInOpenSpotPositions?: number; // Valor en órdenes de spot abiertas
  
  source: 'scheduled_daily' | 'after_trade_close' | 'user_request' | 'initial_setup' | 'capital_flow_event';
  snapshotType?: 'actual_historical' | 'projected_forecast' | 'simulated_what_if' | 'backtest_result';

  targetAssetAllocation?: Record<string, number>; // Ej. {"BTC": 0.4, "ETH": 0.3}

  notes?: string; 
  createdAt: Date; 
}

#### TradingStrategyConfig

// Entidad: TradingStrategyConfig

export enum BaseStrategyType {
  SCALPING = "SCALPING",
  DAY_TRADING = "DAY_TRADING",
  SWING_TRADING = "SWING_TRADING",
  ARBITRAGE_SIMPLE = "ARBITRAGE_SIMPLE",
  ARBITRAGE_TRIANGULAR = "ARBITRAGE_TRIANGULAR",
  GRID_TRADING = "GRID_TRADING",
  DCA_INVESTING = "DCA_INVESTING", // Dollar Cost Averaging
  CUSTOM_AI_DRIVEN = "CUSTOM_AI_DRIVEN",
  MCP_SIGNAL_FOLLOWER = "MCP_SIGNAL_FOLLOWER",
}

export interface ScalpingParameters {
  profitTargetPercentage: number;
  stopLossPercentage: number;
  maxHoldingTimeSeconds?: number;
  leverage?: number;
}

export interface DayTradingParameters {
  rsiPeriod?: number;
  rsiOverbought?: number;
  rsiOversold?: number;
  macdFastPeriod?: number;
  macdSlowPeriod?: number;
  macdSignalPeriod?: number;
  entryTimeframes: string[]; // Ej. ["5m", "15m"]
  exitTimeframes?: string[];
}

export interface ArbitrageSimpleParameters {
  priceDifferencePercentageThreshold: number;
  minTradeVolumeQuote?: number;
  exchangeA_credentialLabel: string; // Referencia a APICredential.credentialLabel
  exchangeB_credentialLabel: string; // Referencia a APICredential.credentialLabel
}

export interface CustomAIDrivenParameters {
  primaryObjectivePrompt: string;
  contextWindowConfiguration?: Record<string, any>;
  decisionModelParameters?: Record<string, any>;
  maxTokensForResponse?: number;
}

export interface MCPSignalFollowerParameters {
  mcpSourceConfigId: string; // ID de UserConfiguration.mcpServerPreferences
  allowedSignalTypes?: string[];
}

export type StrategySpecificParameters = 
  | ScalpingParameters 
  | DayTradingParameters
  | ArbitrageSimpleParameters
  | CustomAIDrivenParameters
  | MCPSignalFollowerParameters
  | Record<string, any>; // Fallback

export interface TradingStrategyConfig {
  id: string; 
  userId: string; 

  configName: string; 
  baseStrategyType: BaseStrategyType | string; 
  description?: string; 

  isActivePaperMode: boolean;  
  isActiveRealMode: boolean;

  parameters: StrategySpecificParameters;

  applicabilityRules?: {
    explicitPairs?: string[];
    includeAllSpot?: boolean;
    dynamicFilter?: {
      minDailyVolatilityPercentage?: number;
      maxDailyVolatilityPercentage?: number;
      minMarketCapUSD?: number;
      includedWatchlistIds?: string[]; // IDs de watchlists de UserConfiguration
      assetCategories?: string[]; 
    };
  };

  aiAnalysisProfileId?: string; // FK a UserConfiguration.aiStrategyConfigurations.id

  riskParametersOverride?: {
    perTradeCapitalRiskPercentage?: number; 
    maxConcurrentTradesForThisStrategy?: number;
    maxCapitalAllocationQuote?: number; // Límite de capital total para esta config
  };
  
  version: number; // Inicia en 1
  parentConfigId?: string; // Si es una versión/optimización de otra

  performanceMetrics?: {
    totalTradesExecuted?: number;
    winningTrades?: number;
    losingTrades?: number;
    winRate?: number;
    cumulativePnlQuote?: number;
    averageWinningTradePnl?: number;
    averageLosingTradePnl?: number;
    profitFactor?: number;
    sharpeRatio?: number;
    lastCalculatedAt?: Date;
  };

  marketConditionFilters?: Array<{
    filterType: 'market_sentiment_index' | 'volatility_index' | 'btc_dominance' | 'overall_market_trend' | 'custom_mcp_data';
    sourceId?: string; 
    condition: 'less_than' | 'greater_than' | 'equal_to' | 'between';
    thresholdValue: number | [number, number];
    actionOnTrigger: 'activate_strategy' | 'pause_strategy' | 'allow_new_trades' | 'prevent_new_trades';
  }>;

  activationSchedule?: {
    cronExpression?: string;
    timeZone?: string;
    eventTriggers?: Array<{
      eventName: string; 
      action: 'activate' | 'deactivate';
      leadTimeMinutes?: number; 
    }>;
  };

  dependsOnStrategies?: Array<{
    strategyConfigId: string;
    requiredStatusForActivation?: 'active_and_profitable' | 'target_achieved' | 'specific_signal_fired';
  }>;

  sharingMetadata?: {
    isTemplate?: boolean;
    authorUserId?: string;
    sharedAt?: Date;
    userRatingAverage?: number;
    downloadOrCopyCount?: number;
    tags?: string[];
  };
  
  createdAt: Date;
  updatedAt: Date;
}

#### Opportunity

// Entidad: Opportunity
export interface Opportunity {
  id: string; 
  userId: string; 

  symbol: string; 
  detectedAt: Date; 

  sourceType: 'mcp_signal' | 'internal_indicator_algo' | 'ai_suggestion_proactive' | 'manual_entry' | 'user_defined_alert';
  sourceName?: string; 
  sourceData?: Record<string, any>; 

  initialSignal: {
    directionSought?: 'buy' | 'sell' | 'neutral' | 'hold';
    entryPrice_target?: number; 
    stopLoss_target?: number; 
    takeProfit_target?: number | number[]; // Puede ser un solo TP o múltiples
    timeframe?: string;
    reasoning_source_structured?: Record<string, any>; // Ej. { "indicator_RSI": { value: 28, condition: "oversold" } }
    reasoning_source_text?: string; // Fallback para texto simple
    confidence_source?: number;
  };

  systemCalculatedPriorityScore?: number; // (0-100)
  lastPriorityCalculationAt?: Date;

  status:  
    | 'new' 
    | 'pending_ai_analysis' 
    | 'under_ai_analysis' 
    | 'analysis_complete'
    | 'rejected_by_ai' 
    | 'rejected_by_user'
    | 'pending_user_confirmation_real' 
    | 'converted_to_trade_paper' 
    | 'converted_to_trade_real' 
    | 'expired'
    | 'error_in_processing'
    | 'pending_further_investigation'
    | 'investigation_complete'
    | 'simulated_post_facto';
  
  statusReasonCode?: string; // Ej. "AI_LOW_CONFIDENCE", "EXPIRED_TIMEOUT"
  statusReasonText?: string; 

  aiAnalysis?: {
    analysisId?: string; 
    analyzedAt: Date;
    modelUsed?: string; 
    
    calculatedConfidence: number; 
    suggestedAction: 'strong_buy' | 'buy' | 'hold_neutral' | 'sell' | 'strong_sell' | 'further_investigation_needed' | 'no_clear_opportunity';
    
    recommendedTradeStrategyType?: 'simple_entry' | 'scaled_entry_dca' | 'grid_setup' | 'options_spread';
    recommendedTradeParams?: Record<string, any> | 
      { entryPrice?: number; stopLossPrice?: number; takeProfitLevels?: number[]; tradeSizePercentage?: number; } |
      { dcaLevels?: Array<{price: number, percentageOfAllocation: number}>; initialStopLoss?: number; overallProfitTarget?: number; };

    reasoning_ai?: string; 
    
    dataVerification?: {
      mobulaCheckStatus?: 'success' | 'failed' | 'not_applicable' | 'pending';
      mobulaDiscrepancies?: string; 
      // ... otros checks (ej. binanceDataCheckStatus)
    };
    
    processingTimeMs?: number;
    aiWarnings?: string[];
  };

  investigationDetails?: {
    assignedTo?: 'user' | 'automated_follow_up_process';
    investigationNotes?: Array<{ note: string; author: string; timestamp: Date; }>;
    nextSteps?: string;
    status?: 'pending' | 'in_progress' | 'resolved_actionable' | 'resolved_discarded';
  };

  userFeedback?: {
    actionTaken: 'accepted_for_trade' | 'rejected_opportunity' | 'modified_params_for_trade' | 'marked_for_investigation';
    rejectionReason?: string; 
    modificationNotes?: string; 
    timestamp: Date;
  };

  linkedTradeIds?: string[]; // Para soportar múltiples trades desde una oportunidad

  expiresAt?: Date;
  expirationLogic?: {
    type: 'fixed_duration_from_detection' | 'timeframe_based' | 'ai_calculated_volatility' | 'manual_user_set';
    value?: string | number; 
  };

  postTradeFeedback?: {
    relatedTradeIds: string[]; 
    overallOutcome?: 'profitable' | 'loss_making' | 'break_even';
    finalPnlQuote?: number;
    outcomeMatchesAISuggestion?: boolean;
    aiConfidenceWasJustified?: boolean;
    keyLearningsOrObservations?: string;
    feedbackTimestamp: Date;
  };

  postFactoSimulationResults?: {
    simulatedAt: Date;
    parametersUsed: Record<string, any>;
    estimatedPnl?: number;
    maxFavorableExcursion?: number;
    maxAdverseExcursion?: number;
    notes?: string;
  };
  
  createdAt: Date; 
  updatedAt: Date; 
}

### API Payload Schemas (If distinct)

#### CreateOrUpdateApiCredentialRequest

// API Payload Schema: CreateOrUpdateApiCredentialRequest
// Utilizado para POST /api/v1/credentials (crear) y PUT /api/v1/credentials/{credentialId} (reemplazar)

// Reutilizamos el enum definido en la entidad APICredential para consistencia
// import { ServiceName } from './APICredential'; // Asumiendo que está en un archivo accesible

export enum ServiceNameEnumForRequest { // Podría ser el mismo enum ServiceName de la entidad
  BINANCE_SPOT = "BINANCE_SPOT",
  BINANCE_FUTURES = "BINANCE_FUTURES",
  TELEGRAM_BOT = "TELEGRAM_BOT",
  GEMINI_API = "GEMINI_API",
  MOBULA_API = "MOBULA_API",
  N8N_WEBHOOK = "N8N_WEBHOOK",
  MCP_GENERIC = "MCP_GENERIC",
  MCP_DOGGYBEE_CCXT = "MCP_DOGGYBEE_CCXT",
  MCP_METATRADER_BRIDGE = "MCP_METATRADER_BRIDGE",
  MCP_WEB3_RESEARCH = "MCP_WEB3_RESEARCH",
  CUSTOM_SERVICE = "CUSTOM_SERVICE"
}

export interface CustomServiceDefinitionForRequest {
  displayName: string; // Nombre legible para la UI
  // Ayuda a la UI a saber qué campos podría esperar el usuario en otherDetails para este servicio:
  expectedOtherDetailFields?: Array<{ fieldName: string; fieldType: 'string' | 'number' | 'boolean'; isSensitive?: boolean }>;
  documentationUrl?: string; // URL a la documentación de este servicio custom
}

export interface CreateOrUpdateApiCredentialRequest {
  serviceName: ServiceNameEnumForRequest | string; // Nombre del servicio. Para POST, es crucial. Para PUT, podría ser inferido o para validar.
  credentialLabel?: string; // Etiqueta amigable para el usuario

  // Credenciales en TEXTO PLANO. El backend se encarga de la encriptación.
  apiKey: string; 
  apiSecret?: string;
  apiPassphrase?: string; // Para servicios que usan una passphrase adicional

  // Para otros detalles específicos del servicio (ej. Telegram Bot Token y Chat ID).
  // La UI los envía como un objeto; el backend lo serializa a JSON y encripta el blob.
  otherDetails?: Record<string, any>; 

  // Solo relevante si serviceName es 'CUSTOM_SERVICE' o un string no en el enum
  customServiceDefinition?: CustomServiceDefinitionForRequest;

  notes?: string; // Notas opcionales del usuario

  // Solicitar al backend que intente verificar la credencial inmediatamente después de guardarla.
  // El resultado de la verificación se podría devolver en la respuesta o actualizar el estado de la credencial.
  verifyAfterSave?: boolean; 
}


#### UpdateUserConfigurationRequest

// API Payload Schema: UpdateUserConfigurationRequest
// Utilizado para PATCH /api/v1/config

// (Reutilizar/Importar NotificationPreferenceForUpdate, WatchlistForUpdate, etc., como se definieron antes,
// con la salvedad del cambio en McpServerPreferenceForUpdate)

export interface McpServerPreferenceForUpdate { // Actualizado
  id: string; // Necesario para identificar cuál actualizar en la lista
  credentialId?: string | null; // ID de la APICredential asociada (gestionada vía /credentials/)
  url?: string; // Configuración no sensible
  isEnabled?: boolean; // Configuración no sensible
  queryFrequencySeconds?: number; // Configuración no sensible
  reliabilityWeight?: number; // Configuración no sensible
  customParameters?: Record<string, any>; // Configuración no sensible
}

// ... (Las otras interfaces como NotificationPreferenceForUpdate, WatchlistForUpdate, 
// RiskProfileSettingsForUpdate, RealTradingSettingsForUpdate, AiStrategyConfigurationForUpdate, 
// DashboardLayoutProfileForUpdate, CloudSyncPreferenceForUpdate permanecen como las definimos
// anteriormente, ya que sus campos ya eran opcionales y adecuados para un PATCH)

export interface UpdateUserConfigurationRequest {
  _knownVersion?: number; // Para optimistic locking

  // --- Preferencias de Notificaciones ---
  telegramChatId?: string;
  notificationPreferences?: Array<NotificationPreferenceForUpdate>; // Asume reemplazo de la lista si se envía
  enableTelegramNotifications?: boolean;

  // --- Preferencias de Trading ---
  defaultPaperTradingCapital?: number;
  watchlists?: Array<WatchlistForUpdate>; // Asume reemplazo de la lista si se envía
  
  riskProfile?: 'conservative' | 'moderate' | 'aggressive' | 'custom';
  riskProfileSettings?: RiskProfileSettingsForUpdate; // Backend hará merge profundo
  realTradingSettings?: RealTradingSettingsForUpdate; // Backend hará merge profundo

  // --- Preferencias de IA y Análisis ---
  aiStrategyConfigurations?: Array<AiStrategyConfigurationForUpdate>; // Asume reemplazo de la lista si se envía
  mcpServerPreferences?: Array<McpServerPreferenceForUpdate>; // Asume reemplazo de la lista si se envía

  // --- Preferencias de UI ---
  selectedTheme?: 'dark' | 'light';
  dashboardLayoutProfiles?: Record<string, { name: string; configuration: any; }>; // Asume reemplazo del objeto completo de perfiles
  activeDashboardLayoutProfileId?: string;
  
  // --- Configuración de Persistencia y Sincronización ---
  cloudSyncPreferences?: CloudSyncPreferenceForUpdate; // Backend hará merge profundo
}

#### SaveTradingStrategyConfigRequest

// API Payload Schema: SaveTradingStrategyConfigRequest
// Utilizado para POST /api/v1/strategies (crear)
// y PUT /api/v1/strategies/{strategyConfigId} (reemplazar/actualizar completamente)

// Asumimos que BaseStrategyType, StrategySpecificParameters (y sus interfaces internas como ScalpingParameters, 
// CustomAIDrivenParameters, etc.), ApplicabilityRulesForRequest, etc., están definidas como antes,
// con la consideración de que si algún parámetro dentro de StrategySpecificParameters es una clave API,
// debería ser un campo como 'someServiceApiKeyCredentialId?: string' que referencia una APICredential.

export interface SaveTradingStrategyConfigRequest {
  configName: string; 
  baseStrategyType: BaseStrategyType | string; 
  description?: string; 

  isActivePaperMode: boolean;  
  isActiveRealMode: boolean;

  parameters: StrategySpecificParameters; // Asegurarse que si hay secretos, sean IDs de credenciales

  applicabilityRules?: ApplicabilityRulesForRequest;

  aiAnalysisProfileId?: string; 

  riskParametersOverride?: RiskParametersOverrideForRequest;
  
  parentConfigId?: string; // Para versionado o duplicación

  status?: 'draft' | 'validated'; // Nuevo estado para la configuración

  marketConditionFilters?: Array<MarketConditionFilterForRequest>;
  activationSchedule?: ActivationScheduleForRequest;
  dependsOnStrategies?: Array<StrategyDependencyForRequest>;
  sharingMetadata?: SharingMetadataForRequest;

  // Acciones post-guardado
  runBacktestAfterSave?: boolean;       // Default: false
  deployToPaperTradingAfterSave?: boolean; // Default: false
  deployToRealTradingAfterSave?: boolean;  // Default: false (requiere precaución y validación extra)
}

### Database Schemas (If applicable)

#### user_configurations 

    -- Tabla: user_configurations
    
    CREATE TABLE user_configurations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL, -- FK a la futura tabla 'users' cuando esta se defina.
    
        -- Preferencias de Notificaciones
        telegram_chat_id VARCHAR(255),
        notification_preferences JSONB, -- Ej: [{ "eventType": "REAL_TRADE_EXECUTED", "channel": "telegram", "isEnabled": true, "minConfidence": 0.9 }, ...]
        enable_telegram_notifications BOOLEAN DEFAULT TRUE,
    
        -- Preferencias de Trading
        default_paper_trading_capital DECIMAL(18, 8), -- Capital para paper trading, ej: 1000.00
        watchlists JSONB, -- Ej: [{ "id": "uuid_watchlist_1", "name": "Volátiles Alto Riesgo", "pairs": ["BTC/USDT", "SOL/USDT"], ... }]. Considerar normalizar a tablas separadas en futuras versiones si se requiere consulta compleja/compartición.
        favorite_pairs TEXT[], -- Ej: {"BTC/USDT", "ETH/USDT"}
        risk_profile VARCHAR(50), -- 'conservative', 'moderate', 'aggressive', 'custom'
        risk_profile_settings JSONB, -- Ej: { "dailyCapitalRiskPercentage": 0.02, "perTradeCapitalRiskPercentage": 0.01 }. Aplicable si risk_profile es 'custom' o para sobreescribir defaults.
        real_trading_settings JSONB, -- Ej: { "maxConcurrentOperations": 5, "dailyLossLimitAbsolute": 100.00, ... }
    
        -- Preferencias de IA y Análisis
        ai_strategy_configurations JSONB, -- Ej: [{ "id": "uuid_ai_config_1", "name": "Scalping Agresivo BTC", "geminiPromptTemplate": "Analiza esta oportunidad para scalping...", ... }]
        ai_analysis_confidence_thresholds JSONB, -- Ej: { "paperTrading": 0.75, "realTrading": 0.85 }
        mcp_server_preferences JSONB, -- Ej: [{ "id": "mcp_server_xyz", "type": "ccxt", "credentialId": "uuid_de_api_credential", "isEnabled": true, ... }]. IMPORTANTE: Contiene 'credentialId' (referencia a api_credentials), NO 'apiKey'.
    
        -- Preferencias de UI
        selected_theme VARCHAR(50) DEFAULT 'dark', -- 'dark' o 'light'
        dashboard_layout_profiles JSONB, -- Almacena perfiles de layout guardados. Ej: { "profile_id_1": { "name": "Vista de Trading", "configuration": { /* detalle del layout */ } }, ... }
        active_dashboard_layout_profile_id VARCHAR(255), -- ID del perfil de layout actualmente activo (clave dentro de dashboard_layout_profiles).
        dashboard_layout_config JSONB, -- Configuración de layout personalizada/actual. Puede ser una modificación no guardada del perfil activo, o un layout ad-hoc si active_dashboard_layout_profile_id es NULL.
    
        -- Configuración de Persistencia y Sincronización
        cloud_sync_preferences JSONB, -- Ej: { "isEnabled": true, "lastSuccessfulSync": "YYYY-MM-DDTHH:MM:SSZ", "frequency": "daily" }
    
        -- Timestamps
        created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    
        -- Constraints e Índices
        CONSTRAINT uq_user_configurations_user_id UNIQUE (user_id) -- Asumiendo una única fila de configuración por usuario.
    );
    
    -- Disparador para actualizar automáticamente 'updated_at'
    CREATE OR REPLACE FUNCTION trigger_set_timestamp()
    RETURNS TRIGGER AS $$
    BEGIN
      NEW.updated_at = timezone('utc'::text, now());
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    CREATE TRIGGER set_user_configurations_updated_at
    BEFORE UPDATE ON user_configurations
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
    
    -- Índices para campos comúnmente consultados
    CREATE INDEX idx_user_configurations_user_id ON user_configurations(user_id);
    -- CREATE INDEX idx_user_configurations_telegram_chat_id ON user_configurations(telegram_chat_id); -- Considerar si se realizarán búsquedas frecuentes por este campo.


#### api_credentials

    CREATE TABLE api_credentials (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES user_configurations(user_id) ON DELETE CASCADE,
    
        service_name VARCHAR(100) NOT NULL, -- Validar contra enum definido en la aplicación para v1.0 (ej: 'BINANCE_SPOT', 'TELEGRAM_BOT').
        credential_label VARCHAR(255) NOT NULL, -- Etiqueta obligatoria definida por el usuario o autogenerada por la app para diferenciar claves del mismo servicio.
    
        -- Campos encriptados (la encriptación/desencriptación ocurre en la capa de aplicación)
        encrypted_api_key TEXT NOT NULL,
        encrypted_api_secret TEXT, -- Opcional, no todos los servicios usan un secret.
        encrypted_other_details TEXT, -- Para JSON encriptado con detalles adicionales (ej: passphrase para algunas APIs de exchange).
    
        status VARCHAR(50) NOT NULL DEFAULT 'verification_pending' CHECK (status IN (
            'active', 
            'inactive', 
            'revoked', 
            'verification_pending', 
            'verification_failed', 
            'expired'
        )),
        last_verified_at TIMESTAMPTZ, -- Fecha de la última verificación exitosa de la API key.
        
        permissions TEXT[], -- Permisos de la API Key, ej: {"readOnly", "enableSpotTrading", "enableWithdrawals"}. La app interpretará estos strings.
        permissions_checked_at TIMESTAMPTZ, -- Cuándo se verificaron por última vez los permisos.
    
        expires_at TIMESTAMPTZ, -- Fecha de expiración de la clave API, si es proporcionada por el servicio.
        rotation_reminder_policy_days INTEGER, -- Días antes de expires_at para un recordatorio (lógica de notificación en la app).
    
        usage_count INTEGER DEFAULT 0, -- Contador de uso (actualizado por la app).
        last_used_at TIMESTAMPTZ, -- Fecha del último uso exitoso (actualizado por la app).
    
        purpose_description TEXT, -- Descripción del propósito de esta API key (ej: "Para trading en par BTC/USDT", "Para recibir notificaciones de trades").
        tags TEXT[], -- Etiquetas para organizar/filtrar, ej: {"trading_principal", "bot_scalping", "notificaciones_alertas"}.
    
        notes TEXT, -- Notas opcionales del usuario sobre esta credencial.
    
        created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    
        -- Un usuario no puede tener múltiples credenciales para el mismo servicio con la misma etiqueta.
        CONSTRAINT uq_api_credentials_user_service_label UNIQUE (user_id, service_name, credential_label) 
    );
    
    -- Disparador para actualizar automáticamente 'updated_at'
    -- (La función trigger_set_timestamp() ya fue creada con user_configurations)
    CREATE TRIGGER set_api_credentials_updated_at
    BEFORE UPDATE ON api_credentials
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
    
    -- Índices
    CREATE INDEX idx_api_credentials_user_id ON api_credentials(user_id);
    CREATE INDEX idx_api_credentials_service_name ON api_credentials(service_name);
    CREATE INDEX idx_api_credentials_status ON api_credentials(status);
    CREATE INDEX idx_api_credentials_expires_at ON api_credentials(expires_at);
    -- CREATE INDEX idx_api_credentials_tags_gin ON api_credentials USING GIN (tags); -- Opcional para v1.0, considerar si hay búsquedas frecuentes por tags.

#### Notifications

    -- Tabla: notifications
    
    CREATE TABLE notifications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID, -- Referencia a user_configurations(user_id). Este user_id en user_configurations representa el ID del usuario final.
                       -- ON DELETE SET NULL permite mantener el historial de notificaciones incluso si la configuración del usuario (o el usuario) se elimina, marcando la notificación como "huérfana" o del sistema.
    
        event_type VARCHAR(100) NOT NULL, -- Ej: "REAL_TRADE_EXECUTED", "OPPORTUNITY_ANALYZED", "SYSTEM_ERROR"
        channel VARCHAR(50) NOT NULL CHECK (channel IN ('telegram', 'ui', 'email')), 
    
        title_key VARCHAR(255), -- Clave para i18n del título (app se encarga de la lógica).
        message_key VARCHAR(255), -- Clave para i18n del mensaje (app se encarga de la lógica).
        message_params JSONB, -- Parámetros para plantillas i18n, ej: {"symbol": "BTC/USDT", "pnl": "25.50"}
        
        title TEXT NOT NULL, -- Título (fallback o idioma por defecto).
        message TEXT NOT NULL, -- Mensaje (fallback o idioma por defecto).
    
        priority VARCHAR(50) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
        
        status VARCHAR(50) NOT NULL DEFAULT 'new' CHECK (status IN (
            'new', 
            'read', 
            'archived', 
            'error_sending',
            'snoozed',
            'processing_action' 
        )),
        snoozed_until TIMESTAMPTZ, -- Si status es 'snoozed'.
    
        data_payload JSONB, -- Datos contextuales del evento, ej: { "tradeId": "uuid_trade_abc", "opportunityId": "uuid_opp_xyz" }
        actions JSONB, -- Array de acciones para la UI, ej: [{ "label": "Ver Detalles", "actionType": "NAVIGATE", "actionValue": "/trade/uuid_trade_abc" }]
    
        correlation_id VARCHAR(255), -- Para agrupar notificaciones relacionadas.
    
        is_summary BOOLEAN DEFAULT FALSE,
        summarized_notification_ids UUID[], -- IDs de notificaciones resumidas (si is_summary es true).
    
        created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
        read_at TIMESTAMPTZ, -- Se actualiza cuando el usuario la marca como leída.
        sent_at TIMESTAMPTZ, -- Se actualiza cuando la notificación se envía por el 'channel'.
    
        status_history JSONB, -- Historial de cambios de estado. Ej: [{ "status": "new", "changedAt": "timestamp", "changedBy": "system" }]. Puede crecer; evaluar necesidad detallada para v1.0.
        generated_by VARCHAR(100), -- Módulo/proceso que generó la notificación.
    
        CONSTRAINT fk_notifications_user_id FOREIGN KEY (user_id) REFERENCES user_configurations(user_id) ON DELETE SET NULL
    );
    
    -- Índices
    CREATE INDEX idx_notifications_user_id_btree ON notifications(user_id) WHERE user_id IS NOT NULL; -- Índice para user_id (solo si no es NULL)
    CREATE INDEX idx_notifications_event_type ON notifications(event_type);
    CREATE INDEX idx_notifications_status ON notifications(status);
    CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC); 
    CREATE INDEX idx_notifications_priority ON notifications(priority);
    CREATE INDEX idx_notifications_correlation_id ON notifications(correlation_id); 
    
    -- Índice compuesto opcional para la consulta común de "mostrar mis notificaciones":
    -- CREATE INDEX idx_notifications_user_status_created ON notifications(user_id, status, created_at DESC); 
    -- Este índice podría mejorar el rendimiento para esa consulta específica, potencialmente haciendo idx_notifications_user_id_btree e idx_notifications_status redundantes para dicha consulta.
    
    -- Índices GIN opcionales para búsqueda en JSONB (optimización futura):
    -- CREATE INDEX idx_notifications_data_payload_gin ON notifications USING GIN (data_payload);
    -- CREATE INDEX idx_notifications_status_history_gin ON notifications USING GIN (status_history);

#### Trades
    -- Tabla: trades
    
    CREATE TABLE trades (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL, -- FK a user_configurations(user_id) o idealmente a una futura tabla users(id). ON DELETE CASCADE es apropiado.
        mode VARCHAR(20) NOT NULL CHECK (mode IN ('paper', 'real', 'backtest')),
    
        symbol VARCHAR(50) NOT NULL, -- Ej: "BTC/USDT"
        side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
        
        strategy_id VARCHAR(255), -- FK a trading_strategy_configs(id). Referencia a la configuración de estrategia que originó el trade.
        opportunity_id UUID, -- FK a opportunities(id). Referencia a la oportunidad que pudo haber generado este trade.
        ai_analysis_confidence DECIMAL(5, 4), -- Ej: 0.9550 (rango [0,1]), confianza de la IA si participó en la decisión.
    
        strategy_execution_instance_id VARCHAR(255), -- ID para agrupar trades de una misma "ejecución" o ciclo de una estrategia (ej. para DCA, Grid).
    
        position_status VARCHAR(50) NOT NULL CHECK (position_status IN (
            'pending_entry_conditions', -- Esperando que se cumplan las condiciones predefinidas para enviar la orden de entrada.
            'opening',                  -- Orden de entrada enviada al exchange, esperando llenado parcial o total.
            'open',                     -- Posición abierta y activa en el mercado.
            'partially_closed',         -- Parte de la posición ha sido cerrada (ej. un TP parcial).
            'closing',                  -- Orden(es) de salida enviada(s) (TP/SL total), esperando llenado.
            'closed',                   -- Posición completamente cerrada.
            'error'                     -- Error en la gestión o ejecución del trade.
        )),
    
        entry_order JSONB NOT NULL, -- Objeto TradeOrderDetails. Considerar normalizar a tabla 'trade_orders' en v2.0+ si se requieren consultas complejas sobre detalles de órdenes.
        exit_orders JSONB,          -- Array de objetos TradeOrderDetails. Misma consideración de normalización futura que entry_order.
    
        initial_risk_quote_amount DECIMAL(18, 8), -- Cantidad de capital (en moneda de cotización) arriesgada inicialmente.
        initial_reward_to_risk_ratio DECIMAL(10, 2), -- Ratio Riesgo/Beneficio inicial esperado.
        risk_reward_adjustments JSONB, -- Array de objetos documentando ajustes a SL/TP durante la vida del trade. Ej: [{ "timestamp": "ts", "newStopLoss": 30000, "reason": "manual" }]
        current_risk_quote_amount DECIMAL(18, 8), -- Riesgo actual después de ajustes.
        current_reward_to_risk_ratio DECIMAL(10, 2), -- Ratio R/B actual.
    
        pnl DECIMAL(18, 8), -- Profit and Loss realizado, en la moneda de cotización.
        pnl_percentage DECIMAL(10, 4), -- P&L como porcentaje (ej. 5.1234% es 5.1234).
        closing_reason TEXT, -- Razón del cierre: "TP_HIT", "SL_HIT", "MANUAL_USER", "AI_SIGNAL", "STRATEGY_EXIT_CONDITION", "EXPIRED".
    
        market_context_snapshots JSONB, -- Ej: { "onEntry": { "price": 30000, "RSI_14_1h": 45, "relevant_news_ids": ["id1"] }, "onExit": { ... } }
        external_event_or_analysis_link JSONB, -- Ej: { "type": "news_event", "referenceId": "url_o_id_noticia", "description": "Impacto de noticia X" }
        backtest_details JSONB, -- Rellenar solo si mode = 'backtest'. Ej: { "backtestRunId": "uuid_run_1", "parametersSnapshot": { "paramA": 10 } }
    
        notes TEXT, -- Notas del usuario sobre este trade específico.
        
        created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL, -- Cuándo se creó el registro del trade en nuestra BD.
        opened_at TIMESTAMPTZ, -- Cuándo se abrió efectivamente la posición en el mercado (ej. primera ejecución de entry_order).
        closed_at TIMESTAMPTZ, -- Cuándo se cerró completamente la posición en el mercado (ej. última ejecución de exit_orders).
        updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    
        CONSTRAINT fk_trades_user_id FOREIGN KEY (user_id) REFERENCES user_configurations(user_id) ON DELETE CASCADE
        -- Las siguientes FKs se activarán cuando las tablas referenciadas y sus PKs (asumidas como 'id') existan:
        -- ,CONSTRAINT fk_trades_opportunity_id FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL
        -- ,CONSTRAINT fk_trades_strategy_id FOREIGN KEY (strategy_id) REFERENCES trading_strategy_configs(id) ON DELETE SET NULL
    );
    
    -- Disparador para actualizar automáticamente 'updated_at'
    -- (La función trigger_set_timestamp() ya fue creada)
    CREATE TRIGGER set_trades_updated_at
    BEFORE UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
    
    -- Índices
    CREATE INDEX idx_trades_user_id ON trades(user_id);
    CREATE INDEX idx_trades_symbol ON trades(symbol);
    CREATE INDEX idx_trades_mode ON trades(mode);
    CREATE INDEX idx_trades_position_status ON trades(position_status);
    CREATE INDEX idx_trades_strategy_id ON trades(strategy_id); 
    CREATE INDEX idx_trades_opportunity_id ON trades(opportunity_id); 
    CREATE INDEX idx_trades_strategy_execution_instance_id ON trades(strategy_execution_instance_id);
    CREATE INDEX idx_trades_opened_at ON trades(opened_at DESC);
    CREATE INDEX idx_trades_closed_at ON trades(closed_at DESC);
    CREATE INDEX idx_trades_created_at ON trades(created_at DESC);
    
    -- Índices compuestos opcionales (evaluar según patrones de consulta más comunes y si los individuales no son suficientes):
    -- CREATE INDEX idx_trades_user_symbol_opened_at ON trades(user_id, symbol, opened_at DESC); -- Para "diario de trading" de un usuario por símbolo.
    -- CREATE INDEX idx_trades_user_status_opened_at ON trades(user_id, position_status, opened_at DESC); -- Para "trades abiertos/cerrados de un usuario".
    
    -- Índices GIN opcionales para JSONB (optimización futura si se requiere consulta profunda en estos campos):
    -- CREATE INDEX idx_trades_entry_order_gin ON trades USING GIN (entry_order);
    -- CREATE INDEX idx_trades_exit_orders_gin ON trades USING GIN (exit_orders);

#### Trading_strategy_configs

    -- Tabla: trading_strategy_configs
    
    CREATE TABLE trading_strategy_configs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL, -- FK a user_configurations(user_id) o idealmente a una futura tabla users(id).
        
        config_name VARCHAR(255) NOT NULL, -- Nombre descriptivo dado por el usuario.
        base_strategy_type VARCHAR(100) NOT NULL CHECK (base_strategy_type IN (
            'SCALPING', 
            'DAY_TRADING', 
            'SWING_TRADING', 
            'ARBITRAGE_SIMPLE', 
            'ARBITRAGE_TRIANGULAR',
            'GRID_TRADING',
            'DCA_INVESTING',
            'CUSTOM_AI_DRIVEN',
            'MCP_SIGNAL_FOLLOWER'
            -- La aplicación debe validar contra un enum BaseStrategyType más completo. El CHECK es una salvaguarda.
        )),
        description TEXT, -- Descripción detallada de la configuración de la estrategia.
    
        is_active_paper_mode BOOLEAN DEFAULT FALSE NOT NULL, -- Si está activa para paper trading.
        is_active_real_mode BOOLEAN DEFAULT FALSE NOT NULL, -- Si está activa para trading real.
    
        parameters JSONB NOT NULL, -- Objeto JSON con todos los parámetros específicos de la estrategia base (ej: { "takeProfitPct": 0.01, "stopLossPct": 0.005 } para ScalpingParameters).
        applicability_rules JSONB, -- Reglas para determinar cuándo/dónde aplicar esta estrategia. Ej: { "explicitPairs": ["BTC/USDT", "ETH/BTC"], "allowedTimeframes": ["1m", "5m"], "marketRegimeFilter": "trending_up" }.
        
        ai_analysis_profile_id UUID, -- Referencia lógica al ID de un perfil de análisis de IA definido en UserConfiguration.aiStrategyConfigurations. La app valida la existencia.
    
        risk_parameters_override JSONB, -- Sobrescribe el perfil de riesgo global para esta estrategia específica. Ej: { "maxTradeSizePercentage": 0.10, "dailyDrawdownLimit": 500.00 }.
        
        version INTEGER DEFAULT 1 NOT NULL, -- Versión de esta configuración de estrategia.
        parent_config_id UUID REFERENCES trading_strategy_configs(id) ON DELETE SET NULL, -- Si esta config es una versión/clon de otra. ON DELETE SET NULL para no perder la historia.
    
        performance_metrics JSONB, -- Métricas de rendimiento cacheadas para esta config (actualizadas por la app/job). Ej: { "totalTrades": 150, "winRate": 0.55, "avgPnlPerTrade": 12.34, "lastCalculationAt": "timestamp" }.
        market_condition_filters JSONB, -- Array de filtros basados en condiciones de mercado para activar/desactivar la estrategia dinámicamente. Ej: [{ "filterType": "VIX_MCP", "condition": "greater_than", "value": 30, "action": "pause_new_trades" }].
        activation_schedule JSONB, -- Configuración para activar/desactivar la estrategia automáticamente (ej. cron). Ej: { "cronExpression": "0 0 * * MON-FRI", "timeZone": "America/New_York", "action": "activate" }.
        depends_on_strategies JSONB, -- Array de IDs (UUIDs) de otras trading_strategy_configs de las que esta depende. Referencia lógica. Ej: [{ "strategyConfigId": "uuid_parent_strat", "conditionForActivation": "parent_must_be_profitable_last_7d" }].
        sharing_metadata JSONB, -- Metadatos para plantillas o compartición. Ej: { "isTemplate": true, "authorUserId": "uuid_del_creador", "tags": ["scalping", "volatility", "btc"], "communityRating": 4.5, "downloadCount": 100 }.
        
        created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    
        CONSTRAINT fk_trading_strategy_configs_user_id FOREIGN KEY (user_id) REFERENCES user_configurations(user_id) ON DELETE CASCADE,
        CONSTRAINT uq_trading_strategy_configs_user_name UNIQUE (user_id, config_name) -- Un usuario no puede tener dos configuraciones de estrategia con el mismo nombre.
    );
    
    -- Disparador para actualizar automáticamente 'updated_at'
    -- (La función trigger_set_timestamp() ya fue creada)
    CREATE TRIGGER set_trading_strategy_configs_updated_at
    BEFORE UPDATE ON trading_strategy_configs
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
    
    -- Índices
    CREATE INDEX idx_trading_strategy_configs_user_id ON trading_strategy_configs(user_id);
    CREATE INDEX idx_trading_strategy_configs_base_strategy_type ON trading_strategy_configs(base_strategy_type);
    CREATE INDEX idx_trading_strategy_configs_is_active_paper ON trading_strategy_configs(is_active_paper_mode);
    CREATE INDEX idx_trading_strategy_configs_is_active_real ON trading_strategy_configs(is_active_real_mode);
    CREATE INDEX idx_trading_strategy_configs_parent_id ON trading_strategy_configs(parent_config_id);
    
    -- Índices GIN opcionales para JSONB (optimización futura si se requieren búsquedas frecuentes dentro de estos campos):
    -- CREATE INDEX idx_tsc_sharing_metadata_tags ON trading_strategy_configs USING GIN ((sharing_metadata -> 'tags')); -- Si se busca por etiquetas.
    -- CREATE INDEX idx_tsc_parameters_specific_key ON trading_strategy_configs USING GIN ((parameters -> 'nombre_parametro_comun')); -- Si se filtra por un parámetro específico común.
    -- CREATE INDEX idx_tsc_applicability_rules_pairs ON trading_strategy_configs USING GIN ((applicability_rules -> 'explicitPairs')); -- Si se buscan estrategias por pares explícitos.


#### Opportunity

    -- Tabla: opportunities
    
    CREATE TABLE opportunities (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL, -- FK a user_configurations(user_id) o idealmente a una futura tabla users(id).
    
        symbol VARCHAR(50) NOT NULL, -- Ej: "BTC/USDT"
        detected_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()), -- Cuándo se detectó/creó la oportunidad.
    
        source_type VARCHAR(50) NOT NULL CHECK (source_type IN (
            'mcp_signal', 
            'internal_indicator_algo', 
            'ai_suggestion_proactive', 
            'manual_entry', 
            'user_defined_alert'
        )),
        source_name VARCHAR(255), -- Nombre de la fuente específica, ej: "MCP_EMA_Cross_Bot", "Manual_High_Conviction"
        source_data JSONB, -- Payload original de la fuente (ej. datos del MCP, parámetros del indicador que disparó la alerta).
    
        initial_signal JSONB NOT NULL, -- Detalles de la señal inicial. 
                                      -- Ej: { "directionSought": "buy", "entryPrice_target": 30000, "stopLoss_target": 29500, "takeProfit_target": [31000, 32000], "timeframe": "4h", "reasoning_source_text": "Breakout de resistencia clave" }
    
        system_calculated_priority_score SMALLINT CHECK (system_calculated_priority_score >= 0 AND system_calculated_priority_score <= 100), -- Puntuación de prioridad (0-100) asignada por el sistema.
        last_priority_calculation_at TIMESTAMPTZ, -- Cuándo se calculó/actualizó por última vez la prioridad.
    
        status VARCHAR(50) NOT NULL DEFAULT 'new' CHECK (status IN (
            'new',                          -- Recién detectada.
            'pending_ai_analysis',          -- Esperando que la IA la analice.
            'under_ai_analysis',            -- Actualmente siendo analizada por la IA.
            'analysis_complete',            -- Análisis de IA completado.
            'rejected_by_ai',               -- Descartada por la IA.
            'rejected_by_user',             -- Descartada manualmente por el usuario.
            'pending_user_confirmation_real', -- Esperando confirmación del usuario para operar en real.
            'converted_to_trade_paper',     -- Convertida a un trade simulado.
            'converted_to_trade_real',      -- Convertida a un trade real.
            'expired',                      -- La oportunidad ya no es válida.
            'error_in_processing',          -- Error durante el procesamiento.
            'pending_further_investigation',-- Marcada para investigación/seguimiento manual.
            'investigation_complete',       -- Investigación/seguimiento completado.
            'simulated_post_facto'          -- Analizada o simulada después de que el evento de mercado ya ocurrió.
            -- La lógica de la aplicación gestionará las transiciones entre estos estados; priorizar implementación de estados clave para MVP.
        )),
        status_reason_code VARCHAR(100), -- Código breve para la razón del estado, ej: "AI_CONF_LOW", "USER_REJECT_VOLATILE"
        status_reason_text TEXT, -- Descripción más detallada de la razón del estado.
    
        ai_analysis JSONB, -- Resultados del análisis de IA. 
                           -- Ej: { "analysisId": "uuid_analysis", "modelUsed": "Gemini-1.5-Pro", "calculatedConfidence": 0.92, "suggestedAction": "buy", "recommendedTradeParams": {"entry":30050, "sl": 29400, "tp":[31500]}, "reasoning_ai": "Fuerte señal alcista..." }
        investigation_details JSONB, -- Ej: { "assignedTo": "user_review_queue", "notes": [{ "note": "Posible evento de noticias impactando. Investigar.", "author": "system_flag", "timestamp": "ts" }] }
        user_feedback JSONB, -- Feedback del usuario. 
                             -- Ej: { "actionTaken": "converted_to_trade_paper", "modificationNotes": "Ajusté SL manualmente", "timestamp": "ts" }
    
        -- Almacena los IDs de los trades generados desde esta oportunidad. La relación principal se establece desde trades.opportunity_id -> opportunities.id.
        linked_trade_ids UUID[], 
    
        expires_at TIMESTAMPTZ, -- Cuándo expira la validez de esta oportunidad si no se actúa.
        expiration_logic JSONB, -- Lógica que determinó expires_at. 
                                -- Ej: { "type": "time_since_detection", "duration_seconds": 14400 } o { "type": "specific_market_event", "event_description": "Hasta cierre de vela diaria" }
    
        post_trade_feedback JSONB, -- Feedback después de que los trades vinculados se completan (poblado por la app).
                                   -- Ej: { "relatedTradeIds": ["uuid_trade_1"], "overallOutcome": "profitable", "finalPnlQuote": 150.75, "aiConfidenceWasJustified": true, "keyLearnings": "La estrategia funcionó bien en este contexto." }
        post_facto_simulation_results JSONB, -- Resultados si se simuló la oportunidad después del hecho.
    
        created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    
        CONSTRAINT fk_opportunities_user_id FOREIGN KEY (user_id) REFERENCES user_configurations(user_id) ON DELETE CASCADE
    );
    
    -- Disparador para actualizar automáticamente 'updated_at'
    -- (La función trigger_set_timestamp() ya fue creada)
    CREATE TRIGGER set_opportunities_updated_at
    BEFORE UPDATE ON opportunities
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
    
    -- Índices
    CREATE INDEX idx_opportunities_user_id ON opportunities(user_id);
    CREATE INDEX idx_opportunities_symbol ON opportunities(symbol);
    CREATE INDEX idx_opportunities_status ON opportunities(status);
    CREATE INDEX idx_opportunities_source_type ON opportunities(source_type);
    CREATE INDEX idx_opportunities_detected_at ON opportunities(detected_at DESC);
    CREATE INDEX idx_opportunities_expires_at ON opportunities(expires_at DESC);
    CREATE INDEX idx_opportunities_priority_score ON opportunities(system_calculated_priority_score DESC);
    
    -- Índice GIN en linked_trade_ids (opcional para v1.0, considerar si hay consultas frecuentes usando este array para buscar la oportunidad desde un trade_id).
    -- La condición 'WHERE linked_trade_ids IS NOT NULL AND array_length(linked_trade_ids, 1) > 0' optimiza el índice.
    -- CREATE INDEX idx_opportunities_linked_trade_ids_gin ON opportunities USING GIN (linked_trade_ids) WHERE linked_trade_ids IS NOT NULL AND array_length(linked_trade_ids, 1) > 0;
    
    -- Índices compuestos opcionales (evaluar según patrones de consulta más comunes):
    -- CREATE INDEX idx_opp_user_status_detected ON opportunities(user_id, status, detected_at DESC); -- Para "mis oportunidades nuevas/pendientes ordenadas por detección"
    -- CREATE INDEX idx_opp_user_status_priority ON opportunities(user_id, status, system_calculated_priority_score DESC); -- Para "mis oportunidades activas más prioritarias"

#### portfolio_snapshots

    -- Tabla: portfolio_snapshots
    
    CREATE TABLE portfolio_snapshots (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES user_configurations(user_id) ON DELETE CASCADE,
        snapshot_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()), -- Momento en que se tomó el snapshot.
        mode VARCHAR(20) NOT NULL CHECK (mode IN ('paper', 'real', 'backtest')),
    
        primary_quote_currency VARCHAR(10) NOT NULL, -- Ej: "USDT", "USD". Moneda base para todos los valores monetarios.
    
        total_portfolio_value DECIMAL(20, 8) NOT NULL, -- Valor total del portafolio en primary_quote_currency.
        total_cash_balance DECIMAL(20, 8), 
        total_spot_assets_value DECIMAL(20, 8), 
        total_derivatives_value DECIMAL(20, 8), 
        
        cash_conversion_rates_used JSONB, -- Ej: {"EUR_USDT": 1.08, "USD_USDT": 1.00}
        cash_balances JSONB NOT NULL, -- Array de objetos: { assetSymbol: string, amount: number }. Ej: [{ "assetSymbol": "USDT", "amount": 1000.50 }]
        
        asset_holdings JSONB NOT NULL, -- Array de objetos AssetHolding. Consultas internas vía operadores JSONB o en la app. Normalización futura si es necesario.
                                       -- Ej: [{ "assetSymbol": "BTC", "quantity": 0.5, "averageBuyPrice": 30000, "taxLots": [...] }, ...]
        derivative_position_holdings JSONB, -- Array de objetos DerivativePositionHolding. Misma consideración que asset_holdings.
    
        capital_inflow_since_last_snapshot DECIMAL(20, 8), 
        capital_outflow_since_last_snapshot DECIMAL(20, 8), 
        
        cumulative_pnl DECIMAL(20, 8), 
        cumulative_pnl_percentage DECIMAL(10, 4), 
        pnl_since_last_snapshot DECIMAL(20, 8), 
        
        sharpe_ratio_period DECIMAL(10, 4), 
        sortino_ratio_period DECIMAL(10, 4), 
        max_drawdown_period_percentage DECIMAL(10, 4), 
        
        total_value_in_open_spot_positions DECIMAL(20, 8), 
        
        source VARCHAR(50) NOT NULL CHECK (source IN (
            'scheduled_daily', 
            'after_trade_close', 
            'user_request', 
            'initial_setup', 
            'capital_flow_event' 
        )),
        snapshot_type VARCHAR(50) CHECK (snapshot_type IN (
            'actual_historical', 
            'projected_forecast', 
            'simulated_what_if', 
            'backtest_result'
        )),
    
        target_asset_allocation JSONB, -- Ej: {"BTC": 0.4, "ETH": 0.3, "CASH_USDT": 0.3}
        notes TEXT, 
        
        created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL -- Momento en que se creó el registro del snapshot en la BD.
    );
    
    -- Índices
    CREATE INDEX idx_portfolio_snapshots_user_id ON portfolio_snapshots(user_id);
    CREATE INDEX idx_portfolio_snapshots_snapshot_at ON portfolio_snapshots(snapshot_at DESC); 
    CREATE INDEX idx_portfolio_snapshots_user_snapshot_at ON portfolio_snapshots(user_id, snapshot_at DESC); 
    CREATE INDEX idx_portfolio_snapshots_mode ON portfolio_snapshots(mode);
    CREATE INDEX idx_portfolio_snapshots_source ON portfolio_snapshots(source);
    CREATE INDEX idx_portfolio_snapshots_snapshot_type ON portfolio_snapshots(snapshot_type);
    
    -- Índices GIN opcionales para consultas dentro de los JSONB (considerar para optimizaciones futuras):
    -- CREATE INDEX idx_ps_asset_holdings_gin ON portfolio_snapshots USING GIN (asset_holdings);
    -- CREATE INDEX idx_ps_derivative_holdings_gin ON portfolio_snapshots USING GIN (derivative_position_holdings);
