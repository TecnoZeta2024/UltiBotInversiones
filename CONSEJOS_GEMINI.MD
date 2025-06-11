# Manifiesto Arquitectónico: UltiBotInversiones

> **Versión:** 2.1 **Fecha:** 11 de junio de 2025 **Autor:** Cline, Arquitecto de Software Principal **Misión:** Transformar `UltiBotInversiones` en una plataforma de trading algorítmico, potenciada por IA, que opere con la precisión, rendimiento y belleza de un reloj atómico óptico.

## 1. Visión y Filosofía de Diseño: El Reloj Atómico Óptico

Un reloj atómico no es simplemente preciso; es la definición misma de la precisión. Cada componente, desde el láser que enfría los átomos hasta el oscilador de cuarzo, trabaja en perfecta sincronía, desacoplado pero interconectado. Esta es nuestra filosofía rectora.

Nuestra arquitectura se basará en tres principios fundamentales:

-   **Precisión (Precision):** Cada acción, desde el cálculo de un indicador hasta la ejecución de una orden, debe ser determinista, auditable y libre de efectos secundarios. La ambigüedad no tiene cabida.
    
-   **Rendimiento (Performance):** El sistema debe operar con una latencia mínima en un entorno asíncrono y no bloqueante. Los flujos de datos y eventos deben ser fluidos e instantáneos.
    
-   **Plasticidad (Plasticity):** La arquitectura debe ser flexible y extensible. Añadir una nueva estrategia, una fuente de datos o una herramienta de IA no debe requerir una refactorización del núcleo, sino ser tan simple como añadir un nuevo "engranaje" al reloj.
    

## 2. Diagrama de Contexto del Sistema

Este proyecto, `UltiBotInversiones`, es una plataforma de trading personal y privada diseñada para ejecutar múltiples estrategias sofisticadas de trading en tiempo real. La arquitectura está concebida para garantizar latencia ultra-baja, procesamiento paralelo eficiente y una integración fluida con servicios externos críticos como Binance, Telegram, Mobula, herramientas MCP (Model Context Protocol) y Gemini AI.

La arquitectura ha sido concebida para satisfacer los requisitos no funcionales más exigentes (rendimiento, seguridad, fiabilidad) mientras mantiene la flexibilidad para evolucionar más allá de la v1.0. Su objetivo principal es servir como el plano técnico definitivo para el desarrollo impulsado por IA, asegurando consistencia y adherencia a los patrones y tecnologías elegidos.

## 3. Parte I: La Arquitectura del Núcleo (`ultibot_backend`)

Para alcanzar la **Precisión** y el **Rendimiento**, debemos evolucionar más allá de una arquitectura de servicios tradicional y adoptar patrones probados en sistemas de alta criticidad.

### 3.1. Arquitectura Hexagonal (Puertos y Adaptadores)

El backend se reestructurará siguiendo un estricto modelo de Arquitectura Hexagonal. Esto garantiza un aislamiento total del dominio de negocio (el "corazón" del sistema) de las tecnologías externas (frameworks, bases de datos, APIs).

-   **El Núcleo del Dominio (`/core`):** Aquí reside la lógica pura del negocio (`TradingEngineService`, `PortfolioService`, `StrategyService`). **Regla Mandatoria:** Este directorio no tendrá **NINGUNA** importación de `fastapi`, `sqlalchemy`, o cualquier otra librería externa. Solo lógica de Python pura y nuestros modelos de dominio (`/core/domain_models`).
    
-   **Puertos (Interfaces):** Clases base abstractas que definen los "contratos" de comunicación. Por ejemplo, `IMarketDataProvider` o `IPersistencePort`.
    
-   **Adaptadores (`/adapters`):** Implementaciones concretas de los puertos. `BinanceAdapter` implementará `IMarketDataProvider`. `PostgresAdapter` implementará `IPersistencePort`.
    

