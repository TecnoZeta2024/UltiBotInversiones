# PLAN DETALLADO DE TAREAS - EVOLUCIÓN ARQUITECTÓNICA
**Proyecto:** UltiBotInversiones  
**Fecha:** 6 de noviembre de 2025  
**Ingeniero:** Cline (Ingeniero Full-Stack Líder)  
**Objetivo:** Transformación hacia plataforma de inversión inteligente

---

## METODOLOGÍA DE EJECUCIÓN

**Principios Arquitectónicos:**
- **Separación Estricta de Capas**: UI solo presentación, Backend toda la lógica
- **Contratos de Datos**: Modelos Pydantic como única fuente de verdad
- **Inyección de Dependencias**: Servicios instanciados en puntos de entrada
- **Modularidad**: Patrones Factory, Adapter, Strategy para extensibilidad

---

# ÉPICA 1: RE-ARQUITECTURA DE LA INTERFAZ DE USUARIO

## Objetivo
Crear una UI limpia, intuitiva y profesional que separe correctamente niveles de información.

## TAREA 1.1: Refactorizar Navegación Principal

### Acción 1.1.1: Modificar SidebarNavigationWidget
**Archivo:** `src/ultibot_ui/widgets/sidebar_navigation_widget.py`
**Pseudocódigo:**
```
ACTUALIZAR nav_items en _create_navigation_buttons():
- nav_items = [("Dashboard", "dashboard"), ("Análisis/Gráficos", "charts"), 
               ("Configuración", "settings"), ("Historial", "history")]
- ELIMINAR botones: "Oportunidades", "Portafolio", "Estrategias"
```

### Acción 1.1.2: Refactorizar MainWindow
**Archivo:** `src/ultibot_ui/windows/main_window.py`
**Pseudocódigo:**
```
EN _setup_central_widget():
- REMOVER inicialización: opportunities_view, strategies_view, portfolio_view
- AGREGAR: charts_view = ChartsView(...)
- ACTUALIZAR view_map = {"dashboard": 0, "charts": 1, "settings": 2, "history": 3}
```

## TAREA 1.2: Rediseñar el Dashboard

### Acción 1.2.1: Eliminar ChartWidget del Dashboard
**Archivo:** `src/ultibot_ui/windows/dashboard_view.py`
**Pseudocódigo:**
```
- REMOVER import ChartWidget
- ELIMINAR instanciación chart_widget del layout
- LIBERAR espacio para widgets de estado
```

### Acción 1.2.2: Implementar Layout Adaptativo
**Pseudocódigo:**
```
REEMPLAZAR layout actual con QGridLayout:
- grid_layout = QGridLayout()
- setSpacing(16), setContentsMargins(20, 20, 20, 20)
- DISTRIBUIR widgets en grid 2x2 para responsive design
```

### Acción 1.2.3: Crear Widgets de Estado del Sistema
**Archivos a Crear:**
1. `src/ultibot_ui/widgets/market_status_widget.py`
2. `src/ultibot_ui/widgets/ai_status_widget.py`
3. `src/ultibot_ui/widgets/orchestrator_status_widget.py`

**Pseudocódigo para MarketStatusWidget:**
```
CLASS MarketStatusWidget(QWidget):
    MÉTODOS:
    - __init__(): crear layout con indicadores visuales
    - update_status(api_name, is_connected, timestamp): actualizar estado
    - _create_status_indicator(): círculo verde/rojo por API
    COMPONENTES:
    - QLabel para cada API (Binance, Mobula)
    - QLabel para timestamp última conexión
```

**Pseudocódigo para AIStatusWidget:**
```
CLASS AIStatusWidget(QWidget):
    MÉTODOS:
    - update_ai_status(mode, last_action, timestamp)
    - _set_mode_indicator(): cambiar color según estado
    COMPONENTES:
    - Indicador estado motor Gemini
    - Label modo actual ("Buscando", "Analizando", "En Espera")
    - Label última acción significativa
```

**Pseudocódigo para OrchestratorStatusWidget:**
```
CLASS OrchestratorStatusWidget(QWidget):
    MÉTODOS:
    - update_orchestrator_stats(opportunities, winrate)
    COMPONENTES:
    - Contador oportunidades detectadas en sesión
    - Winrate de sesión actual
    - Estado motor de oportunidades
```

