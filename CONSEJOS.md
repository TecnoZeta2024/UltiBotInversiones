De acuerdo. He analizado la estructura y el código del repositorio `ultibotinversiones`, enfocándome en el directorio `src/ultibot_ui`. A continuación, presento un plan de acción detallado para reestructurar y embellecer la interfaz de usuario, resolviendo los problemas funcionales y de diseño que has señalado.

Este plan está diseñado para ser entregado a tu desarrollador frontend, con justificaciones técnicas basadas en principios de ingeniería de software para garantizar una implementación robusta, mantenible y de alta calidad.

----------

## **Plan de Refactorización y Mejora de la Interfaz de Usuario (UI)**

La propuesta se centra en transformar la UI actual en una aplicación de escritorio moderna, intuitiva y funcional, siguiendo una arquitectura limpia y componentes desacoplados.

### **1. Reestructuración de la Navegación Principal y Vistas**

**Diagnóstico:** La configuración está ubicada de forma poco intuitiva y los gráficos sobrecargan el dashboard principal. La navegación principal debe ser el pilar de la experiencia de usuario, ofreciendo acceso claro y directo a las secciones clave.

**Plan de Acción:**

1.  **Mover "Configuración" al Sidebar:** La configuración es una sección primaria, no secundaria. Su lugar natural es el menú de navegación principal.
    
    -   **Archivo a modificar:** `src/ultibot_ui/widgets/sidebar_navigation_widget.py`.
    -   **Acción:** Añadir un nuevo botón/opción en el sidebar llamado "**Configuración**". Esto centraliza el acceso y mejora la predictibilidad de la interfaz.
    -   **Archivo a modificar:** `src/ultibot_ui/windows/main_window.py`.
    -   **Acción:** Reconfigurar el `QStackedWidget` para que el `SettingsView` sea una de las vistas principales gestionadas por el sidebar, en lugar de un diálogo o widget secundario.
2.  **Crear una Sección Dedicada para "Análisis y Gráficos"**: El análisis de datos es una tarea compleja que merece su propio espacio para no trivializar el dashboard.
    
    -   **Acción:** Crear un nuevo archivo de vista: `src/ultibot_ui/windows/charts_view.py`.
    -   **Contenido:** Esta vista contendrá el `ChartWidget` y cualquier otro widget futuro relacionado con el análisis de datos históricos o de mercado.
    -   **Archivo a modificar:** `src/ultibot_ui/widgets/sidebar_navigation_widget.py`.
    -   **Acción:** Añadir una nueva opción llamada "**Análisis**" o "**Gráficos**" en el sidebar.
    -   **Archivo a modificar:** `src/ultibot_ui/windows/main_window.py`.
    -   **Acción:** Integrar la nueva `ChartsView` en el `QStackedWidget`, conectándola a la opción correspondiente del sidebar.

### **2. Rediseño del Dashboard**

**Diagnóstico:** El dashboard actual mezcla incorrectamente datos operativos de alto nivel con análisis detallados (gráficos) y las tarjetas de información carecen de una estructura visual clara y adaptativa.

**Plan de Acción:**

1.  **Definir la Jerarquía de Información del Dashboard:** El dashboard debe ofrecer una vista de "estado del sistema" de un solo vistazo.
    
    -   **Archivo a refactorizar:** `src/ultibot_ui/windows/dashboard_view.py`.
    -   **Acción:** Eliminar por completo el `ChartWidget` de esta vista. Utilizar un `QGridLayout` como layout principal para posicionar las nuevas tarjetas de estado de forma ordenada y adaptativa.