```
graph TD
    subgraph Núcleo del Dominio (Lógica Pura)
        A[TradingEngineService]
        B[PortfolioService]
        C[StrategyService]
        D[AIOrchestratorService]
    end

    subgraph Puertos (Interfaces)
        P1(Inbound: IAPIPort)
        P2(Outbound: IMarketDataProvider)
        P3(Outbound: IPersistencePort)
        P4(Outbound: IToolExecutionPort)
    end

    subgraph Adaptadores (Tecnología Concreta)
        Ad1[API de FastAPI]
        Ad2[BinanceAdapter]
        Ad3[MobulaAdapter]
        Ad4[PostgresAdapter]
        Ad5[MCPToolAdapter]
    end

    Ad1 -- Implementa --> P1
    P1 -- Invoca --> A
    A -- Utiliza --> P2
    A -- Utiliza --> P3
    D -- Utiliza --> P4
    P2 -- Es implementado por --> Ad2
    P2 -- Es implementado por --> Ad3
    P3 -- Es implementado por --> Ad4
    P4 -- Es implementado por --> Ad5

```

### 3.2. Flujo de Datos con CQRS (Command Query Responsibility Segregation)

Para un rendimiento y una claridad máximos, separaremos las operaciones de escritura (Comandos) de las de lectura (Consultas).

-   **Comandos:** Acciones que mutan el estado del sistema. Cada comando será una clase Pydantic específica que se envía a un endpoint `/commands/{command_name}`.
    
    -   Ej: `PlaceOrderCommand(asset, amount, price, side)`
        
    -   Ej: `ActivateStrategyCommand(strategy_id, parameters)`
        
-   **Consultas:** Acciones que leen datos sin modificarlos.
    
    -   Ej: `GetPortfolioQuery(user_id)`
        
    -   Ej: `GetStrategyPerformanceQuery(strategy_id)`
        

Esto simplifica la lógica, permite optimizar las lecturas (ej. usando caché o réplicas de base de datos) y hace que el flujo de intención del usuario sea explícito y auditable.

### 3.3. Sistema Asíncrono Orientado a Eventos

El núcleo funcionará como un sistema reactivo.

1.  **Broker de Eventos:** Se implementará un `EventBroker` central.
    
2.  **Publicación de Eventos:** Cuando un servicio completa una acción crítica, publica un evento. Ej: `TradingEngineService` publica un `TradeExecutedEvent`.
    
3.  **Suscripción de Servicios:** Otros servicios se suscriben a estos eventos. `PerformanceService` y `NotificationService` escucharán el `TradeExecutedEvent` para actualizar métricas y notificar al usuario, respectivamente. Todo de forma asíncrona y desacoplada.
    

## 4. Parte II: La Interfaz de Usuario (`ultibot_ui`)

Para lograr la **Belleza** y **Funcionalidad**, la UI debe ser una capa de presentación delgada, reactiva y estéticamente coherente.

### 4.1. Patrón de Diseño Model-View-ViewModel (MVVM)

Actualmente, la lógica de la UI está mezclada en los `workers` y las `windows`. Adoptaremos MVVM para una separación de responsabilidades limpia y testeable.

-   **Modelo (`/services/api_client.py`):** La capa de datos, responsable únicamente de comunicarse con el backend.
    
-   **Vista (`/widgets`, `/windows`):** Los componentes PyQt6. Su única responsabilidad es mostrar datos y delegar las acciones del usuario al ViewModel. Deben ser "tontos" por diseño.
    
-   **ViewModel (`/viewmodels` -** _**nuevo directorio**_**):** El mediador. Habrá un ViewModel por cada vista compleja (ej. `DashboardViewModel`).
    
    -   Expone propiedades a las que la Vista se puede enlazar (ej. `self.portfolio_value`).
        
    -   Expone comandos que la Vista puede invocar (ej. `self.refresh_data_command`).
        
    -   Contiene toda la lógica de presentación, como formatear un número para mostrarlo como moneda.
        

### 4.2. Motor Centralizado de Estilos (QSS)