### Acción 1.2.4: Refactorizar PortfolioWidget
**Archivo:** `src/ultibot_ui/widgets/portfolio_widget.py`
**Pseudocódigo:**
```
REFACTORIZAR diseño:
- ENVOLVER en QGroupBox("Resumen de Portafolio")
- CREAR layouts internos: QHBoxLayout para etiqueta-valor
- ESTILO: font-weight bold para valores, colores por P&L
- PADDING: 8px interno, 4px entre elementos
```

## TAREA 1.3: Crear Vista de Análisis

### Acción 1.3.1: Crear ChartsView
**Archivo a Crear:** `src/ultibot_ui/windows/charts_view.py`
**Pseudocódigo:**
```
CLASS ChartsView(QWidget):
    MÉTODOS:
    - __init__(user_id, main_window, api_client, loop)
    - _setup_ui(): crear layout con header y chart_widget
    - enter_view(): refrescar datos al activar vista
    - leave_view(), cleanup(): gestión de recursos
    COMPONENTES:
    - Header "Análisis de Mercado"
    - ChartWidget movido desde dashboard
```

### Acción 1.3.2: Integrar ChartsView en MainWindow
**Pseudocódigo:**
```
EN main_window.py:
- IMPORTAR ChartsView
- EN _setup_central_widget(): 
  self.charts_view = ChartsView(...)
  self.stacked_widget.addWidget(self.charts_view)
```

## TAREA 1.4: Implementar Presets de Configuración

### Acción 1.4.1: Agregar PresetManagementWidget a SettingsView
**Archivo:** `src/ultibot_ui/windows/settings_view.py`
**Pseudocódigo:**
```
AGREGAR sección presets:
- QGroupBox("Gestión de Presets de Configuración")
- QComboBox para listar presets
- QPushButton("Guardar Preset Actual", "Eliminar Preset")
- CONECTAR señales: currentTextChanged -> load_preset
```

### Acción 1.4.2: Extender Backend para Presets
**Archivo:** `src/ultibot_backend/services/config_service.py`
**Pseudocódigo:**
```
AGREGAR métodos:
- save_configuration_preset(user_id, preset_name, config_data) -> bool
- load_configuration_preset(user_id, preset_name) -> dict
- get_all_presets(user_id) -> List[str]
- delete_preset(user_id, preset_name) -> bool
```

### Acción 1.4.3: Crear Tabla de Presets
**Archivo:** `supabase/migrations/create_configuration_presets.sql`
**Pseudocódigo:**
```
CREATE TABLE configuration_presets:
- id UUID PRIMARY KEY
- user_id UUID NOT NULL
- preset_name VARCHAR(100) NOT NULL
- configuration_data JSONB NOT NULL
- created_at, updated_at TIMESTAMP
- UNIQUE(user_id, preset_name)
```

### Acción 1.4.4: Crear Endpoints de API
**Archivo:** `src/ultibot_backend/api/v1/endpoints/config.py`
**Pseudocódigo:**
```
AGREGAR endpoints:
- POST /presets/{preset_name}: guardar preset
- GET /presets/{preset_name}: cargar preset
- GET /presets: listar todos los presets
- DELETE /presets/{preset_name}: eliminar preset
```

---

# ÉPICA 2: MOTOR DE ESTRATEGIAS "PLUGGABLE"

## Objetivo
Permitir que las estrategias de trading sean módulos independientes y extensibles.

## TAREA 2.1: Definir Interfaz de Estrategia

### Acción 2.1.1: Crear BaseStrategy
**Archivo a Crear:** `src/ultibot_backend/strategies/base_strategy.py`
**Pseudocódigo:**
```
DEFINIR enums y dataclasses:
- TradingSignal(Enum): COMPRAR, VENDER, ESPERAR
- StrategyResult(dataclass): signal, confidence, reasoning, amounts

ABSTRACT CLASS BaseStrategy:
    MÉTODOS ABSTRACTOS:
    - evaluate(market_data) -> StrategyResult
    - name() -> str
    - required_data_points() -> List[str]
    - get_parameters_schema() -> Dict[str, Any]
    
    MÉTODOS CONCRETOS:
    - update_parameters(new_parameters)
    - get_current_parameters()
```

### Acción 2.1.2: Crear Directorio de Estrategias
**Directorio a Crear:** `src/ultibot_backend/strategies/`
**Archivos Iniciales:**
- `__init__.py` (vacío)
- `base_strategy.py`
- `README.md` (documentación)

## TAREA 2.2: Implementar Estrategias Concretas

