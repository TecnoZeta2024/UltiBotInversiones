# PLAN DE EJECUCIÓN GRANULAR: ULTIBOTINVERSIONES

**Versión:** 1.0  
**Fecha:** 11 de junio de 2025  
**Autor:** Cline, Arquitecto de Software Principal  
**Objetivo:** Traducir el manifiesto `CONSEJOS_GEMINI.MD` en tareas de codificación atómicas

---

## ESTRUCTURA DEL PLAN

Este plan organiza la implementación en **4 Fases** siguiendo la hoja de ruta del manifiesto:

- **FASE 1:** Cimientos (Arquitectura Hexagonal + CQRS + EventBroker)
- **FASE 2:** Núcleo Funcional (Estrategias + UI MVVM)
- **FASE 3:** Inteligencia (AI Orchestrator + MCP Tools + Prompt Studio)
- **FASE 4:** Expansión y Pulido (Bibliotecas completas + Integración)

Cada fase se divide en **Épicas** (componentes arquitectónicos mayores) y estas en **Tareas** atómicas con criterios de aceptación específicos.

---

# FASE 1: CIMIENTOS (2 Semanas)
*Refactorizar a Arquitectura Hexagonal, CQRS y EventBroker*

## ÉPICA 1.1: Establecimiento de Arquitectura Hexagonal

### **Tarea 1.1.1: Creación del Núcleo de Dominio Puro**

**Archivo(s):** 
- `src/ultibot_backend/core/ports.py`
- `src/ultibot_backend/core/domain_models/__init__.py`
- `src/ultibot_backend/core/domain_models/trading.py`
- `src/ultibot_backend/core/domain_models/portfolio.py`
- `src/ultibot_backend/core/domain_models/market.py`

**Clase/Función:** Interfaces de puertos y modelos de dominio

**Descripción Técnica:** 
Crear las interfaces (puertos) que definen los contratos de comunicación del núcleo hacia el exterior, sin importar ninguna librería externa. Definir modelos Pydantic puros para entidades del dominio.

```python
# Pseudocódigo para ports.py
from abc import ABC, abstractmethod
from typing import Protocol

class IMarketDataProvider(Protocol):
    async def get_ticker(self, symbol: str) -> TickerData
    async def get_klines(self, symbol: str, interval: str) -> list[KlineData]

class IPersistencePort(Protocol):
    async def save_trade(self, trade: Trade) -> TradeId
    async def get_portfolio(self, user_id: UserId) -> Portfolio

class INotificationPort(Protocol):
    async def send_alert(self, message: str, priority: Priority) -> None
```

**Criterios de Aceptación (DoD):**
- [ ] Archivo `ports.py` define mínimo 8 interfaces: IMarketDataProvider, IPersistencePort, INotificationPort, IOrderExecutionPort, IToolExecutionPort, IAPIPort, IEventPublisher, ICredentialProvider
- [ ] Modelos de dominio utilizan solo Pydantic y tipos Python nativos
- [ ] Cero imports de fastapi, sqlalchemy, o cualquier framework externo en `/core`
- [ ] Todos los puertos usan async/await por defecto
- [ ] Documentación completa con docstrings estilo Google

**Comentarios y Riesgos:** 
Crítico mantener pureza del dominio. Validar constantemente que no hay imports de frameworks.

---

### **Tarea 1.1.2: Implementación de Servicios del Núcleo**

**Archivo(s):**
- `src/ultibot_backend/core/services/__init__.py`
- `src/ultibot_backend/core/services/trading_engine.py`
- `src/ultibot_backend/core/services/portfolio_manager.py`
- `src/ultibot_backend/core/services/event_broker.py`

**Clase/Función:** TradingEngineService, PortfolioManagerService, EventBrokerService

**Descripción Técnica:**
Implementar los servicios del núcleo que contienen la lógica de negocio pura. Estos servicios reciben puertos inyectados y publican eventos.

```python
# Pseudocódigo para trading_engine.py
class TradingEngineService:
    def __init__(
        self,
        market_provider: IMarketDataProvider,
        persistence: IPersistencePort,
        event_publisher: IEventPublisher
    ):
        self._market = market_provider
        self._persistence = persistence
        self._events = event_publisher
    
    async def execute_trade(self, opportunity: Opportunity) -> TradeResult:
        # Lógica pura sin dependencias externas
        trade = await self._create_trade(opportunity)
        result = await self._persistence.save_trade(trade)
        await self._events.publish(TradeExecutedEvent(trade_id=result.id))
        return result
```

**Criterios de Aceptación (DoD):**
- [ ] TradingEngineService implementa lógica de ejecución de trades
- [ ] PortfolioManagerService gestiona balances y P&L
- [ ] EventBrokerService maneja pub/sub sin dependencias externas
- [ ] Todos los servicios reciben dependencias por inyección
- [ ] Cobertura de tests unitarios >90% con mocks de puertos
- [ ] Performance: operaciones core <50ms sin I/O

**Comentarios y Riesgos:**
EventBroker es crítico para desacoplamiento. Debe ser in-memory inicialmente pero extensible.

---

### **Tarea 1.1.3: Creación de Adaptadores para APIs Externas**

**Archivo(s):**
- `src/ultibot_backend/adapters/binance_adapter.py`
- `src/ultibot_backend/adapters/persistence_adapter.py`
- `src/ultibot_backend/adapters/telegram_adapter.py`
- `src/ultibot_backend/adapters/mobula_adapter.py`