Para una belleza consistente, eliminaremos todos los estilos en línea.

-   **Acción:** Crear un directorio `/resources/themes`.
    
-   **Acción:** Dentro, crear archivos como `dark_theme.qss` y `light_theme.qss`.
    
-   **Acción:** En `main.py`, se cargará el archivo QSS seleccionado y se aplicará a toda la aplicación. Esto permite un cambio de tema instantáneo y asegura que cada `MagicCard` y cada `ChartWidget` se vean exactamente iguales.
    

### 4.3. Un Dashboard Reimaginado y Vistas Dedicadas

La UI se reorganizará para una experiencia de usuario superior.

-   **Dashboard:** Será el centro de comando. No mostrará gráficos complejos. Su propósito es dar una visión general de un vistazo:
    
    -   KPIs clave: P&L del día, estado de APIs, Trades Abiertos.
        
    -   Feed de Actividad del Agente IA.
        
    -   Feed de Oportunidades Recientes.
        
-   **Nueva Vista: "Análisis de Mercado":** Esta vista contendrá los `ChartWidget` y herramientas de análisis técnico. Será un espacio de trabajo dedicado para la investigación.
    
-   **Nueva Vista: "AI Studio":** Un espacio dedicado para interactuar con el agente IA, como se detalla en la siguiente sección.
    

## 5. Parte III: El Núcleo Inteligente (Estrategias y IA)

Aquí es donde alcanzamos la **Plasticidad**.

### 5.1. Motor de Estrategias Plug-and-Play

El `StrategyService` se convertirá en un cargador dinámico.

-   **Directorio:** Se creará un directorio `src/ultibot_backend/strategies`.
    
-   **Interfaz Base:** Se definirá una `BaseStrategy` con métodos abstractos como `setup(params)`, `analyze(market_data)` y `generate_signal()`.
    
-   **Cargador Dinámico:** Al iniciar, el `StrategyService` escaneará este directorio, importará cualquier clase que herede de `BaseStrategy` y la registrará como una estrategia disponible en todo el sistema.
    
-   **UI:** La `StrategyManagementView` permitirá al usuario ver estas estrategias cargadas dinámicamente, configurar sus parámetros y activarlas.
    
-   **Requisito Mínimo:** Se debe desarrollar una biblioteca inicial de **10 estrategias diversas** para dotar al sistema y al Agente IA de un arsenal completo.
    

#### 5.1.1. Biblioteca de Estrategias Mínima

1.  **Momentum & Trend Following:**
    
    1.  `MACD_RSI_Trend_Rider`: Sigue tendencias confirmadas por MACD y RSI.
        
    2.  `SuperTrend_Volatility_Filter`: Entra en tendencias marcadas por SuperTrend, pero solo si la volatilidad (ATR) está dentro de un rango.
        
2.  **Mean Reversion:** 3. `Bollinger_Bands_Squeeze_Breakout`: Opera los breakouts tras períodos de baja volatilidad (bandas estrechas). 4. `Stochastic_RSI_Overbought_Oversold`: Busca reversiones en niveles extremos de sobrecompra/sobreventa.
    
3.  **Arbitraje y Valor Relativo:** 5. `Triangular_Arbitrage_Spot`: Busca oportunidades de arbitraje sin riesgo entre tres pares (ej. BTC-ETH, ETH-USDT, BTC-USDT). 6. `Statistical_Arbitrage_Pairs_Trading`: Busca dos activos altamente correlacionados y opera en la divergencia de sus precios.
    
4.  **Basadas en Volumen y Order Book:** 7. `VWAP_Cross_Strategy`: Opera cruces del precio con el VWAP (Volume-Weighted Average Price). 8. `Order_Book_Imbalance_Scalper`: Detecta grandes desbalances entre órdenes de compra/venta en el libro de órdenes para predecir movimientos a corto plazo.
    
