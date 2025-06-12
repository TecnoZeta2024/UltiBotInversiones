"""
Modelos de dominio para el sistema de IA.

Este módulo define los tipos de datos puros utilizados por el AI Orchestrator Service.
Mantiene la pureza del dominio sin importar librerías externas.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


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
    
    class Config:
        frozen = True


class ToolExecutionRequest(BaseModel):
    """Solicitud para ejecutar una herramienta."""
    tool_name: str
    parameters: Dict[str, Any]

    class Config:
        frozen = True


class ToolExecutionResult(BaseModel):
    """Resultado de la ejecución de una herramienta."""
    
    tool_name: str = Field(..., description="Nombre de la herramienta ejecutada")
    success: bool = Field(..., description="Si la ejecución fue exitosa")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Datos del resultado")
    error: Optional[str] = Field(default=None, description="Mensaje de error si falló")
    execution_time_ms: float = Field(..., description="Tiempo de ejecución en milisegundos")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de ejecución")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")
    
    class Config:
        frozen = True


class AIAnalysisRequest(BaseModel):
    """Request para análisis de IA."""
    
    request_id: UUID = Field(default_factory=uuid4, description="ID único del request")
    opportunity_id: str = Field(..., description="ID de la oportunidad a analizar")
    market_data: Dict[str, Any] = Field(..., description="Datos de mercado")
    strategy_context: Optional[Dict[str, Any]] = Field(default=None, description="Contexto de estrategia")
    priority: AIRequestPriority = Field(default=AIRequestPriority.MEDIUM, description="Prioridad del análisis")
    max_tools_per_stage: int = Field(default=3, description="Máximo número de herramientas por etapa")
    timeout_seconds: int = Field(default=300, description="Timeout total en segundos")
    
    @validator('opportunity_id')
    def validate_opportunity_id(cls, v):
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
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de creación")
    
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
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de creación")
    model_used: AIModelType = Field(default=AIModelType.GEMINI_PRO, description="Modelo de IA utilizado")
    
    class Config:
        frozen = True
    
    @validator('confidence')
    def validate_confidence_score(cls, v):
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
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")
    
    class Config:
        frozen = True


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
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de detección")
    expires_at: Optional[datetime] = Field(default=None, description="Timestamp de expiración")
    risk_level: str = Field("MEDIUM", description="Nivel de riesgo estimado")
    expected_profit: Optional[float] = Field(None, description="Beneficio esperado")
    timeframe: Optional[str] = Field(None, description="Timeframe de la oportunidad")
    
    class Config:
        frozen = True
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Override para serialización personalizada."""
        data = super().dict(**kwargs)
        # Convertir Decimal a float para JSON serialization
        if data.get('current_price') is not None:
            data['current_price'] = float(data['current_price'])
        if data.get('volume_24h') is not None:
            data['volume_24h'] = float(data['volume_24h'])
        return data


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
    measured_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de medición")
    
    class Config:
        frozen = True
    
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
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de los datos")
    source: str = Field(default="market_scanner", description="Fuente de los datos")
    
    class Config:
        frozen = True
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Override para serialización personalizada."""
        data = super().dict(**kwargs)
        # Convertir Decimal a float para JSON serialization
        for field in ['price', 'volume', 'market_cap', 'ma_20', 'ma_50']:
            if data.get(field) is not None:
                data[field] = float(data[field])
        return data

# Aliases para compatibilidad
AIRequest = AIAnalysisRequest
AIResult = AIAnalysisResult
ToolResult = ToolExecutionResult
OpportunityModel = TradingOpportunity  # Alias adicional