**Clase/Función:** BinanceMarketAdapter, PostgresPersistenceAdapter, TelegramNotificationAdapter

**Descripción Técnica:**
Implementar adaptadores concretos que implementan los puertos definidos. Estos sí pueden importar librerías externas.

```python
# Pseudocódigo para binance_adapter.py
import httpx
from ..core.ports import IMarketDataProvider

class BinanceMarketAdapter(IMarketDataProvider):
    def __init__(self, credentials: BinanceCredentials):
        self._client = httpx.AsyncClient()
        self._creds = credentials
    
    async def get_ticker(self, symbol: str) -> TickerData:
        response = await self._client.get(f"/api/v3/ticker/24hr?symbol={symbol}")
        return TickerData.parse_obj(response.json())
```

**Criterios de Aceptación (DoD):**
- [ ] BinanceAdapter implementa IMarketDataProvider e IOrderExecutionPort
- [ ] PostgresAdapter implementa IPersistencePort con conexión Supabase
- [ ] TelegramAdapter implementa INotificationPort
- [ ] MobulaAdapter implementa IMarketDataProvider (secundario)
- [ ] Gestión de errores y reintentos en todos los adaptadores
- [ ] Rate limiting implementado según docs de cada API
- [ ] Tests de integración con mocks de respuestas HTTP

**Comentarios y Riesgos:**
Gestión de credenciales debe ser segura desde el inicio. Rate limiting crítico para evitar bloqueos.

---

## ÉPICA 1.2: Implementación de CQRS

### **Tarea 1.2.1: Estructura de Comandos y Consultas**

**Archivo(s):**
- `src/ultibot_backend/core/commands/__init__.py`
- `src/ultibot_backend/core/commands/trading_commands.py`
- `src/ultibot_backend/core/queries/__init__.py`
- `src/ultibot_backend/core/queries/portfolio_queries.py`

**Clase/Función:** PlaceOrderCommand, ActivateStrategyCommand, GetPortfolioQuery, GetTradeHistoryQuery

**Descripción Técnica:**
Definir comandos (mutaciones) y consultas (lecturas) como modelos Pydantic. Separar claramente operaciones de escritura y lectura.

```python
# Pseudocódigo para trading_commands.py
class PlaceOrderCommand(BaseModel):
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Optional[Decimal]
    order_type: OrderType
    strategy_id: Optional[str]

class ActivateStrategyCommand(BaseModel):
    strategy_name: str
    parameters: dict[str, Any]
    mode: TradingMode  # PAPER | REAL
```

**Criterios de Aceptación (DoD):**
- [ ] Mínimo 5 comandos definidos: PlaceOrderCommand, CancelOrderCommand, ActivateStrategyCommand, DeactivateStrategyCommand, UpdateConfigCommand
- [ ] Mínimo 5 consultas definidas: GetPortfolioQuery, GetTradeHistoryQuery, GetStrategyPerformanceQuery, GetMarketDataQuery, GetConfigQuery
- [ ] Todos son modelos Pydantic con validación estricta
- [ ] Documentación clara del propósito de cada comando/consulta
- [ ] Separación clara: comandos mutan, consultas solo leen

**Comentarios y Riesgos:**
CQRS debe ser evidente en la estructura. Comandos y consultas nunca deben mezclarse.

---

### **Tarea 1.2.2: Handlers para Comandos y Consultas**

**Archivo(s):**
- `src/ultibot_backend/core/handlers/command_handlers.py`
- `src/ultibot_backend/core/handlers/query_handlers.py`
- `src/ultibot_backend/core/handlers/handler_registry.py`

**Clase/Función:** TradingCommandHandler, PortfolioQueryHandler, HandlerRegistry

**Descripción Técnica:**
Implementar handlers que procesan comandos y consultas. Usar patrón Registry para dispatch automático.

```python
# Pseudocódigo para command_handlers.py
class TradingCommandHandler:
    def __init__(self, trading_engine: TradingEngineService):
        self._engine = trading_engine
    
    async def handle_place_order(self, cmd: PlaceOrderCommand) -> CommandResult:
        opportunity = self._create_opportunity_from_command(cmd)
        result = await self._engine.execute_trade(opportunity)
        return CommandResult(success=True, data=result)
```

**Criterios de Aceptación (DoD):**
- [ ] Handler para cada comando definido en Tarea 1.2.1
- [ ] Handler para cada consulta definida en Tarea 1.2.1
- [ ] HandlerRegistry permite dispatch automático por tipo
- [ ] Todos los handlers son async y devuelven tipos tipados
- [ ] Manejo de errores consistente con excepciones específicas
- [ ] Logging de auditoría en todos los comandos

**Comentarios y Riesgos:**
Registry debe ser thread-safe. Performance crítica en query handlers.

---

## ÉPICA 1.3: Sistema de Eventos Asíncrono

### **Tarea 1.3.1: Definición de Eventos del Dominio**

**Archivo(s):**
- `src/ultibot_backend/core/events/__init__.py`
- `src/ultibot_backend/core/events/trading_events.py`
- `src/ultibot_backend/core/events/portfolio_events.py`
- `src/ultibot_backend/core/events/strategy_events.py`

**Clase/Función:** TradeExecutedEvent, PortfolioUpdatedEvent, StrategyActivatedEvent

**Descripción Técnica:**
Definir eventos inmutables que representan hechos que han ocurrido en el sistema. Base para auditabilidad completa.