### Acción 2.2.1: Crear MomentumStrategy
**Archivo a Crear:** `src/ultibot_backend/strategies/momentum_strategy.py`
**Pseudocódigo:**
```
CLASS MomentumStrategy(BaseStrategy):
    PARÁMETROS:
    - momentum_period: 24h
    - volume_multiplier: 1.5
    - rsi_oversold: 30, rsi_overbought: 70
    - min_price_change: 0.03
    
    MÉTODO evaluate():
    - OBTENER: current_price, price_change_24h, volume_24h, rsi
    - CALCULAR momentum_score basado en precio y volumen
    - AJUSTAR por RSI (penalizar sobrecompra/sobreventa)
    - RETORNAR StrategyResult con señal y confianza
    
    MÉTODO _calculate_momentum_score():
    - price_score = price_change / 100
    - volume_score = min((volume_ratio - 1) * 0.3, 0.3)
    - rsi_adjustment basado en condiciones
```

### Acción 2.2.2: Crear MeanReversionStrategy
**Archivo a Crear:** `src/ultibot_backend/strategies/mean_reversion_strategy.py`
**Pseudocódigo:**
```
CLASS MeanReversionStrategy(BaseStrategy):
    LÓGICA:
    - DETECTAR desviaciones del precio de media móvil
    - IDENTIFICAR puntos de entrada cuando precio alejado de media
    - USAR Bollinger Bands para confirmación
```

### Acción 2.2.3: Crear VolatilityBreakoutStrategy
**Archivo a Crear:** `src/ultibot_backend/strategies/volatility_breakout_strategy.py`
**Pseudocódigo:**
```
CLASS VolatilityBreakoutStrategy(BaseStrategy):
    ESPECIALIDAD: "mercados explosivos"
    LÓGICA:
    - DETECTAR rupturas de volatilidad
    - USAR ATR (Average True Range) para medir volatilidad
    - IDENTIFICAR breakouts con volumen confirmatorio
```

## TAREA 2.3: Construir Factory de Estrategias

### Acción 2.3.1: Refactorizar StrategyService
**Archivo:** `src/ultibot_backend/services/strategy_service.py`
**Pseudocódigo:**
```
CLASS StrategyService (Factory pattern):
    ATRIBUTOS:
    - _strategies: Dict[str, Type[BaseStrategy]]
    - _strategy_instances: Dict[str, BaseStrategy]
    
    MÉTODO _load_strategies():
    - ESCANEAR directorio strategies/
    - IMPORTAR dinámicamente módulos .py
    - REGISTRAR clases que hereden de BaseStrategy
    
    MÉTODOS PÚBLICOS:
    - get_available_strategies() -> List[str]
    - get_strategy(strategy_name, parameters) -> BaseStrategy
    - get_strategy_schema(strategy_name) -> Dict
    - reload_strategies()
```

### Acción 2.3.2: Crear Endpoints para Estrategias
**Archivo:** `src/ultibot_backend/api/v1/endpoints/strategies.py`
**Pseudocódigo:**
```
ENDPOINTS:
- GET /available: listar estrategias disponibles
- GET /{strategy_name}/schema: obtener esquema de parámetros
- POST /{strategy_name}/evaluate: evaluar estrategia con datos
```

---

# ÉPICA 3: MÓDULO DE ORQUESTACIÓN DE HERRAMIENTAS MCP

## Objetivo
Implementar un sistema robusto para que el Agente IA utilice herramientas MCP externas.

## TAREA 3.1: Crear Adaptador MCP

### Acción 3.1.1: Crear MCPAdapter
**Archivo a Crear:** `src/ultibot_backend/adapters/mcp_adapter.py`
**Pseudocódigo:**
```
DATACLASS MCPResult:
- success: bool, data: Any, error: str, execution_time: float

CLASS MCPAdapter:
    MÉTODOS:
    - __aenter__, __aexit__: context manager para httpx session
    - execute_tool(server_url, tool_name, params) -> MCPResult
    - test_connection(server_url) -> bool
    
    PROTOCOLO MCP:
    - CONSTRUIR payload JSON-RPC 2.0
    - HEADERS: Content-Type application/json
    - MANEJAR errores HTTP y timeouts
    - EXTRAER resultado de response.json()["result"]
```

## TAREA 3.2: Crear Registro de Herramientas