2.  **Crear Widgets de Estado del Sistema:** Reemplazar el espacio liberado con widgets que muestren información operativa crítica. Estos deben ser componentes auto-contenidos que obtienen datos del `api_client`.
    
    -   **Nuevo Widget 1: `MarketStatusWidget`**:
        -   **Propósito:** Mostrar el estado de la conexión con las APIs de mercado (Binance, Mobula).
        -   **UI:** Debe incluir un indicador de estado (ej. un círculo verde/rojo), el nombre del servicio ("Binance API") y un timestamp de la última conexión exitosa.
    -   **Nuevo Widget 2: `AIOrchestratorWidget`**:
        -   **Propósito:** Informar sobre el estado del motor de IA.
        -   **UI:** Indicador de estado, modo actual ("Buscando Oportunidades", "En Espera"), y un resumen de la última acción significativa (ej. "Última oportunidad evaluada: BTC/USDT a las 10:45:12").
    -   **Nuevo Widget 3: `PortfolioSummaryWidget` (`portfolio_widget.py` refactorizado):**
        -   **Propósito:** Corregir el diseño de la tarjeta de portafolio.
        -   **UI:** Usar un `QGroupBox` con un título claro ("Resumen de Portafolio"). Estructurar los datos con layouts internos (`QHBoxLayout`, `QVBoxLayout`) para alinear correctamente etiquetas y valores (ej. "Valor Total:", "$ 1,234.56"). Asegurar padding y márgenes consistentes.

### **3. Implementación de la Ventana Adaptativa (Responsive)**

**Diagnóstico:** La ventana tiene un tamaño fijo, lo cual es inaceptable para una aplicación moderna. La UI debe ser fluida y legible en diferentes tamaños de pantalla.

**Plan de Acción:**

1.  **Uso Exclusivo de Layouts Dinámicos:** Prohibir el uso de geometrías fijas (`.setGeometry()`, `.resize()`) para el posicionamiento de widgets principales.
    
    -   **Archivos a revisar:** Todos los archivos en `src/ultibot_ui/windows` y `src/ultibot_ui/widgets`.
    -   **Acción:** Asegurarse de que cada `QWidget` o `QDialog` tenga un layout principal (`QGridLayout`, `QVBoxLayout`, etc.) seteado.
2.  **Implementar `QSplitter` para Vistas Complejas:** Para la `MainWindow` y la futura `ChartsView`, usar `QSplitter` permite al usuario redimensionar áreas de la interfaz según su necesidad, una característica clave en aplicaciones de alta densidad de datos.
    
    -   **Archivo a modificar:** `src/ultibot_ui/windows/main_window.py`.
    -   **Acción:** Implementar un `QSplitter` que divida el sidebar del `QStackedWidget` (el área de contenido principal). Esto hace que el ancho del sidebar sea ajustable por el usuario.

### **4. Gestión de Configuraciones Avanzadas (Presets)**

**Diagnóstico:** La configuración manual de estrategias es repetitiva y propensa a errores. Se necesita un sistema para guardar y cargar configuraciones recurrentes.

**Plan de Acción:**

1.  **Crear un `PresetManagementWidget`:**
    
    -   **Propósito:** Este widget gestionará la lógica de guardar, cargar y eliminar presets de configuración.
    -   **Ubicación:** Debe ser añadido a la vista `SettingsView` (`src/ultibot_ui/windows/settings_view.py`).
    -   **UI:**
        -   Un `QComboBox` para listar los presets guardados.
        -   Un `QPushButton` ("Guardar Preset Actual") que abrirá un diálogo para nombrar y guardar la configuración actual.
        -   Un `QPushButton` ("Eliminar") para borrar el preset seleccionado.
        -   La selección de un preset en el `QComboBox` debe cargar automáticamente la configuración en la UI.
2.  **Extender el Backend para Soportar Presets:** La UI solo se encarga de la presentación; la lógica de negocio debe residir en el backend.
    
    -   **Archivo a modificar:** `src/ultibot_backend/services/config_service.py`.
    -   **Acción:** Añadir nuevos métodos: `save_configuration_preset(user_id, preset_name, config_data)`, `load_configuration_preset(user_id, preset_name)`, `get_all_presets(user_id)` y `delete_preset(user_id, preset_name)`.
    -   **Archivo a modificar:** `src/ultibot_backend/adapters/persistence_service.py`.
    -   **Acción:** Implementar la lógica de base de datos (Supabase) para almacenar estos presets. Se sugiere una nueva tabla `configuration_presets` con columnas como `id`, `user_id`, `preset_name`, y `configuration_data` (JSONB).
    -   **API Endpoints:** Exponer esta funcionalidad a través de nuevos endpoints en `src/ultibot_backend/api/v1/endpoints/config.py`.