```python
# Pseudocódigo para trading_events.py
class TradeExecutedEvent(BaseEvent):
    trade_id: TradeId
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    strategy_id: Optional[str]
    
    class Config:
        frozen = True  # Inmutable
```

**Criterios de Aceptación (DoD):**
- [ ] Mínimo 8 eventos definidos cubriendo trading, portfolio, strategies, AI
- [ ] Todos los eventos son inmutables (frozen=True)
- [ ] Timestamp automático en BaseEvent
- [ ] Versionado de eventos para evolución futura
- [ ] Serialización JSON para persistencia opcional

**Comentarios y Riesgos:**
Eventos son la fuente de verdad del sistema. Diseño cuidadoso para evitar breaking changes.

---

### **Tarea 1.3.2: EventBroker Asíncrono In-Memory**

**Archivo(s):**
- `src/ultibot_backend/core/services/event_broker.py`
- `src/ultibot_backend/core/services/event_dispatcher.py`

**Clase/Función:** AsyncEventBroker, EventDispatcher

**Descripción Técnica:**
Implementar broker de eventos completamente asíncrono con soporte para suscriptores múltiples y garantías de entrega.

```python
# Pseudocódigo para event_broker.py
class AsyncEventBroker:
    def __init__(self):
        self._subscribers: dict[Type[BaseEvent], list[EventHandler]] = defaultdict(list)
        self._queue: asyncio.Queue = asyncio.Queue()
    
    async def publish(self, event: BaseEvent) -> None:
        await self._queue.put(event)
        await self._dispatch_event(event)
    
    async def subscribe(self, event_type: Type[BaseEvent], handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)
```

**Criterios de Aceptación (DoD):**
- [ ] Pub/Sub completamente asíncrono
- [ ] Soporte para múltiples suscriptores por evento
- [ ] Cola de eventos con garantía de orden FIFO
- [ ] Manejo de errores: un handler fallido no afecta otros
- [ ] Métricas: eventos publicados, handlers ejecutados, errores
- [ ] Performance: <10ms para publish, <100ms para dispatch
- [ ] Tests exhaustivos con múltiples suscriptores concurrentes

**Comentarios y Riesgos:**
Performance crítica. Considerar circuit breaker para handlers problemáticos.

---

# FASE 2: NÚCLEO FUNCIONAL (1 Semana)
*Motor de Estrategias Plug-and-Play y UI MVVM*

## ÉPICA 2.1: Motor de Estrategias Dinámico

### **Tarea 2.1.1: Infraestructura Base de Estrategias**

**Archivo(s):**
- `src/ultibot_backend/strategies/__init__.py`
- `src/ultibot_backend/strategies/base_strategy.py`
- `src/ultibot_backend/strategies/strategy_loader.py`
- `src/ultibot_backend/strategies/strategy_registry.py`

**Clase/Función:** BaseStrategy, StrategyLoader, StrategyRegistry

**Descripción Técnica:**
Crear la infraestructura que permite carga dinámica de estrategias. BaseStrategy define la interfaz común, StrategyLoader escanea el directorio.

```python
# Pseudocódigo para base_strategy.py
class BaseStrategy(ABC):
    def __init__(self, name: str, parameters: StrategyParameters):
        self.name = name
        self.parameters = parameters
    
    @abstractmethod
    async def setup(self, market_data: IMarketDataProvider) -> None:
        pass
    
    @abstractmethod
    async def analyze(self, market_snapshot: MarketSnapshot) -> AnalysisResult:
        pass
    
    @abstractmethod
    async def generate_signal(self, analysis: AnalysisResult) -> Optional[TradingSignal]:
        pass
```

**Criterios de Aceptación (DoD):**
- [ ] BaseStrategy define interfaz completa con setup, analyze, generate_signal
- [ ] StrategyLoader escanea directorio y carga clases dinámicamente
- [ ] StrategyRegistry mantiene estrategias disponibles y activas
- [ ] Soporte para parámetros configurables por estrategia
- [ ] Validación de parámetros con Pydantic
- [ ] Hot-reload opcional para desarrollo
- [ ] Logging detallado del proceso de carga

**Comentarios y Riesgos:**
Seguridad en carga dinámica. Validar que las estrategias son válidas antes de registrar.

---

### **Tarea 2.1.2: Implementación de 3 Estrategias Iniciales**

**Archivo(s):**
- `src/ultibot_backend/strategies/macd_rsi_trend_rider.py`
- `src/ultibot_backend/strategies/bollinger_squeeze_breakout.py`
- `src/ultibot_backend/strategies/triangular_arbitrage.py`

**Clase/Función:** MACDRSITrendRider, BollingerSqueezeBreakout, TriangularArbitrage

**Descripción Técnica:**
Implementar 3 estrategias diversas siguiendo BaseStrategy. Cada una con lógica específica y parámetros configurables.

```python
# Pseudocódigo para macd_rsi_trend_rider.py
class MACDRSITrendRider(BaseStrategy):
    def __init__(self, params: MACDRSIParameters):
        super().__init__("MACD_RSI_Trend_Rider", params)
        self.macd_fast = params.macd_fast_period
        self.macd_slow = params.macd_slow_period
        self.rsi_period = params.rsi_period
    
    async def analyze(self, snapshot: MarketSnapshot) -> AnalysisResult:
        macd_signal = self._calculate_macd(snapshot.klines)
        rsi_value = self._calculate_rsi(snapshot.klines)
        return AnalysisResult(
            confidence=self._calculate_confidence(macd_signal, rsi_value),
            indicators={"macd": macd_signal, "rsi": rsi_value}
        )
```