### Acción 3.2.1: Crear ToolRegistryService
**Archivo a Crear:** `src/ultibot_backend/services/tool_registry_service.py`
**Pseudocódigo:**
```
DATACLASS MCPTool:
- name, description, mcp_server_url, parameters_schema

CLASS ToolRegistryService:
    MÉTODOS:
    - _load_tools_from_config(): cargar desde tools.yaml
    - get_available_tools() -> List[MCPTool]
    - get_tool_by_name(name) -> MCPTool
    - register_tool(tool_info), unregister_tool(name)
    - test_all_connections() -> Dict[str, bool]
```

### Acción 3.2.2: Crear Archivo de Configuración
**Archivo a Crear:** `config/tools.yaml`
**Pseudocódigo:**
```
ESTRUCTURA YAML:
tools:
  - name: "get_crypto_price_history_ccxt"
    description: "Obtiene historial de precios OHLCV usando CCXT"
    mcp_server_url: "http://localhost:8001"
    parameters:
      symbol: {type: string, required: true}
      timeframe: {type: string, default: "1h"}
```

## TAREA 3.3: Actualizar Orquestador de IA

### Acción 3.3.1: Refactorizar ai_orchestrator_service.py
**Pseudocódigo:**
```
IMPLEMENTAR ciclo "Planificación -> Ejecución -> Síntesis":

FASE PLANIFICACIÓN:
- OBTENER herramientas de ToolRegistryService
- CONSTRUIR prompt con lista de herramientas disponibles
- PEDIR a Gemini: usar herramienta O responder directamente
- ESPERAR respuesta JSON o texto

FASE EJECUCIÓN:
- SI respuesta es JSON herramienta:
  * EXTRAER tool_name y parameters
  * USAR MCPAdapter.execute_tool()
  * OBTENER resultado de herramienta
- SI respuesta es texto: es respuesta final

FASE SÍNTESIS:
- SI se usó herramienta:
  * CONSTRUIR segundo prompt con pregunta original + datos herramienta
  * PEDIR a Gemini respuesta final usando esos datos
- RETORNAR respuesta final
```

### Acción 3.3.2: Crear Endpoints MCP
**Archivo:** `src/ultibot_backend/api/v1/endpoints/mcp_tools.py`
**Pseudocódigo:**
```
ENDPOINTS:
- GET /tools: listar herramientas disponibles
- POST /tools/{tool_name}/execute: ejecutar herramienta específica
- GET /tools/health: verificar conexiones de servidores MCP
```

---

# ÉPICA 4: CONTROL DE PROMPTS Y "AI PROMPT STUDIO"

## Objetivo
Dar al usuario control total sobre las instrucciones que guían al Agente IA.

## TAREA 4.1: Backend para Gestión de Prompts

### Acción 4.1.1: Crear Tabla AI Prompt Templates
**Archivo:** `supabase/migrations/create_ai_prompt_templates.sql`
**Pseudocódigo:**
```
CREATE TABLE ai_prompt_templates:
- id UUID PRIMARY KEY
- user_id UUID NOT NULL
- template_name VARCHAR(100) (ej: "system_prompt_default")
- template_content TEXT NOT NULL
- version INTEGER DEFAULT 1
- is_active BOOLEAN DEFAULT false
- created_at, updated_at TIMESTAMP
```

### Acción 4.1.2: Extender ConfigService
**Archivo:** `src/ultibot_backend/services/config_service.py`
**Pseudocódigo:**
```
AGREGAR métodos para prompts:
- save_prompt_template(user_id, name, content) -> PromptTemplate
- get_prompt_template(user_id, name) -> PromptTemplate
- list_prompt_templates(user_id) -> List[PromptTemplate]
- delete_prompt_template(user_id, name) -> bool
- set_active_template(user_id, name) -> bool
```

### Acción 4.1.3: Refactorizar ai_orchestrator_service.py
**Pseudocódigo:**
```
MODIFICAR para usar prompts dinámicos:
- EN __init__(): inyectar ConfigService
- MÉTODO get_active_prompt_template(template_type) -> str
- REEMPLAZAR prompts hardcodeados con:
  * template = config_service.get_prompt_template(user_id, "analysis_prompt")
  * final_prompt = template.content.format(symbol=symbol, data=market_data)
```

## TAREA 4.2: Frontend para "Prompt Studio"

### Acción 4.2.1: Agregar Sección "Ajuste de Agente IA" en SettingsView
**Archivo:** `src/ultibot_ui/windows/settings_view.py`
**Pseudocódigo:**
```
AGREGAR nueva sección:
- QGroupBox("AI Prompt Studio")
- QComboBox para seleccionar plantilla
- QTextEdit grande para editar contenido
- QPushButton("Guardar Cambios", "Restaurar Default")
- QPushButton("Test Panel")
```