----------

Este plan integral no solo soluciona los problemas estéticos y funcionales reportados, sino que eleva la arquitectura del frontend a un estándar profesional, garantizando que el producto final sea tan preciso y fiable como un **reloj atómico óptico**.

## ** Plan de mejoras y optimizaciones, enfocado en convertir tu herramienta en una plataforma de trading verdaderamente inteligente y adaptable. **

----------

### **1. Evolución del Módulo de Estrategias: Hacia una Arquitectura de "Plugins"**

**Diagnóstico:** El concepto de "estrategia" está implícito y probablemente disperso o rígidamente codificado. Para manejar 6 o más estrategias, necesitas un sistema donde cada estrategia sea un componente independiente y "enchufable" (pluggable).

**Plan de Acción (Backend):**

1.  **Definir una Interfaz de Estrategia Común:**
    
    -   **Acción:** Crear una clase base abstracta en un nuevo archivo, por ejemplo `src/ultibot_backend/strategies/base_strategy.py`.
    -   **Contenido:** Esta clase `BaseStrategy` definirá la firma que _todas_ las estrategias deben cumplir. Métodos mandatorios:
        -   `evaluate(self, market_data: dict) -> TradingSignal`: Analiza los datos de mercado y devuelve una señal (COMPRAR, VENDER, ESPERAR).
        -   `name(self) -> str`: Devuelve el nombre de la estrategia.
        -   `required_data_points(self) -> list`: Especifica qué datos necesita la estrategia (ej. `['precio', 'volumen', 'RSI_14']`).
    -   **Justificación:** Esto impone un contrato estricto. El motor principal no necesita saber _cómo_ funciona una estrategia, solo que puede llamar a `.evaluate()` y obtener una señal. Esto es el **Principio de Inversión de Dependencias**.
2.  **Implementar Estrategias como Plugins Concretos:**
    
    -   **Acción:** Crear un nuevo directorio `src/ultibot_backend/strategies/`. Dentro, cada estrategia será su propio archivo Python, implementando la clase `BaseStrategy`.
    -   **Ejemplos:**
        -   `momentum_strategy.py` (Clase `MomentumStrategy`)
        -   `mean_reversion_strategy.py` (Clase `MeanReversionStrategy`)
        -   **`volatility_breakout_strategy.py` (Clase `VolatilityBreakoutStrategy`) -> Esta es clave para tu necesidad de "mercados explosivos".**
3.  **Crear un `StrategyFactory`:**
    
    -   **Acción:** Modificar `src/ultibot_backend/services/strategy_service.py` para que actúe como una fábrica (Factory).
    -   **Funcionalidad:** Tendrá un método `load_strategies()` que escanea el directorio `strategies/`, importa las clases, y las registra en un diccionario. El método `get_strategy(name)` devolverá una instancia de la estrategia solicitada.
    -   **Justificación:** Desacopla completamente el motor de trading de las implementaciones de estrategia. Para añadir una nueva estrategia, solo necesitas crear un nuevo archivo en el directorio correcto, sin modificar el núcleo del servicio.

----------

### **2. Creación de un "Prompt Studio": Control Total sobre tu Agente IA**

**Diagnóstico:** El Agente IA es una caja negra. Sus prompts están hardcodeados, impidiendo cualquier ajuste fino, experimentación o adaptación a diferentes contextos de mercado.

**Plan de Acción (Full-Stack):**