**Criterios de Aceptación (DoD):**
- [ ] MACDRSITrendRider: Trend following con confirmación RSI
- [ ] BollingerSqueezeBreakout: Mean reversion con volatilidad
- [ ] TriangularArbitrage: Arbitraje entre 3 pares
- [ ] Cada estrategia tiene parámetros configurables documentados
- [ ] Tests unitarios con datos de mercado sintéticos
- [ ] Benchmarks de performance: <200ms por análisis
- [ ] Documentación de la lógica de cada estrategia

**Comentarios y Riesgos:**
Foco en calidad vs. cantidad. Mejor 3 estrategias robustas que 10 básicas.

---

## ÉPICA 2.2: Transformación UI a MVVM

### **Tarea 2.2.1: Arquitectura ViewModel Base**

**Archivo(s):**
- `src/ultibot_ui/viewmodels/__init__.py`
- `src/ultibot_ui/viewmodels/base_viewmodel.py`
- `src/ultibot_ui/viewmodels/dashboard_viewmodel.py`
- `src/ultibot_ui/services/api_client.py`

**Clase/Función:** BaseViewModel, DashboardViewModel, APIClient

**Descripción Técnica:**
Crear arquitectura MVVM clara. BaseViewModel maneja estado y comandos, APIClient comunica con backend.

```python
# Pseudocódigo para base_viewmodel.py
class BaseViewModel(QObject):
    def __init__(self, api_client: APIClient):
        super().__init__()
        self._api = api_client
        self._properties: dict[str, Any] = {}
    
    def bind_property(self, name: str, value: Any) -> None:
        self._properties[name] = value
        self.property_changed.emit(name, value)
    
    @pyqtSlot()
    async def refresh_data(self) -> None:
        # Template method pattern
        await self._do_refresh()
```

**Criterios de Aceptación (DoD):**
- [ ] BaseViewModel con gestión de propiedades y comandos
- [ ] DashboardViewModel expone datos: portfolio_value, active_trades, market_data
- [ ] APIClient abstrae comunicación HTTP con backend
- [ ] Binding reactivo entre ViewModel y Vista
- [ ] Comandos async con manejo de errores
- [ ] Separación completa: Vista no accede directamente al modelo

**Comentarios y Riesgos:**
Threading crítico en PyQt. Asegurar que operaciones async no bloqueen UI.

---

### **Tarea 2.2.2: Sistema de Temas Centralizado**

**Archivo(s):**
- `src/ultibot_ui/resources/themes/dark_theme.qss`
- `src/ultibot_ui/resources/themes/light_theme.qss`
- `src/ultibot_ui/services/theme_manager.py`

**Clase/Función:** ThemeManager

**Descripción Técnica:**
Implementar sistema de temas QSS centralizado con cambio dinámico. Eliminar todos los estilos inline.

```python
# Pseudocódigo para theme_manager.py
class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        self._current_theme = "dark"
        self._themes = {
            "dark": ":/themes/dark_theme.qss",
            "light": ":/themes/light_theme.qss"
        }
    
    def apply_theme(self, theme_name: str) -> None:
        qss_content = self._load_theme_file(theme_name)
        QApplication.instance().setStyleSheet(qss_content)
        self.theme_changed.emit(theme_name)
```

**Criterios de Aceptación (DoD):**
- [ ] dark_theme.qss: Tema oscuro profesional completo
- [ ] light_theme.qss: Alternativa clara (opcional para v1.0)
- [ ] ThemeManager permite cambio dinámico sin restart
- [ ] Todos los widgets principales estilizados: MagicCard, ChartWidget, etc.
- [ ] Colores consistentes definidos como variables QSS
- [ ] Performance: cambio de tema <500ms

**Comentarios y Riesgos:**
QSS puede ser complejo. Priorizar widgets críticos primero.

---

# FASE 3: INTELIGENCIA (2 Semanas)
*AI Orchestrator, MCP Tools y Prompt Studio*

## ÉPICA 3.1: AI Orchestrator Service

### **Tarea 3.1.1: Estructura del AI Orchestrator**

**Archivo(s):**
- `src/ultibot_backend/core/services/ai_orchestrator.py`
- `src/ultibot_backend/adapters/gemini_adapter.py`
- `src/ultibot_backend/core/domain_models/ai_models.py`

**Clase/Función:** AIOrchestratorService, GeminiAdapter, AIAnalysisRequest, AIAnalysisResult

**Descripción Técnica:**
Crear el orquestador central de IA que gestiona prompts, herramientas y síntesis de respuestas usando Gemini.