### Acción 4.2.2: Crear Panel de Pruebas
**Pseudocódigo:**
```
COMPONENTES Panel de Pruebas:
- QLineEdit para ingresar símbolo (ej: "BTCUSDT")
- QPushButton("Generar Prompt de Prueba")
- QTextEdit READ-ONLY: mostrar prompt final con datos reales
- QPushButton("Ejecutar Prueba")
- QTextEdit READ-ONLY: mostrar respuesta IA en bruto

FLUJO:
1. Usuario ingresa símbolo
2. Sistema obtiene datos reales de mercado
3. Aplica template.format() con datos
4. Muestra prompt exacto que se enviaría
5. Usuario puede ejecutar y ver respuesta
```

### Acción 4.2.3: Implementar CRUD de Templates
**Pseudocódigo:**
```
MÉTODOS en SettingsView:
- load_template_list(): poblar QComboBox
- on_template_selected(): cargar contenido en QTextEdit
- save_current_template(): guardar cambios
- restore_default_template(): resetear a versión original
- test_template_with_real_data(): panel de pruebas
```

## TAREA 4.3: Crear Endpoints API para Prompts

### Acción 4.3.1: Crear Endpoints
**Archivo:** `src/ultibot_backend/api/v1/endpoints/ai_prompts.py`
**Pseudocódigo:**
```
ENDPOINTS:
- GET /prompts: listar todas las plantillas del usuario
- POST /prompts: crear nueva plantilla
- GET /prompts/{template_name}: obtener plantilla específica
- PUT /prompts/{template_name}: actualizar plantilla
- DELETE /prompts/{template_name}: eliminar plantilla
- POST /prompts/{template_name}/test: probar plantilla con datos reales
```

---

# MÉTRICAS DE ÉXITO Y VERIFICACIÓN

## Criterios de Aceptación por Épica

### ÉPICA 1 - UI Re-arquitectura
- ✅ Dashboard muestra solo información de estado (no gráficos)
- ✅ Vista Charts dedicada con análisis completo
- ✅ Navegación principal con 4 botones únicamente
- ✅ Sistema de presets funcional con CRUD completo
- ✅ Widgets de estado actualizan en tiempo real

### ÉPICA 2 - Motor Estrategias
- ✅ Mínimo 3 estrategias concretas implementadas
- ✅ Agregar nueva estrategia toma < 30 minutos
- ✅ Factory carga estrategias dinámicamente
- ✅ Cada estrategia configurable independientemente
- ✅ Esquemas de parámetros auto-documentados

### ÉPICA 3 - Orquestación MCP
- ✅ MCPAdapter conecta con cualquier servidor MCP
- ✅ Registry carga herramientas desde configuración
- ✅ Ciclo Planificación->Ejecución->Síntesis funcional
- ✅ Manejo robusto de errores y timeouts
- ✅ Tests de conectividad automáticos

### ÉPICA 4 - Prompt Studio
- ✅ 100% de prompts externalizados de código
- ✅ CRUD completo para plantillas de prompts
- ✅ Panel de pruebas con datos reales funcional
- ✅ Configurar prompt personalizado < 5 minutos
- ✅ Sistema de versioning de plantillas

## Timeline Estimado

**ÉPICA 1:** 12-15 horas de desarrollo
**ÉPICA 2:** 10-12 horas de desarrollo  
**ÉPICA 3:** 15-18 horas de desarrollo
**ÉPICA 4:** 8-10 horas de desarrollo

**TOTAL ESTIMADO:** 45-55 horas

## Consideraciones de Implementación

### Orden de Priorización Recomendado
1. **ÉPICA 1** - Base para experiencia de usuario mejorada
2. **ÉPICA 2** - Core extensible de funcionalidad trading
3. **ÉPICA 3** - Potenciación máxima de capacidades IA
4. **ÉPICA 4** - Control total y personalización avanzada

### Puntos de Control
- Checkpoint cada épica para validación funcional
- Tests de regresión antes de épica siguiente
- Backup de configuración antes de cambios mayores
- Documentación actualizada por cada épica completada

### Estrategia de Rollback
- Git branches separados por épica
- Migraciones de DB reversibles
- Configuraciones de ejemplo para testing
- Plan de recuperación ante fallos críticos

---

**Estado del Plan:** LISTO PARA EJECUCIÓN  
**Próximo Paso:** Iniciar ÉPICA 1 - Acción 1.1.1