1.  **Backend: Externalizar y Centralizar los Prompts:**
    
    -   **Acción:** La configuración de la IA no debe estar en el código. Debe residir en la base de datos.
    -   **Modelo de Datos:** Crear una nueva tabla en Supabase: `ai_prompt_templates`.
        -   **Columnas:** `id`, `user_id`, `template_name` (ej. "system_prompt_default", "market_analysis_explosive"), `template_content` (TEXT), `version`.
    -   **Servicio:** Extender `config_service.py` para que pueda leer y escribir estas plantillas de prompts.
    -   **Refactorizar `ai_orchestrator_service.py`:** Este servicio ya no tendrá prompts hardcodeados. En su lugar, solicitará la plantilla de prompt activa al `ConfigService` y la formateará con los datos de mercado en tiempo real antes de enviarla al modelo de lenguaje. `template_content.format(symbol=symbol, data=market_data_summary)`.
2.  **Frontend: La Interfaz de Control del "Cerebro":**
    
    -   **Acción:** Crear una nueva pestaña o sección en la vista de **Configuración** llamada "**Ajuste de Agente IA**" o "**Prompt Studio**".
    -   **Componentes de la UI:**
        -   Un `QComboBox` para seleccionar qué plantilla de prompt editar (ej. "Análisis de Volatilidad", "Análisis General", "System Prompt").
        -   Un `QTextEdit` grande y central donde se muestra y edita el contenido de la plantilla de prompt seleccionada.
        -   Botones: "Guardar Cambios", "Restaurar a Versión por Defecto".
        -   **Panel de Pruebas (CRÍTICO):** Un área en esta misma vista donde puedes:
            1.  Ingresar un símbolo de mercado (ej. "BTCUSDT").
            2.  Hacer clic en un botón "Generar Prompt de Prueba".
            3.  El sistema muestra el **prompt exacto y final** que se enviaría a la IA, con los datos reales ya inyectados.
            4.  Un botón "Ejecutar Prueba" que envía este prompt y muestra la respuesta **en bruto** de la IA.
    -   **Justificación:** Esto transforma la IA de una herramienta estática a una dinámica. Permite la **ingeniería de prompts iterativa**, que es el núcleo del trabajo con modelos de lenguaje. Te da la visibilidad y el control que sientes que te faltan.

----------

### **3. Implementación del "Market Scanner" para Mercados Explosivos**

**Diagnóstico:** No puedes encontrar mercados explosivos porque no los estás buscando activamente. Necesitas un sistema proactivo que vigile el mercado por ti.

**Plan de Acción (Backend + UI):**

1.  **Servicio de Escaneo (`MarketScannerService`):**
    
    -   **Acción:** Crear un nuevo servicio en el backend que funcione en segundo plano.
    -   **Lógica:**
        1.  Cada X minutos (configurable), obtiene una lista amplia de activos (ej. todos los pares `USDT` de Binance).
        2.  Aplica un **filtro rápido y barato**: Usa una de tus nuevas estrategias "plug-and-play" (ej. `VolatilityBreakoutStrategy`) o un indicador simple (ej. ¿El volumen de las últimas 24h es > 500% del promedio de 7 días?) para pre-seleccionar un puñado de candidatos interesantes.
        3.  Para los pocos candidatos que pasan el filtro, y solo para esos, invoca al `AIOrchestratorService`.
        4.  El orquestador usará una plantilla de prompt específica (`market_analysis_explosive`) para pedir a la IA una evaluación cualitativa sobre si el candidato es una oportunidad genuina.
        5.  Guarda los resultados (candidatos y análisis de la IA) en una nueva tabla en la base de datos: `market_opportunities`.
2.  **UI: El Panel de Oportunidades:**
    
    -   **Acción:** Añadir un nuevo widget principal al Dashboard (o incluso una nueva vista principal en el sidebar) llamado "**Escáner de Oportunidades**".
    -   **UI:**
        -   Una tabla que se actualiza en tiempo real mostrando los símbolos marcados por el `MarketScannerService`.
        -   **Columnas:** Símbolo, Precio Actual, Variación 24h, **Estado** ("Analizando por IA", "Oportunidad Detectada"), **Resumen IA** (una frase corta del análisis de la IA).
        -   Al hacer clic en una fila, se abre un panel de detalles con el análisis completo de la IA y botones de acción rápida ("Ejecutar Orden", "Vigilar").