```python
# Pseudocódigo para ai_orchestrator.py
class AIOrchestratorService:
    def __init__(
        self,
        gemini_adapter: GeminiAdapter,
        tool_hub: MCPToolHub,
        prompt_manager: PromptManager
    ):
        self._gemini = gemini_adapter
        self._tools = tool_hub
        self._prompts = prompt_manager
    
    async def analyze_opportunity(self, opportunity: TradingOpportunity) -> AIAnalysisResult:
        # Fase 1: Planificación
        planning_prompt = self._prompts.get("opportunity_planning")
        tools_available = await self._tools.list_available_tools()
        plan = await self._gemini.generate(planning_prompt, context={
            "opportunity": opportunity.dict(),
            "tools": tools_available
        })
        
        # Fase 2: Ejecución de herramientas
        for tool_action in plan.tool_actions:
            tool_result = await self._tools.execute_tool(
                tool_action.name, 
                tool_action.parameters
            )
            plan.add_result(tool_result)
        
        # Fase 3: Síntesis
        synthesis_prompt = self._prompts.get("opportunity_synthesis")
        final_analysis = await self._gemini.generate(synthesis_prompt, context={
            "opportunity": opportunity.dict(),
            "tool_results": plan.results
        })
        
        return AIAnalysisResult.parse_obj(final_analysis)
```

**Criterios de Aceptación (DoD):**
- [ ] AIOrchestratorService con flujo planificación → ejecución → síntesis
- [ ] GeminiAdapter abstrae interacción con google-generativeai
- [ ] Soporte para prompts templated con variables
- [ ] Manejo de rate limits de Gemini API
- [ ] Logging detallado de interacciones IA para debugging
- [ ] Timeout y circuit breaker para llamadas IA
- [ ] Tests con mocks de respuestas Gemini

**Comentarios y Riesgos:**
Rate limits de Gemini críticos. Implementar cola con prioridades si necesario.

---

### **Tarea 3.1.2: MCP Tool Hub**

**Archivo(s):**
- `src/ultibot_backend/core/services/mcp_tool_hub.py`
- `src/ultibot_backend/adapters/mcp_tools/base_mcp_adapter.py`
- `src/ultibot_backend/adapters/mcp_tools/metatrader_adapter.py`
- `src/ultibot_backend/adapters/mcp_tools/web3_research_adapter.py`

**Clase/Función:** MCPToolHub, BaseMCPAdapter, MetatraderAdapter, Web3ResearchAdapter

**Descripción Técnica:**
Implementar hub centralizado de herramientas MCP con registro dinámico y ejecución abstracta.

```python
# Pseudocódigo para mcp_tool_hub.py
class MCPToolHub:
    def __init__(self):
        self._tools: dict[str, BaseMCPAdapter] = {}
    
    def register_tool(self, name: str, adapter: BaseMCPAdapter) -> None:
        self._tools[name] = adapter
    
    async def list_available_tools(self) -> list[ToolDescriptor]:
        tools = []
        for name, adapter in self._tools.items():
            descriptor = await adapter.get_tool_descriptor()
            tools.append(descriptor)
        return tools
    
    async def execute_tool(self, name: str, parameters: dict[str, Any]) -> ToolResult:
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool {name} not registered")
        
        adapter = self._tools[name]
        return await adapter.execute(parameters)
```

**Criterios de Aceptación (DoD):**
- [ ] MCPToolHub permite registro dinámico de herramientas
- [ ] BaseMCPAdapter define interfaz común: get_descriptor(), execute()
- [ ] Mínimo 2 adaptadores implementados como prueba de concepto
- [ ] Manejo de errores robusto en ejecución de herramientas
- [ ] Timeout configurable por herramienta
- [ ] Logging de uso de herramientas para análisis
- [ ] Validación de parámetros según schema de cada herramienta

**Comentarios y Riesgos:**
Abstracción clave para extensibilidad. Debe ser simple de implementar nuevas herramientas.

---

## ÉPICA 3.2: Prompt Management System

### **Tarea 3.2.1: Base de Datos de Prompts**

**Archivo(s):**
- `supabase/migrations/create_ai_prompts_table.sql`
- `src/ultibot_backend/core/services/prompt_manager.py`
- `src/ultibot_backend/core/domain_models/prompt_models.py`

**Clase/Función:** PromptManager, PromptTemplate, PromptVersion

**Descripción Técnica:**
Mover prompts del código a base de datos con versionado y templating. Permitir edición dinámica.

```sql
-- Pseudocódigo para create_ai_prompts_table.sql
CREATE TABLE ai_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    version INTEGER NOT NULL DEFAULT 1,
    template TEXT NOT NULL,
    variables JSONB,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

```python
# Pseudocódigo para prompt_manager.py
class PromptManager:
    def __init__(self, persistence: IPersistencePort):
        self._persistence = persistence
        self._cache: dict[str, PromptTemplate] = {}
    
    async def get(self, name: str, variables: dict[str, Any] = None) -> str:
        template = await self._get_template(name)
        return template.render(variables or {})
    
    async def update_prompt(self, name: str, new_template: str) -> PromptVersion:
        # Crear nueva versión, no sobrescribir
        return await self._persistence.create_prompt_version(name, new_template)
