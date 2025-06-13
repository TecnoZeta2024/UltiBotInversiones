"""
Modelos de dominio para el sistema de IA.

Este módulo define los tipos de datos puros utilizados por el AI Orchestrator Service.
Mantiene la pureza del dominio sin importar librerías externas.
"""

from datetime import datetime, timezone # ADDED timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator # MODIFIED validator
# from pydantic_settings import SettingsConfigDict # REMOVED - only needed for BaseSettings


class AIModelType(str, Enum):
    """Tipos de modelos de IA soportados."""
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_FLASH = "gemini-1.5-flash"
    GEMINI_FLASH_8B = "gemini-1.5-flash-8b"


class AIRequestPriority(str, Enum):
    """Prioridades para requests de IA."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AIProcessingStage(str, Enum):
    """Etapas del flujo de procesamiento de IA."""
    PLANNING = "planning"
    EXECUTION = "execution"
    SYNTHESIS = "synthesis"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolAction(BaseModel):
    """Acción de herramienta a ejecutar."""
    
    name: str = Field(..., description="Nombre de la herramienta")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros de la herramienta")
    priority: AIRequestPriority = Field(default=AIRequestPriority.MEDIUM, description="Prioridad de ejecución")
    timeout_seconds: Optional[int] = Field(default=30, description="Timeout en segundos")
    
    model_config = {"frozen": True} # MODIFIED


class ToolExecutionRequest(BaseModel):
    """Solicitud para ejecutar una herramienta."""
    tool_name: str
    parameters: Dict[str, Any]

    model_config = {"frozen": True} # MODIFIED


class ToolExecutionResult(BaseModel):
    """Resultado de la ejecución de una herramienta."""
    
    tool_name: str = Field(..., description="Nombre de la herramienta ejecutada")
    success: bool = Field(..., description="Si la ejecución fue exitosa")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Datos del resultado")
    error: Optional[str] = Field(default=None, description="Mensaje de error si falló")
    execution_time_ms: float = Field(..., description="Tiempo de ejecución en milisegundos")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp de ejecución") # MODIFIED
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")
    
    model_config = {"frozen": True} # MODIFIED


class AIAnalysisRequest(BaseModel):
    """Request para análisis de IA."""
    
    request_id: UUID = Field(default_factory=uuid4, description="ID único del request")
    opportunity_id: str = Field(..., description="ID de la oportunidad a analizar")
    market_data: Dict[str, Any] = Field(..., description="Datos de mercado")
    strategy_context: Optional[Dict[str, Any]] = Field(default=None, description="Contexto de estrategia")
    priority: AIRequestPriority = Field(default=AIRequestPriority.MEDIUM, description="Prioridad del análisis")
    max_tools_per_stage: int = Field(default=3, description="Máximo número de herramientas por etapa")
    timeout_seconds: int = Field(default=300, description="Timeout total en segundos")
    
    @field_validator('opportunity_id') # MODIFIED
    @classmethod # ADDED
    def validate_opportunity_id(cls, v: str) -> str: # ADDED type hints
        if not v or len(v.strip()) == 0:
            raise ValueError("opportunity_id no puede estar vacío")
        return v.strip()


class AIAnalysisPlan(BaseModel):
    """Plan de análisis generado por IA."""
    
    plan_id: UUID = Field(default_factory=uuid4, description="ID único del plan")
    request_id: UUID = Field(..., description="ID del request original")
    reasoning: str = Field(..., description="Razonamiento del plan")
    tool_actions: List[ToolAction] = Field(default_factory=list, description="Acciones de herramientas planificadas")
    estimated_duration_ms: int = Field(..., description="Duración estimada en milisegundos")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confianza en el plan")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp de creación") # MODIFIED
    
    def add_tool_action(self, action: ToolAction) -> None:
        """Añade una acción de herramienta al plan."""
        # Crear una nueva lista para mantener inmutabilidad
        self.__dict__['tool_actions'] = self.tool_actions + [action]
    
    def add_result(self, result: ToolExecutionResult) -> None:
        """Añade un resultado de herramienta al plan."""
        # Este método se mantiene para compatibilidad, pero en un modelo inmutable
        # los resultados se manejarían en una estructura separada
        pass


class AIAnalysisResult(BaseModel):
    """Resultado final del análisis de IA."""
    
    result_id: UUID = Field(default_factory=uuid4, description="ID único del resultado")
    request_id: UUID = Field(..., description="ID del request original")
    plan_id: Optional[UUID] = Field(None, description="ID del plan ejecutado")
    stage: AIProcessingStage = Field(..., description="Etapa de procesamiento")
    
    # Resultados del análisis
    recommendation: str = Field(..., description="Recomendación principal")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza en la recomendación")
    reasoning: Optional[str] = Field(None, description="Razonamiento detallado de la recomendación.")
    risk_assessment: Optional[str] = Field(None, description="Evaluación de riesgo")
    
    # Datos técnicos
    tool_results: List[ToolExecutionResult] = Field(default_factory=list, description="Resultados de herramientas")
    total_execution_time_ms: float = Field(..., description="Tiempo total de ejecución")
    tokens_used: int = Field(default=0, description="Tokens consumidos")
    
    # Metadatos
    ai_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos de la ejecución de IA")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp de creación") # MODIFIED
    model_used: AIModelType = Field(default=AIModelType.GEMINI_PRO, description="Modelo de IA utilizado")
    
    model_config = {"frozen": True} # MODIFIED
    
    @field_validator('confidence') # MODIFIED
    @classmethod # ADDED
    def validate_confidence_score(cls, v: float) -> float: # ADDED type hints
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence_score debe estar entre 0.0 y 1.0")
        return v


class AIInteractionLog(BaseModel):
    """Log de interacción con IA para debugging."""
    
    log_id: UUID = Field(default_factory=uuid4, description="ID único del log")
    request_id: UUID = Field(..., description="ID del request")
    interaction_type: str = Field(..., description="Tipo de interacción")
    stage: AIProcessingStage = Field(..., description="Etapa de procesamiento")
    
    # Datos de la interacción
    prompt_template: str = Field(..., description="Template del prompt utilizado")
    prompt_variables: Dict[str, Any] = Field(default_factory=dict, description="Variables del prompt")
    rendered_prompt: str = Field(..., description="Prompt final renderizado")
    
    # Respuesta del modelo
    ai_response: str = Field(..., description="Respuesta del modelo de IA")
    tokens_input: int = Field(default=0, description="Tokens de entrada")
    tokens_output: int = Field(default=0, description="Tokens de salida")
    
    # Metadatos
    model_used: AIModelType = Field(..., description="Modelo utilizado")
    execution_time_ms: float = Field(..., description="Tiempo de ejecución")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp") # MODIFIED
    
    model_config = {"frozen": True} # MODIFIED


class TradingOpportunity(BaseModel):
    """Oportunidad de trading identificada por el sistema."""
    
    opportunity_id: str = Field(default_factory=lambda: str(uuid4()), description="ID único de la oportunidad")
    symbol: str = Field(..., description="Símbolo del asset")
    strategy_name: str = Field(..., description="Nombre de la estrategia que detectó la oportunidad")
    
    # Datos de mercado
    current_price: Optional[Decimal] = Field(None, description="Precio actual")
    volume_24h: Optional[Decimal] = Field(None, description="Volumen 24h")
    price_change_24h: Optional[float] = Field(None, description="Cambio de precio 24h (%)")
    market_context: Optional[Dict[str, Any]] = Field(default=None, description="Contexto de mercado adicional")
    
    # Análisis técnico
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza en la oportunidad")
    technical_indicators: Dict[str, Any] = Field(default_factory=dict, description="Indicadores técnicos")
    signal_strength: Optional[float] = Field(None, ge=0.0, le=1.0, description="Fuerza de la señal")
    
    # Contexto
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp de detección") # MODIFIED
    expires_at: Optional[datetime] = Field(default=None, description="Timestamp de expiración")
    risk_level: str = Field("MEDIUM", description="Nivel de riesgo estimado")
    expected_profit: Optional[float] = Field(None, description="Beneficio esperado")
    timeframe: Optional[str] = Field(None, description="Timeframe de la oportunidad")
    
    model_config = { # MODIFIED
        "frozen": True,
        "json_encoders": {Decimal: lambda d: float(d)} # ADDED json_encoders for Decimal
    }
    
    # def dict(self, **kwargs) -> Dict[str, Any]: # REMOVED custom dict
    #     """Override para serialización personalizada."""
    #     data = super().model_dump(**kwargs) # CHANGED to model_dump
    #     # Convertir Decimal a float para JSON serialization
    #     # This should now be handled by json_encoders in model_config when using model_dump(mode='json')
    #     if data.get('current_price') is not None and isinstance(data['current_price'], Decimal):
    #         data['current_price'] = float(data['current_price'])
    #     if data.get('volume_24h') is not None and isinstance(data['volume_24h'], Decimal):
    #         data['volume_24h'] = float(data['volume_24h'])
    #     return data


class AISystemMetrics(BaseModel):
    """Métricas del sistema de IA."""
    
    # Métricas de rendimiento
    avg_response_time_ms: float = Field(..., description="Tiempo promedio de respuesta")
    total_requests: int = Field(default=0, description="Total de requests procesados")
    successful_requests: int = Field(default=0, description="Requests exitosos")
    failed_requests: int = Field(default=0, description="Requests fallidos")
    
    # Métricas de recursos
    total_tokens_used: int = Field(default=0, description="Total de tokens consumidos")
    avg_tokens_per_request: float = Field(default=0.0, description="Promedio de tokens por request")
    
    # Métricas de calidad
    avg_confidence_score: float = Field(default=0.0, description="Confianza promedio")
    rate_limit_hits: int = Field(default=0, description="Veces que se alcanzó rate limit")
    
    # Timestamp
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp de medición") # MODIFIED
    
    model_config = {"frozen": True} # MODIFIED
    
    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def failure_rate(self) -> float:
        """Calcula la tasa de fallo."""
        return 1.0 - self.success_rate


class Recommendation(str, Enum):
    """Recomendaciones de trading."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    SHORT = "SHORT"
    CLOSE = "CLOSE"
    ERROR = "ERROR"