**Justificación:** Este sistema crea un **embudo de descubrimiento**. En lugar de analizar todo, realiza un filtrado computacionalmente barato primero y luego aplica el costoso y potente análisis de la IA solo donde importa. Es la forma más eficiente de encontrar agujas en un pajar.

## **Usar un protocolo como MCP (Model-Context-Protocol) **

Tu idea no es un caso perdido. Al contrario, es **arquitectónicamente correcta y avanzada**. El objetivo de usar un protocolo como MCP (Model-Context-Protocol) para que un Agente IA interactúe con herramientas de datos es precisamente la dirección en la que se mueve la ingeniería de sistemas de IA complejos. Alivia la carga del modelo de lenguaje, reduce costos de API y encapsula la lógica de acceso a datos.

El fracaso de tu agente de codificación no se debe a una limitación del stack tecnológico (Python/FastAPI/Qt es perfectamente capaz), sino a un error de enfoque. Probablemente buscó una "conexión directa" o una librería que hiciera todo el trabajo. La solución no es un conector, es un **patrón de orquestación**.

Aquí está la solución técnica para implementar tu visión. Esto no es solo una solución; es el diseño estándar de la industria para agentes autónomos que utilizan herramientas.

----------

### **Solución: Arquitectura de Agente IA con Orquestación de Herramientas MCP**

El principio clave es: **El Agente IA no "llama" directamente a las herramientas**. El `AIOrchestratorService` actúa como el cerebro que interpreta la intención del Agente IA, ejecuta la herramienta apropiada en su nombre y le devuelve los resultados para que elabore una respuesta final.

Este es el plan de implementación:

#### **Paso 1: Crear un Adaptador MCP Unificado**

No te conectarás a cada MCP por separado. Crearás un único adaptador responsable de la comunicación con cualquier servidor MCP, siguiendo el **Principio de Responsabilidad Única**.

1.  **Acción:** Crear un nuevo archivo: `src/ultibot_backend/adapters/mcp_adapter.py`.
2.  **Contenido de la Clase `MCPAdapter`:**
    -   Tendrá un método principal, por ejemplo, `execute_tool(self, server_url: str, tool_name: str, params: dict) -> dict:`.
    -   Este método será un cliente HTTP simple (usando la librería `httpx`, que ya está en tu stack). Construirá una petición POST a la `server_url` con un cuerpo JSON que contenga el nombre de la herramienta y sus parámetros, tal como lo especifique el protocolo MCP.
    -   Manejará la respuesta y las excepciones (timeouts, errores de conexión, JSON malformado).
3.  **Justificación:** El resto de tu aplicación no necesita saber hablar "MCP". Solo necesita hablar con tu `MCPAdapter`. Esto desacopla tu lógica de negocio de la implementación específica del protocolo.

#### **Paso 2: Implementar un Registro de Herramientas (Tool Registry)**

El Agente IA necesita saber qué herramientas tiene disponibles y para qué sirven. Esto debe ser explícito.

1.  **Acción:** Crear un nuevo servicio: `src/ultibot_backend/services/tool_registry_service.py`.
2.  **Funcionalidad:**
    -   Este servicio mantendrá una lista de todas las herramientas MCP disponibles. Inicialmente, puedes definir esto en un archivo de configuración (ej. `tools.yaml`) para no tenerlo hardcodeado.
    -   Cada herramienta registrada tendrá un **esquema claro**:
        -   `name`: `get_crypto_price_history_ccxt`
        -   `description`: "Obtiene el historial de precios OHLCV para un símbolo de criptomoneda desde un exchange específico usando CCXT. Útil para análisis técnico." (Esta descripción es para que la entienda el Agente IA).
        -   `mcp_server_url`: La URL del servidor MCP que aloja esta herramienta (ej. `http://localhost:8001`).
        -   `parameters`: Un esquema JSON que define los parámetros de entrada (ej. `{"symbol": "string", "timeframe": "string", "exchange": "string"}`).