5.  **Event-Driven y Sentimiento (Potenciadas por IA):** 9. `News_Sentiment_Spike_Trader`: Utiliza herramientas MCP para detectar picos de sentimiento en noticias y redes sociales. 10. `On_Chain_Metrics_Divergence`: Usa herramientas MCP para encontrar divergencias entre el precio y métricas on-chain clave (ej. flujos de exchange, grandes transacciones).
    

### 5.2. El Orquestador de IA y el Hub de Herramientas MCP (Solución Definitiva)

La idea de usar MCPs es correcta; la ejecución inicial fue errónea. La solución es una doble capa de abstracción.

```
sequenceDiagram
    participant User
    participant AI_Studio_View as Vista: AI Studio
    participant AIOrchestratorService as Backend: Orquestador IA
    participant MCPToolHub as Backend: Hub de Herramientas
    participant SpecificAdapter as Backend: Ej: MetatraderAdapter

    User->>AI_Studio_View: Escribe: "Encuentra criptos con sentimiento alcista extremo"
    AI_Studio_View->>AIOrchestratorService: execute_ai_task(prompt)
    AIOrchestratorService->>MCPToolHub: list_available_tools()
    MCPToolHub-->>AIOrchestratorService: ["get_sentiment", "get_onchain_data", ...]
    AIOrchestratorService->>Gemini: "Basado en este objetivo y estas herramientas, ¿qué herramienta debo usar y con qué parámetros?" (Planificación)
    Gemini-->>AIOrchestratorService: "{'tool': 'get_sentiment', 'params': {'asset': 'all_crypto'}}"
    AIOrchestratorService->>MCPToolHub: execute_tool("get_sentiment", {'asset': 'all_crypto'})
    MCPToolHub->>SpecificAdapter: execute({'asset': 'all_crypto'})
    SpecificAdapter-->>MCPToolHub: Retorna datos de sentimiento
    MCPToolHub-->>AIOrchestratorService: Retorna datos de sentimiento
    AIOrchestratorService->>Gemini: "Con estos datos, genera la respuesta final" (Síntesis)
    Gemini-->>AIOrchestratorService: "Las criptos con mayor sentimiento alcista son..."
    AIOrchestratorService-->>AI_Studio_View: Devuelve respuesta final
    AI_Studio_View->>User: Muestra la respuesta

```

-   **`AIOrchestratorService`:** Su única responsabilidad es dialogar con el LLM (Gemini) para planificar y sintetizar.
    
-   **`MCPToolHub`:** Mantiene un registro de todas las herramientas disponibles. Expone métodos como `list_available_tools()` y `execute_tool(name, params)`.
    
-   **`BaseToolAdapter`:** Una interfaz que define `execute(params)`.
    
-   **Adaptadores Concretos:**  `MetatraderAdapter`, `ArmorWalletAdapter`, `Web3ResearchAdapter`. Cada uno implementa `BaseToolAdapter` y contiene la lógica para comunicarse con su respectivo servidor MCP. **Esta es la clave que faltaba.**
    

### 5.3. El AI Prompt Studio

Para un control total sobre la IA:

-   **Persistencia:** Todos los prompts (del sistema, de planificación, de síntesis) se moverán del código a una tabla en la base de datos Supabase.
    
-   **UI (`AIStudioView`):** Una nueva vista permitirá:
    
    -   Ver, crear, editar y versionar las plantillas de prompts usando un editor de texto enriquecido.
        
    -   Un "Playground" donde se puede seleccionar un prompt, proporcionar datos de contexto (ej. un JSON de datos de mercado) y hacer clic en "Ejecutar" para ver la salida exacta de la IA, permitiendo un ajuste fino y rápido.
        

### 5.4. Gestor de Presets de Mercado

Para acelerar la búsqueda de oportunidades, se creará un sistema de presets de escaneo de mercado.

-   **Requisito Mínimo:** Se debe desarrollar una biblioteca inicial de **10 presets de escaneo** enfocados en diferentes tipos de oportunidades.
    