```

**Criterios de Aceptación (DoD):**
- [ ] Tabla ai_prompts con versionado completo
- [ ] PromptManager con cache y renderizado de templates
- [ ] Mínimo 5 prompts base: opportunity_planning, opportunity_synthesis, strategy_analysis, risk_assessment, market_sentiment
- [ ] Soporte para variables en templates con Jinja2 o similar
- [ ] Versionado: crear nueva versión en cada cambio
- [ ] API para CRUD de prompts desde UI
- [ ] Rollback a versiones anteriores

**Comentarios y Riesgos:**
Templates complejos pueden afectar performance. Considerar pre-compilación.

---

### **Tarea 3.2.2: AI Studio UI**

**Archivo(s):**
- `src/ultibot_ui/views/ai_studio_view.py`
- `src/ultibot_ui/viewmodels/ai_studio_viewmodel.py`
- `src/ultibot_ui/widgets/prompt_editor_widget.py`
- `src/ultibot_ui/widgets/ai_playground_widget.py`

**Clase/Función:** AIStudioView, AIStudioViewModel, PromptEditorWidget, AIPlaygroundWidget

**Descripción Técnica:**
Crear vista dedicada para gestionar prompts y probar IA. Editor de texto rico y playground interactivo.

```python
# Pseudocódigo para ai_studio_view.py
class AIStudioView(QWidget):
    def __init__(self, viewmodel: AIStudioViewModel):
        super().__init__()
        self._vm = viewmodel
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout()
        
        # Panel izquierdo: Lista de prompts
        prompt_list = QListWidget()
        prompt_list.itemClicked.connect(self._vm.load_prompt)
        
        # Panel central: Editor
        editor = PromptEditorWidget()
        editor.text_changed.connect(self._vm.update_prompt_text)
        
        # Panel derecho: Playground
        playground = AIPlaygroundWidget()
        playground.execute_clicked.connect(self._vm.test_prompt)
        
        layout.addWidget(prompt_list, 1)
        layout.addWidget(editor, 2)
        layout.addWidget(playground, 1)
```

**Criterios de Aceptación (DoD):**
- [ ] Vista AIStudio integrada en navegación principal
- [ ] Lista de prompts con búsqueda y filtros
- [ ] Editor de texto con syntax highlighting para templates
- [ ] Playground: inputs para variables, botón ejecutar, output del LLM
- [ ] Versionado visible: ver historial, crear versión, rollback
- [ ] Guardado automático con confirmación
- [ ] Validación de sintaxis de templates
- [ ] Export/import de prompts para backup

**Comentarios y Riesgos:**
UI compleja. Priorizar funcionalidad core: editar, probar, guardar.

---

# FASE 4: EXPANSIÓN Y PULIDO (2 Semanas)
*Bibliotecas completas + Integración + Tests*

## ÉPICA 4.1: Biblioteca Completa de Estrategias

### **Tarea 4.1.1: 7 Estrategias Restantes**

**Archivo(s):**
- `src/ultibot_backend/strategies/supertrend_volatility_filter.py`
- `src/ultibot_backend/strategies/stochastic_rsi_overbought_oversold.py`
- `src/ultibot_backend/strategies/statistical_arbitrage_pairs.py`
- `src/ultibot_backend/strategies/vwap_cross_strategy.py`
- `src/ultibot_backend/strategies/order_book_imbalance_scalper.py`
- `src/ultibot_backend/strategies/news_sentiment_spike_trader.py`
- `src/ultibot_backend/strategies/onchain_metrics_divergence.py`

**Clase/Función:** SuperTrendVolatilityFilter, StochasticRSIOverboughtOversold, etc.

**Descripción Técnica:**
Completar la biblioteca de 10 estrategias diversas según especificación del manifiesto. Enfoque en diversidad de enfoques.

```python
# Pseudocódigo para news_sentiment_spike_trader.py
class NewsSentimentSpikeTrader(BaseStrategy):
    def __init__(self, params: SentimentParameters):
        super().__init__("News_Sentiment_Spike_Trader", params)
        self.sentiment_threshold = params.sentiment_threshold
        self.spike_multiplier = params.spike_multiplier
    
    async def analyze(self, snapshot: MarketSnapshot) -> AnalysisResult:
        # Usar herramienta MCP para obtener sentiment
        mcp_result = await self._tools.execute_tool("get_sentiment", {
            "asset": snapshot.symbol,
            "timeframe": "1h"
        })
        
        sentiment_score = mcp_result.data["sentiment_score"]
        volume_spike = self._detect_volume_spike(snapshot.volume_data)
        
        confidence = self._calculate_confidence(sentiment_score, volume_spike)
        return AnalysisResult(confidence=confidence, metadata={
            "sentiment": sentiment_score,
            "volume_spike": volume_spike
        })
```

**Criterios de Aceptación (DoD):**
- [ ] 10 estrategias total implementadas y funcionales
- [ ] Diversidad de enfoques: momentum, mean reversion, arbitraje, volume, sentiment
- [ ] Estrategias potenciadas por IA integran herramientas MCP
- [ ] Tests unitarios para cada estrategia con escenarios diversos
- [ ] Performance benchmark: todas <200ms por análisis
- [ ] Documentación completa de parámetros y lógica
- [ ] Configuración por defecto sensata para cada estrategia

**Comentarios y Riesgos:**
Foco en calidad vs. velocidad. Mejor pocas estrategias robustas que muchas frágiles.

---

### **Tarea 4.1.2: Biblioteca de Presets de Escaneo**

**Archivo(s):**
- `src/ultibot_backend/core/domain_models/scan_presets.py`
- `src/ultibot_backend/core/services/market_scanner.py`
- `data/scan_presets.json`

**Clase/Función:** ScanPreset, MarketScannerService

**Descripción Técnica:**
Implementar 10 presets de escaneo de mercado para acelerar detección de oportunidades según especificación del manifiesto.

```python
# Pseudocódigo para market_scanner.py
class MarketScannerService:
    def __init__(self, market_provider: IMarketDataProvider):
        self._market = market_provider
        self._presets = self._load_presets()
    
    async def scan_market(self, preset_name: str) -> list[ScanResult]:
        preset = self._presets[preset_name]
        all_symbols = await self._market.get_all_symbols()
        results = []
        
        for symbol in all_symbols:
            ticker = await self._market.get_ticker(symbol)
            if preset.matches(ticker):
                results.append(ScanResult(
                    symbol=symbol,
                    score=preset.calculate_score(ticker),
                    preset=preset_name
                ))
        
        return sorted(results, key=lambda x: x.score, reverse=True)