class TradingAIResponse(AIAnalysisResult):
    """
    Respuesta estructurada del AI Orchestrator para decisiones de trading.
    Extiende AIAnalysisResult con campos y métodos específicos de trading.
    """
    entry_price: Optional[Decimal] = Field(None, description="Precio de entrada recomendado")
    stop_loss: Optional[Decimal] = Field(None, description="Precio de Stop Loss recomendado")
    take_profit: Optional[Decimal] = Field(None, description="Precio de Take Profit recomendado")
    risk_level: Optional[str] = Field(None, description="Nivel de riesgo de la operación (LOW, MEDIUM, HIGH)")
    timeframe: Optional[str] = Field(None, description="Timeframe de la oportunidad (e.g., '1m', '5m', '1h')")
    analysis_id: UUID = Field(default_factory=uuid4, description="ID único de este análisis de trading")

    # Sobrescribir el tipo de recomendación para usar el Enum
    recommendation: Recommendation = Field(..., description="Recomendación principal de trading")

    model_config = { # MODIFIED: SettingsConfigDict is for BaseSettings
        "frozen": True,
        "extra": "allow"
    }

    @model_validator(mode='after')
    def validate_prices(self) -> 'TradingAIResponse':
        """Valida que los precios sean positivos si están presentes."""
        if self.entry_price is not None and self.entry_price <= 0:
            raise ValueError("Entry price must be positive.")
        if self.stop_loss is not None and self.stop_loss <= 0:
            raise ValueError("Stop loss must be positive.")
        if self.take_profit is not None and self.take_profit <= 0:
            raise ValueError("Take profit must be positive.")
        return self

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Indica si la confianza de la recomendación es alta."""
        return self.confidence >= threshold

    def is_suitable_for_real_trading(self, confidence_threshold: float = 0.95) -> bool:
        """Indica si la recomendación es apta para trading real (alta confianza)."""
        return self.confidence >= confidence_threshold and self.recommendation != Recommendation.ERROR

    def get_summary(self) -> str:
        """Genera un resumen conciso de la recomendación."""
        summary = f"Recomendación: {self.recommendation.value} (Confianza: {self.confidence:.1%})."
        if self.entry_price:
            summary += f" Entrada: ${self.entry_price:,.2f}."
        if self.stop_loss:
            summary += f" SL: ${self.stop_loss:,.2f}."
        if self.take_profit:
            summary += f" TP: ${self.take_profit:,.2f}."
        if self.risk_level:
            summary += f" Riesgo: {self.risk_level}."
        return summary

    def to_telegram_message(self) -> str:
        """Formatea la respuesta para un mensaje de Telegram."""
        msg = (
            f"📊 **Análisis de IA para Trading**\n\n"
            f"🎯 **Recomendación:** `{self.recommendation.value}`\n"
            f"📈 **Confianza:** `{self.confidence:.1%}`\n"
            f"🧠 **Razonamiento:** {self.reasoning or 'N/A'}\n"
        )
        if self.entry_price:
            msg += f"💰 **Precio de Entrada:** `${self.entry_price:,.2f}`\n"
        if self.stop_loss:
            msg += f"🛑 **Stop Loss:** `${self.stop_loss:,.2f}`\n"
        if self.take_profit:
            msg += f"🎯 **Take Profit:** `${self.take_profit:,.2f}`\n"
        if self.risk_level:
            msg += f"📊 **Nivel de Riesgo:** `{self.risk_level}`\n"
        if self.timeframe:
            msg += f"⏰ **Timeframe:** `{self.timeframe}`\n"
        if self.warnings:
            msg += f"⚠️ **Advertencias:** {', '.join(self.warnings)}\n"
        
        msg += f"\n_ID de Análisis: {self.analysis_id}_"
        return msg

class OpportunityData(BaseModel):
    """Datos de oportunidad de trading para análisis de IA."""
    
    symbol: str = Field(..., description="Símbolo del asset")
    price: Decimal = Field(..., description="Precio actual")
    volume: Optional[Decimal] = Field(None, description="Volumen")
    change_24h: Optional[float] = Field(None, description="Cambio 24h (%)")
    market_cap: Optional[Decimal] = Field(None, description="Market cap")
    
    # Indicadores técnicos
    rsi: Optional[float] = Field(None, description="RSI")
    ma_20: Optional[Decimal] = Field(None, description="Media móvil 20")
    ma_50: Optional[Decimal] = Field(None, description="Media móvil 50")
    
    # Metadatos
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp de los datos") # MODIFIED
    source: str = Field(default="market_scanner", description="Fuente de los datos")
    
    model_config = { # MODIFIED
        "frozen": True,
        "json_encoders": {Decimal: lambda d: float(d)} # ADDED json_encoders for Decimal
    }

    # def dict(self, **kwargs) -> Dict[str, Any]: # REMOVED custom dict
    #     """Override para serialización personalizada."""
    #     data = super().model_dump(**kwargs) # CHANGED to model_dump
    #     # Convertir Decimal a float para JSON serialization
    #     # This should now be handled by json_encoders in model_config when using model_dump(mode='json')
    #     for field_name in ['price', 'volume', 'market_cap', 'ma_20', 'ma_50']:
    #         if data.get(field_name) is not None and isinstance(data[field_name], Decimal):
    #             data[field_name] = float(data[field_name])
    #     return data

# Aliases para compatibilidad
AIRequest = AIAnalysisRequest
AIResult = AIAnalysisResult
ToolResult = ToolExecutionResult
OpportunityModel = TradingOpportunity  # Alias adicional