-   **Ejemplos de Presets:**
    
    1.  **Explosive Volatility:** Busca activos con ATR(14) en el 5% superior y volumen en las últimas 24h > $10M.
        
    2.  **Sleeping Giants:** Activos con capitalización > $1B pero con volatilidad en el 10% inferior (posible acumulación).
        
    3.  **High Momentum:** Activos cuyo precio está por encima de las medias móviles de 20, 50 y 200 períodos.
        
    4.  **Strong Mean Reversion Candidates:** Activos fuera de las 2 desviaciones estándar de las Bandas de Bollinger.
        
    5.  **New Listings High Volume:** Activos listados en Binance en los últimos 7 días con volumen creciente.
        
    6.  **Social Sentiment Rockets:** Activos con un pico de >50% en menciones sociales positivas (vía MCP).
        
    7.  **On-Chain Whales:** Activos con un aumento significativo en la actividad de grandes billeteras (vía MCP).
        
    8.  **DeFi Blue Chips:** Top 10 activos de DeFi por TVL con correlación negativa a BTC.
        
    9.  **Low-Cap Gems:** Activos con market cap < $50M pero con commits de código diarios en su Github.
        
    10.  **Forex Majors Breakout:** Pares de divisas mayores (EUR/USD, etc.) que han roto su rango de las últimas 24h.
        

## 6. Project Structure

Una estructura de directorios clara es fundamental para la mantenibilidad y para depurar archivos que no cumplen una función útil. La siguiente estructura está alineada con la arquitectura propuesta y sirve como guía para la organización del código en `src/`.

```
src/
├── ultibot_backend/
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── binance_adapter.py        # Implementa IMarketDataProvider, IOrderExecutionPort
│   │   ├── mobula_adapter.py         # Implementa IMarketDataProvider (secundario)
│   │   ├── telegram_adapter.py       # Implementa INotificationPort
│   │   ├── postgres_adapter.py       # Implementa IPersistencePort
│   │   └── mcp_tools/
│   │       ├── __init__.py
│   │       ├── base_mcp_adapter.py   # Define la interfaz IToolAdapter
│   │       └── ...                   # Adaptadores específicos para cada MCP
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                   # Punto de entrada de FastAPI
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── commands.py           # Endpoints para Comandos CQRS
│   │       └── queries.py            # Endpoints para Consultas CQRS
│   ├── core/
│   │   ├── __init__.py
│   │   ├── domain_models/            # Modelos Pydantic puros del negocio
│   │   ├── ports.py                  # Definición de todas las interfaces (Puertos)
│   │   └── services/                 # Lógica de negocio pura (TradingEngine, etc.)
│   ├── strategies/                   # Directorio para las estrategias Plug-and-Play
│   │   ├── __init__.py
│   │   ├── base_strategy.py
│   │   └── ...                       # Archivos de estrategias individuales
│   ├── __main__.py                   # Permite ejecutar el backend como módulo
│   └── app_config.py                 # Carga de configuración y dependencias
│
└── ultibot_ui/
    ├── __init__.py
    ├── resources/
    │   ├── icons/
    │   └── themes/
    │       ├── dark_theme.qss
    │       └── light_theme.qss
    ├── services/
    │   ├── __init__.py
    │   └── api_client.py             # Cliente HTTP para comunicarse con el backend
    ├── viewmodels/
    │   ├── __init__.py
    │   ├── dashboard_viewmodel.py
    │   └── ...                       # ViewModels para cada vista
    ├── views/                        # Vistas complejas que agrupan widgets
    │   ├── __init__.py
    │   ├── dashboard_view.py
    │   ├── analysis_view.py
    │   ├── ai_studio_view.py
    │   └── ...
    ├── widgets/                      # Componentes de UI reutilizables
    │   ├── __init__.py
    │   ├── magic_card_widget.py
    │   └── ...
    ├── windows/
    │   ├── __init__.py
    │   └── main_window.py            # La ventana principal de la aplicación
    ├── __main__.py
    └── main.py                       # Punto de entrada de la aplicación UI

```