```

```json
// Pseudocódigo para scan_presets.json
{
  "explosive_volatility": {
    "name": "Explosive Volatility",
    "criteria": {
      "atr_percentile": {"min": 95},
      "volume_24h": {"min": 10000000},
      "price_change_24h": {"min": 5}
    }
  },
  "sleeping_giants": {
    "name": "Sleeping Giants", 
    "criteria": {
      "market_cap": {"min": 1000000000},
      "volatility_percentile": {"max": 10},
      "volume_trend": "increasing"
    }
  }
}
```

**Criterios de Aceptación (DoD):**
- [ ] 10 presets implementados según especificación del manifiesto
- [ ] MarketScannerService ejecuta presets eficientemente
- [ ] Scoring system para ranking de resultados
- [ ] Configuración JSON externa para fácil modificación
- [ ] Cache de resultados para evitar API calls repetitivas
- [ ] Performance: escaneo completo <30 segundos
- [ ] UI integration: selector de presets en dashboard

**Comentarios y Riesgos:**
Performance crítica con muchos símbolos. Implementar paralelización y rate limiting.

---

## ÉPICA 4.2: Integración y Testing End-to-End

### **Tarea 4.2.1: Tests de Integración Completos**

**Archivo(s):**
- `tests/integration/test_complete_trading_flow.py`
- `tests/integration/test_ai_orchestrator_integration.py`
- `tests/integration/test_strategy_engine_integration.py`
- `tests/integration/fixtures/market_data_fixtures.py`

**Clase/Función:** TestCompleteTradingFlow, TestAIOrchestrator, TestStrategyEngine

**Descripción Técnica:**
Crear tests de integración que validen flujos end-to-end sin dependencias externas reales.

```python
# Pseudocódigo para test_complete_trading_flow.py
class TestCompleteTradingFlow:
    @pytest.fixture
    async def trading_system(self):
        # Setup completo del sistema con mocks
        mock_binance = MockBinanceAdapter()
        mock_gemini = MockGeminiAdapter()
        
        container = DIContainer()
        container.register(IMarketDataProvider, mock_binance)
        container.register(GeminiAdapter, mock_gemini)
        
        system = TradingSystem(container)
        await system.initialize()
        return system
    
    async def test_paper_trading_complete_cycle(self, trading_system):
        # 1. Detectar oportunidad
        opportunity = await trading_system.scan_market("explosive_volatility")
        assert len(opportunity) > 0
        
        # 2. Análisis IA
        analysis = await trading_system.analyze_opportunity(opportunity[0])
        assert analysis.confidence > 0.8
        
        # 3. Ejecutar trade simulado
        trade_result = await trading_system.execute_paper_trade(analysis)
        assert trade_result.success
        
        # 4. Verificar eventos publicados
        events = trading_system.get_published_events()
        assert any(isinstance(e, TradeExecutedEvent) for e in events)
```

**Criterios de Aceptación (DoD):**
- [ ] Test completo de paper trading: detección → análisis → ejecución
- [ ] Test completo de real trading con confirmación de usuario
- [ ] Test de AI Orchestrator con múltiples herramientas MCP
- [ ] Test de carga dinámica de estrategias
- [ ] Mocks completos de todas las APIs externas
- [ ] Fixtures realistas de datos de mercado
- [ ] Tests de performance bajo carga
- [ ] Coverage >85% en flujos críticos

**Comentarios y Riesgos:**
Tests complejos pueden ser frágiles. Foco en casos de uso críticos primero.

---

### **Tarea 4.2.2: Script de Despliegue y Configuración**

**Archivo(s):**
- `scripts/deploy_production.py`
- `scripts/setup_database.py`
- `scripts/verify_system.py`
- `docker-compose.production.yml`

**Clase/Función:** DeploymentScript, DatabaseSetup, SystemVerifier

**Descripción Técnica:**
Crear scripts automatizados para despliegue en producción personal del usuario.

```python
# Pseudocódigo para deploy_production.py
class DeploymentScript:
    def __init__(self):
        self.config = self._load_config()
        self.logger = self._setup_logging()
    
    async def deploy(self):
        self.logger.info("Iniciando despliegue de UltiBotInversiones v1.0")
        
        # 1. Verificar prerrequisitos
        await self._verify_prerequisites()
        
        # 2. Setup base de datos
        await self._setup_database()
        
        # 3. Instalar dependencias
        await self._install_dependencies()
        
        # 4. Configurar servicios
        await self._configure_services()
        
        # 5. Migrar datos si existen
        await self._migrate_existing_data()
        
        # 6. Verificar sistema
        await self._verify_deployment()
        
        self.logger.info("Despliegue completado exitosamente")