3.  **Justificación:** Permite añadir, quitar o modificar herramientas sin tocar el código del orquestador. El Agente IA puede consultar este registro para decidir qué herramienta es la más adecuada para una tarea.

#### **Paso 3: Rediseñar el Flujo del `AIOrchestratorService` (El Núcleo)**

Aquí es donde ocurre la magia. El flujo de trabajo del orquestador cambia de un simple "pregunta-respuesta" a un ciclo de **"Planificación -> Ejecución -> Síntesis"**.

1.  **Acción:** Refactorizar `src/ultibot_backend/services/ai_orchestrator_service.py`.
    
2.  **Nuevo Flujo de Ejecución:**
    
    a. **Consulta Inicial:** El servicio recibe una consulta del usuario (ej. "Analiza la volatilidad de ETH/USDT en el último día y dame una opinión").
    
    b. **Fase de Planificación (1er llamado a Gemini):** * El orquestador obtiene la lista de herramientas del `ToolRegistryService`. * Construye un _prompt_ para Gemini que incluye: 1. La consulta original del usuario. 2. Una sección titulada **"Herramientas Disponibles"** con las descripciones y parámetros de cada herramienta. 3. Una instrucción crucial: "Analiza la petición del usuario. Si necesitas usar una de estas herramientas para responder, responde únicamente con un objeto JSON con las claves 'tool_name' y 'parameters'. Si no necesitas una herramienta, responde directamente a la pregunta". * **El objetivo de esta primera llamada no es obtener la respuesta final, sino un plan de acción.**
    
    c. **Fase de Ejecución (Lógica del Orquestador):** * El orquestador recibe la respuesta de Gemini. * **Si la respuesta es el JSON de una herramienta**: * Extrae `tool_name` y `parameters`. * Usa el `MCPAdapter` para ejecutar la herramienta: `tool_result = mcp_adapter.execute_tool(server_url, tool_name, params)`. * **Si la respuesta no es un JSON**: Es la respuesta final, se devuelve directamente.
    
    d. **Fase de Síntesis (2do llamado a Gemini, si fue necesario):** * Si se ejecutó una herramienta, el orquestador ahora construye un _segundo prompt_: * "Contexto: El usuario preguntó originalmente '[consulta original]'." * "Para responder, se utilizó la herramienta '[tool_name]' y se obtuvieron los siguientes datos: `[resultado_de_la_herramienta]`." * "Ahora, usando estos datos, por favor proporciona una respuesta completa y bien fundamentada a la pregunta original del usuario." * Se envía este prompt a Gemini. **Ahora el modelo tiene toda la información necesaria para razonar y construir la respuesta final.**
    
    e. **Respuesta Final:** La respuesta de la fase de síntesis se devuelve al usuario.
    

----------

**Conclusión:**

Tu idea es **excelente** y lejos de ser un caso perdido. Es la implementación correcta para un sistema robusto. El problema fue una falta de visión arquitectónica en la implementación.

Al adoptar este patrón de **Orquestador + Adaptador + Registro**, tu sistema se vuelve:

-   **Extensible:** Añadir nuevas herramientas (incluso de fuentes que no sean MCP) solo requiere crear un adaptador y registrarlas.
-   **Eficiente:** El modelo de lenguaje se usa para lo que es mejor (razonamiento y planificación), no para realizar tareas de bajo nivel.
-   **Controlable:** Tienes visibilidad completa sobre qué herramientas se llaman y con qué datos.

Esta es la solución. Entrégasela a tu desarrollador; es un plan de acción técnico y directo para materializar tu visión.