**Nota sobre la depuración:** Cualquier archivo en el `src/` actual que no encaje en esta estructura debe ser evaluado. Probablemente pertenezca a una versión anterior de la lógica (ej. lógica de UI en `workers.py` que debería moverse a un `ViewModel`) o ya no sea necesario.

## 7. Diagrama de Componentes y APIs Externas

### 7.1. APIs Externas Consumidas

#### 7.1.1. Binance API

-   **Purpose:** La API de Binance se utiliza para obtener datos de mercado en tiempo real e históricos, ejecutar órdenes de trading (spot), gestionar órdenes, y consultar balances de cuenta. Es la plataforma de exchange principal.
    
-   **Base URL(s):**
    
    -   Production (REST): `https://api.binance.com`
        
    -   Production (WebSockets): `wss://stream.binance.com:9443/ws`
        
-   **Authentication:**
    
    -   REST API: `API-Key` (`BINANCE_API_KEY`) en `X-MBX-APIKEY` y `HMAC SHA256 signature`.
        
    -   WebSockets: `listenKey` para streams de datos de usuario.
        
-   **Key Endpoints & Streams:**
    
    -   REST: `GET /api/v3/account`, `POST /api/v3/order`, `GET /api/v3/klines`, `POST /api/v3/userDataStream` y sus correspondientes `PUT`/`DELETE`.
        
    -   WebSockets: `<symbol>@kline_<interval>`, `<symbol>@ticker`, `!miniTicker@arr`, y streams de datos de usuario.
        
-   **Rate Limits:** Deben ser gestionados programáticamente dentro del `BinanceAdapter` con reintentos exponenciales y una cola de prioridades para las llamadas.
    