```

**Criterios de Aceptación (DoD):**
- [ ] Script de despliegue completamente automatizado
- [ ] Verificación de prerrequisitos (Python, Docker, etc.)
- [ ] Setup automático de base de datos Supabase
- [ ] Migración de datos existentes si los hay
- [ ] Configuración de variables de entorno
- [ ] Verificación post-despliegue de todos los servicios
- [ ] Rollback automático en caso de fallo
- [ ] Documentación completa del proceso

**Comentarios y Riesgos:**
Script crítico para adopción. Debe ser robusto y recuperable ante fallos.

---

## ÉPICA 4.3: Pulido Final y Optimización

### **Tarea 4.3.1: Optimización de Performance**

**Archivo(s):**
- `src/ultibot_backend/core/services/performance_monitor.py`
- `scripts/benchmark_system.py`
- `docs/performance_report.md`

**Clase/Función:** PerformanceMonitor, SystemBenchmark

**Descripción Técnica:**
Implementar monitoreo de performance y optimizar puntos críticos para cumplir objetivos <500ms.

```python
# Pseudocódigo para performance_monitor.py
class PerformanceMonitor:
    def __init__(self):
        self._metrics: dict[str, list[float]] = defaultdict(list)
        self._thresholds = {
            "opportunity_detection": 100,  # ms
            "ai_analysis": 300,  # ms
            "trade_execution": 50,  # ms
            "total_cycle": 500  # ms
        }
    
    @contextmanager
    def measure(self, operation: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = (time.perf_counter() - start) * 1000
            self._metrics[operation].append(duration)
            self._check_threshold(operation, duration)
    
    def get_performance_report(self) -> PerformanceReport:
        return PerformanceReport(
            averages={k: statistics.mean(v) for k, v in self._metrics.items()},
            p95={k: statistics.quantiles(v, n=20)[18] for k, v in self._metrics.items()},
            violations=self._get_threshold_violations()
        )
```

**Criterios de Aceptación (DoD):**
- [ ] PerformanceMonitor instrumenta todas las operaciones críticas
- [ ] Benchmark completo del sistema bajo carga
- [ ] Identificación y optimización de bottlenecks
- [ ] Cumplimiento de objetivos: ciclo completo <500ms en P95
- [ ] Memoria: uso estable sin memory leaks
- [ ] CPU: utilización eficiente en operaciones concurrentes
- [ ] Reporte de performance detallado
- [ ] Alertas automáticas en degradación

**Comentarios y Riesgos:**
Optimización prematura es el root of evil. Medir primero, optimizar después.

---

### **Tarea 4.3.2: Documentación Final y Handover**

**Archivo(s):**
- `docs/user_manual.md`
- `docs/developer_guide.md`
- `docs/architecture_implementation.md`
- `docs/troubleshooting.md`

**Clase/Función:** N/A (Documentación)

**Descripción Técnica:**
Crear documentación completa para usuario final y desarrolladores futuros.

**Criterios de Aceptación (DoD):**
- [ ] Manual de usuario: setup inicial, configuración básica, uso diario
- [ ] Guía de desarrollador: arquitectura, patrones, cómo añadir estrategias
- [ ] Documentación de implementación: decisiones técnicas, trade-offs
- [ ] Troubleshooting: problemas comunes y soluciones
- [ ] API reference generada automáticamente
- [ ] Video tutoriales básicos (opcional)
- [ ] README actualizado con quickstart

**Comentarios y Riesgos:**
Documentación crítica para mantenimiento futuro y onboarding.

---

# RESUMEN DE ENTREGABLES

## **Métricas de Éxito por Fase**

### **FASE 1 - Cimientos**
- [ ] Arquitectura hexagonal: 0 imports externos en `/core`
- [ ] CQRS: 5+ comandos, 5+ consultas implementados
- [ ] EventBroker: <10ms publish, <100ms dispatch
- [ ] Tests: >90% coverage en servicios core

### **FASE 2 - Núcleo Funcional**
- [ ] 3 estrategias funcionando: MACD+RSI, Bollinger, Arbitraje
- [ ] UI MVVM: separación completa Vista/ViewModel
- [ ] Temas: cambio dinámico <500ms
- [ ] Performance: análisis estrategia <200ms

### **FASE 3 - Inteligencia**
- [ ] AI Orchestrator: flujo completo planificación→ejecución→síntesis
- [ ] 2+ herramientas MCP funcionando
- [ ] Prompts en BD: 5+ templates, versionado
- [ ] AI Studio: editar, probar, guardar prompts

### **FASE 4 - Expansión**
- [ ] 10 estrategias total + 10 presets escaneo
- [ ] Tests E2E: flujo paper y real trading
- [ ] Deploy script: automatizado y robusto
- [ ] Performance: <500ms ciclo completo P95

## **Criterios de Aceptación Final del Sistema**

### **Funcionales**
- [ ] Paper trading funcional con IA
- [ ] Real trading limitado con confirmación
- [ ] 10 estrategias + 10 presets
- [ ] UI profesional con temas
- [ ] AI Studio operativo

### **No Funcionales**
- [ ] Latencia <500ms P95
- [ ] Win Rate >75% en backtesting
- [ ] Cobertura tests >85%
- [ ] Disponibilidad >99.9%
- [ ] Documentación completa

### **Arquitectónicos**
- [ ] Hexagonal: core puro
- [ ] CQRS: separación clara
- [ ] Eventos: desacoplamiento total
- [ ] MVVM: UI testeable
- [ ] Plug-and-play: estrategias y herramientas

---

**Resultado Final:** Un sistema de trading algorítmico que funciona con la precisión, rendimiento y belleza de un reloj atómico óptico, donde cada componente es un engranaje perfecto en la maquinaria global.