-   **Link to Official Docs:**  [https://binance-docs.github.io/apidocs/spot/en/](https://binance-docs.github.io/apidocs/spot/en/ "null")
    

#### 7.1.2. Telegram Bot API

-   **Purpose:** Se utiliza para enviar notificaciones y alertas al usuario (confirmaciones de trade, errores críticos, alertas de IA).
    
-   **Base URL:**  `https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/`
    
-   **Authentication:** A través del `TELEGRAM_BOT_TOKEN` en la URL.
    
-   **Key Endpoints Used:**  `POST /sendMessage`.
    
-   **Rate Limits:** Gestionados en el `TelegramAdapter` para evitar el bloqueo del bot.
    
-   **Link to Official Docs:**  [https://core.telegram.org/bots/api](https://core.telegram.org/bots/api "null")
    

#### 7.1.3. Mobula API

-   **Purpose:** Para la verificación y obtención de metadatos de criptoactivos (direcciones de contrato, redes sociales, etc.), complementando la información de Binance.
    
-   **Base URL:**  `https://api.mobula.io/api/1`
    
-   **Authentication:** API Key en el header `Authorization`.
    
-   **Key Endpoints Used:**  `GET /search`, `GET /market/data`, `GET /market/history`.
    
-   **Rate Limits:** Gestionados en el `MobulaAdapter`.
    
-   **Link to Official Docs:**  [https://docs.mobula.io/](https://docs.mobula.io/ "null")
    

#### 7.1.4. Google Gemini API

-   **Purpose:** Es el motor de IA para análisis avanzado, planificación de uso de herramientas y síntesis de respuestas. Se usará Gemini 1.5 Pro/Flash por su ventana de contexto y capacidades de razonamiento.
    
-   **Authentication:** API Key de Google (`GEMINI_API_KEY`).
    
-   **Interaction Pattern:** La interacción se abstraerá a través de la librería `google-generativeai` y el framework LangChain para la orquestación de agentes y el uso de herramientas (Tool Use). Esto es fundamental para que Gemini pueda interactuar con los adaptadores MCP.
    
-   **Link to Official Docs:**
    
    -   Google AI: [https://ai.google.dev/docs](https://ai.google.dev/docs "null")
        
    -   LangChain (Python): [https://python.langchain.com/](https://python.langchain.com/ "null")
        

## 8. Coding Standards & Testing

### 8.1. Coding Standards

-   **Estilo:** PEP 8 estricto, formateado automáticamente con `black`.
    
-   **Tipado:** 100% de type hints estáticos, verificado con `mypy`.
    
-   **Linting:**  `ruff` o `flake8` para asegurar la calidad y detectar errores comunes.
    
-   **Nomenclatura:** Clases en `CamelCase`, funciones y variables en `snake_case`. Interfaces prefijadas con `I` (ej. `IMarketDataProvider`).
    
-   **Documentación:** Docstrings en formato Google para todos los módulos, clases y funciones públicas.
    

### 8.2. Overall Testing Strategy

-   **Unit Tests:** Cada servicio, adaptador y viewModel debe tener tests unitarios que verifiquen su lógica de forma aislada, usando mocks para dependencias externas.
    
-   **Integration Tests:** Se probará la interacción entre los servicios del núcleo y los adaptadores contra entornos de prueba (Testnet de Binance, base de datos de prueba).
    
-   **End-to-End (E2E) Tests:** Scripts que simulan el flujo completo: desde una acción en la UI, pasando por el backend, hasta la ejecución en una API externa (en modo simulación o Testnet).
    
-   **Cobertura:** Se buscará una cobertura de tests > 85% para los módulos críticos del backend.
    

## 9. Infraestructura y Despliegue (v1.0 Local)

-   Dada la naturaleza de `UltiBotInversiones` como una aplicación de escritorio para uso personal, la infraestructura es local.
    
-   **Backend:** Se ejecuta como un proceso local con `uvicorn`.
    
-   **Frontend:** Se ejecuta como una aplicación PyQt6 nativa.
    
-   **Base de Datos:** Se utilizará un contenedor Docker con PostgreSQL para la persistencia local de datos de trading, o una conexión directa a Supabase si se prefiere una solución gestionada. La configuración debe ser flexible.
    
-   **Empaquetado:** Para la distribución, se utilizará `PyInstaller` o `cx_Freeze` para crear un ejecutable autocontenido para Windows, simplificando la instalación para el usuario final.
    

## 10. Hoja de Ruta de Implementación (Revisada)

1.  **Fase 1: Cimientos (2 Semanas)**
    
    -   **Backend:** Refactorizar a Arquitectura Hexagonal y CQRS. Implementar el Broker de Eventos.
        
    -   **UI:** Implementar el patrón MVVM y el motor de estilos QSS. Reestructurar la navegación principal.
        
2.  **Fase 2: El Núcleo Funcional (1 Semana)**
    
    -   **Backend:** Implementar el Motor de Estrategias Plug-and-Play y desarrollar 3 de las 10 estrategias.
        
    -   **UI:** Crear la `StrategyManagementView` y el gestor de presets (con 3 presets iniciales).
        
3.  **Fase 3: La Inteligencia (2 Semanas)**
    
    -   **Backend:** Construir el `AIOrchestratorService`, `MCPToolHub` y al menos dos `Adapters` MCP como prueba de concepto. Mover los prompts a la BD.
        
    -   **UI:** Desarrollar la vista `AIStudioView` con el editor y el Playground.
        
4.  **Fase 4: Expansión y Pulido (2 Semanas)**
    
    -   Desarrollar las 7 estrategias y 7 presets restantes.
        
    -   Conectar todos los nuevos componentes y realizar pruebas de integración end-to-end.
        
    -   Refinar la estética de la UI basada en el nuevo motor de temas.
        

Este documento es el plan para construir no solo un software, sino un instrumento de precisión. Cada decisión arquitectónica está tomada para servir a la visión del **reloj atómico óptico**: un sistema donde cada parte funciona en perfecta, bella y funcional armonía.