# UltiBotInversiones Architecture Document

## Introduction / Preamble

Este documento detalla la arquitectura técnica general de UltiBotInversiones, una plataforma avanzada de trading personal diseñada para ejecutar múltiples estrategias sofisticadas de trading (scalping, day trading y arbitraje) en tiempo real. La arquitectura está diseñada para garantizar latencia ultra-baja, procesamiento paralelo eficiente y una integración fluida con servicios externos críticos como Binance, Telegram, Gemini AI y servidores MCP.

La arquitectura ha sido concebida para satisfacer los requisitos no funcionales exigentes (rendimiento, seguridad, fiabilidad) mientras mantiene la flexibilidad para evolucionar más allá de la v1.0. Su objetivo principal es servir como el plano técnico definitivo para el desarrollo impulsado por IA, asegurando consistencia y adherencia a los patrones y tecnologías elegidos.

**Relationship to Frontend Architecture:**
Dado que UltiBotInversiones incluye una interfaz de usuario significativa implementada con PyQt5, se desarrollará un Documento de Arquitectura Frontend separado que detallará los aspectos específicos de la UI. Este documento principal establece las decisiones tecnológicas fundamentales para todo el proyecto, incluyendo la interfaz de usuario.

## Technical Summary

UltiBotInversiones se implementará como un **Monolito Modular** dentro de una estructura de **Monorepo**, con módulos claramente definidos que incluyen la interfaz de usuario (UI con **PyQt5**), la lógica del núcleo de trading (para operaciones simuladas y reales), la gestión de datos, los servicios de Inteligencia Artificial (IA) y las notificaciones. El sistema utilizará **Python 3.11+** como lenguaje principal para el backend, apoyándose en **FastAPI** para la creación de servicios internos. La persistencia de datos se gestionará con **PostgreSQL** (a través de **Supabase**), utilizando el cliente `supabase-py`, y se empleará **Redis** para la caché L2. Las interacciones HTTP asíncronas se realizarán con `httpx` y las conexiones WebSocket (ej. con Binance) mediante la biblioteca `websockets`. Las tareas en segundo plano, como los análisis de IA complejos, se gestionarán inicialmente con las `BackgroundTasks` de FastAPI.

El motor de análisis de IA se basará en **Gemini** (específicamente modelos como Gemini 1.5 Pro o Flash), orquestado mediante **LangChain (Python)**. Esta aproximación permitirá a Gemini interactuar con "Herramientas" desarrolladas como wrappers para APIs externas, incluyendo los **Servidores MCP** (para detección de oportunidades), la **API de Binance** (para datos de mercado y ejecución de operaciones), y la **API de Mobula** (para verificación de datos de activos). Otras integraciones clave incluyen la **API de Telegram** para notificaciones al usuario.

La arquitectura está optimizada para una **latencia ultra-baja** (objetivo <500ms para el ciclo completo de detección-análisis-ejecución) y un eficiente **procesamiento asíncrono/paralelo**. El diseño se adhiere a principios de Domain-Driven Design (DDD) y, donde sea aplicable, Command Query Responsibility Segregation (CQRS), con un fuerte énfasis en la modularidad para facilitar la posible evolución futura hacia una Arquitectura Orientada a Eventos con Microservicios Opcionales post-v1.0.

## High-Level Overview

UltiBotInversiones adopta un **Monolito Modular** como su estilo arquitectónico principal para la v1.0, siguiendo la decisión documentada en el PRD. Esta elección favorece la velocidad de desarrollo inicial manteniendo una clara separación de responsabilidades a través de módulos bien definidos. El sistema está organizado como un **Monorepo**, facilitando la gestión de dependencias y la coherencia entre componentes, mientras prepara el terreno para una posible evolución futura hacia una arquitectura más distribuida.

El sistema implementa un patrón de **flujo de datos unidireccional** para su funcionamiento principal: desde la captura de datos del mercado y detección de oportunidades (a menudo iniciada por **Servidores MCP**), pasando por un análisis y toma de decisiones sofisticados —orquestados por **LangChain (Python)** que permite a **Gemini** utilizar diversas herramientas (incluyendo los propios MCPs, datos de Binance, y Mobula)—, hasta la ejecución de la operación (simulada o real) y la notificación al usuario (vía UI y Telegram). Este flujo garantiza un procesamiento predecible y una clara trazabilidad de las decisiones operativas.

## Diagrama de Contexto del Sistema (Mermaid C4 Model - Nivel 1):

graph TD
    User["Usuario de UltiBotInversiones"] 
    
    subgraph "UltiBotInversiones"
        UI["Interfaz de Usuario\n(PyQt5)"]
        Core["Núcleo de Trading\n(Paper & Real)"]
        AI_Orchestrator["Orquestador de Análisis IA\n(LangChain + Gemini + Herramientas)"]
        DataMgmt["Gestión de Datos\n(Supabase/PostgreSQL)"]
        NotifSys["Sistema de Notificaciones"]
    end
    
    subgraph "Servicios Externos"
        Binance["Binance API\n(Datos & Ejecución)"]
        Telegram["Telegram Bot API\n(Notificaciones)"]
        MCPs["Servidores MCP Externos\n(Herramienta para IA)"]
        Mobula["Mobula API\n(Herramienta para IA)"]
        GeminiAPI["Google Gemini API\n(Motor IA para LangChain)"]
    end
    
    User -->|"Configura, Monitorea,\nConfirma Operaciones"| UI
    UI -->|"Muestra Datos,\nNotificaciones"| User
    
    UI <-->|"Envía Acciones,\nRecibe Estado"| Core
    Core <-->|"Solicita Análisis,\nRecibe Decisión IA"| AI_Orchestrator
    Core <-->|"Lee/Escribe\nDatos Persistentes"| DataMgmt
    Core -->|"Genera Eventos\nde Notificación"| NotifSys
    
    Core <-->|"Datos de Mercado,\nEjecución de Órdenes"| Binance
    NotifSys -->|"Envía Alertas"| Telegram
    AI_Orchestrator -->|"Utiliza Herramienta MCP"| MCPs
    AI_Orchestrator -->|"Utiliza Herramienta Mobula"| Mobula
    AI_Orchestrator <-->|"Consulta Motor IA"| GeminiAPI
    AI_Orchestrator -->|"Puede usar Herramienta Binance"| Binance

## Architectural / Design Patterns Adopted

A continuación, se listan los patrones arquitectónicos y de diseño fundamentales que se adoptarán para "UltiBotInversiones":

* **Monolito Modular (Modular Monolith):**
    * _Rationale/Referencia:_ Es el estilo arquitectónico principal para la v1.0, como se decidió en el PRD. Favorece la velocidad de desarrollo inicial para el MVP, manteniendo una clara separación de responsabilidades a través de módulos bien definidos (ej. UI, núcleo de trading, gestión de datos, servicios de IA, notificaciones). Esta modularidad interna facilitará una posible evolución futura.

* **Monorepo:**
    * _Rationale/Referencia:_ La estructura del repositorio será un Monorepo, según la decisión del PRD para la v1.0. Esto simplificará la gestión de dependencias, la configuración del entorno de desarrollo y los procesos de CI/CD iniciales, además de facilitar la coherencia y refactorización en las primeras etapas.

* **Agente-Herramientas (Agent-Tool) con LangChain (Python):**
    * _Rationale/Referencia:_ Para la interacción con la IA (Gemini), se utilizará el patrón Agente-Herramientas facilitado por LangChain (Python). El agente (impulsado por Gemini) podrá decidir dinámicamente qué "herramienta" (wrappers para APIs de Binance, Servidores MCP, Mobula API, etc.) utilizar para recopilar información o ejecutar acciones, permitiendo un análisis y toma de decisiones más flexibles y potentes.

* **Procesamiento Asíncrono:**
    * _Rationale/Referencia:_ Se empleará extensivamente el procesamiento asíncrono (`async/await` en Python con bibliotecas como `httpx`, `websockets`, y las `BackgroundTasks` de FastAPI) para cumplir con el requisito de baja latencia (<500ms) y para manejar operaciones de I/O intensivas (llamadas a APIs externas, streams de datos) y tareas de larga duración (análisis de IA) sin bloquear el flujo principal de la aplicación.

* **Diseño Orientado al Dominio (Domain-Driven Design - DDD) - (Principio Guía):**
    * _Rationale/Referencia:_ El PRD valora los principios de DDD. Si bien no es un patrón estructural per se para el monolito, DDD guiará el diseño de los módulos internos, el modelado de entidades y la lógica de negocio, buscando alinear el software estrechamente con el dominio del trading y las inversiones para gestionar la complejidad.

* **Arquitectura Orientada a Eventos (Event-Driven Architecture - EDA) - (Consideración para Evolución Futura):**
    * _Rationale/Referencia:_ El PRD menciona la visión de evolucionar hacia una "Arquitectura Orientada a Eventos con Microservicios Opcionales" post-v1.0. El diseño modular actual del monolito deberá considerar interfaces y flujos de datos que puedan facilitar una futura transición hacia una EDA si el sistema escala y lo requiere, por ejemplo, para desacoplar servicios o manejar flujos de datos complejos de manera más reactiva.

* **Command Query Responsibility Segregation (CQRS) - (Consideración para Evolución Futura):**
    * _Rationale/Referencia:_ El PRD también valora CQRS como principio. Aunque probablemente no se implementará completamente en la v1.0 del monolito, el diseño de los módulos de datos y servicios podría considerar una separación conceptual de los modelos y rutas para comandos (escrituras) y consultas (lecturas) si esto simplifica la lógica o prepara el camino para futuras optimizaciones de rendimiento y escalabilidad.


## Diagrama de Componentes Principales (Mermaid C4 Model - Nivel 2):

graph TD
    UserInterface["Interfaz de Usuario (PyQt5)"]

    subgraph "UltiBotInversiones - Componentes del Monolito Modular"
        TradingEngine["Motor de Trading"]
        MarketDataMgr["Gestor de Datos de Mercado"]
        AI_Orchestrator["Orquestador de Análisis IA\n(LangChain + Gemini + Herramientas)"]
        OrderExecutor["Ejecutor de Órdenes"]
        PortfolioManager["Gestor de Portafolio"]
        StrategyManager["Gestor de Estrategias"]
        NotificationService["Servicio de Notificaciones"]
        CredentialManager["Gestor de Credenciales"]
        ConfigManager["Gestor de Configuración"]
        DataPersistenceService["Servicio de Persistencia de Datos\n(Supabase/PostgreSQL)"]
    end

    subgraph "Servicios Externos"
        BinanceAPI[("API de Binance")]
        TelegramAPI[("API de Telegram")]
        GeminiModelAPI[("API del Modelo Gemini")]
        MCPServers[("Servidores MCP")]
        MobulaAPI[("API de Mobula")]
    end

    %% Interacciones de la UI
    UserInterface --> TradingEngine
    UserInterface --> PortfolioManager
    UserInterface --> StrategyManager
    UserInterface --> ConfigManager
    UserInterface -.-> NotificationService %% UI puede leer notificaciones o disparar tests

    %% Interacciones del Motor de Trading
    TradingEngine --> MarketDataMgr
    TradingEngine --> AI_Orchestrator
    TradingEngine --> OrderExecutor
    TradingEngine --> PortfolioManager
    TradingEngine --> StrategyManager
    TradingEngine -.-> ConfigManager %% Para leer configuraciones de gestión de capital, etc.
    TradingEngine -.-> DataPersistenceService %% Para registrar histórico de trades, etc.

    %% Interacciones del Orquestador de IA
    AI_Orchestrator -.-> MarketDataMgr %% Como herramienta/fuente de datos
    AI_Orchestrator -.-> CredentialManager %% Para obtener claves de sus herramientas
    AI_Orchestrator -->|Consulta Motor IA| GeminiModelAPI
    AI_Orchestrator -->|Utiliza Herramienta| MCPServers
    AI_Orchestrator -->|Utiliza Herramienta| MobulaAPI
    AI_Orchestrator -->|Puede usar Herramienta| BinanceAPI %% Para datos adicionales

    %% Interacciones de los Gestores de Datos y Configuración
    CredentialManager --> DataPersistenceService
    ConfigManager --> DataPersistenceService
    PortfolioManager --> DataPersistenceService
    PortfolioManager -.-> MarketDataMgr %% Para precios actuales y valoración
    StrategyManager --> DataPersistenceService

    %% Interacciones con APIs Externas (directas)
    MarketDataMgr -->|Datos de Mercado| BinanceAPI
    OrderExecutor -->|Ejecución de Órdenes| BinanceAPI
    NotificationService -->|Envío de Mensajes| TelegramAPI
    
    %% Componentes que necesitan credenciales
    MarketDataMgr -.-> CredentialManager
    OrderExecutor -.-> CredentialManager
    NotificationService -.-> CredentialManager
    %% AI_Orchestrator ya tiene su línea a CredentialManager


## Project Structure

A continuación, se presenta la estructura de directorios propuesta para el Monorepo de "UltiBotInversiones". Esta estructura está diseñada para separar claramente las responsabilidades del backend, la interfaz de usuario de escritorio (PyQt5), y otros artefactos del proyecto.

{project-root}/
├── .github/                    # Workflows de CI/CD (ej. GitHub Actions)
│   └── workflows/
│       └── main.yml
├── .vscode/                    # Configuración específica para VSCode (opcional)
│   └── settings.json
├── docs/                       # Toda la documentación del proyecto (PRD, Arquitectura, Épicas, etc.)
│   ├── index.md                # Índice principal de la documentación
│   ├── PRD.md
│   ├── Architecture.md
│   ├── Epicas.md
│   └── ... (otros archivos .md como data-models.md, api-reference.md que crearemos)
├── infra/                      # Configuración de infraestructura (ej. Docker-compose para desarrollo, scripts de Supabase si son necesarios fuera de la app)
│   └── docker-compose.yml
├── scripts/                    # Scripts de utilidad (ej. para linters, formateadores, tareas de build o despliegue personalizadas)
│   └── run_linters.sh
├── src/                        # Código fuente principal de la aplicación
│   ├── ultibot_backend/        # Módulo principal del backend (Monolito Modular con FastAPI)
│   │   ├── __init__.py
│   │   ├── api/                # Endpoints/Routers de FastAPI (controladores)
│   │   │   ├── __init__.py
│   │   │   └── v1/             # Versión 1 de la API
│   │   │       ├── __init__.py
│   │   │       └── endpoints/  # Módulos para diferentes grupos de endpoints
│   │   ├── core/               # Lógica de negocio central, entidades y modelos de dominio (agnósticos al framework)
│   │   │   ├── __init__.py
│   │   │   └── domain_models/  # Modelos Pydantic o dataclasses para el dominio
│   │   ├── services/           # Implementaciones de nuestros componentes lógicos (TradingEngine, AI_Orchestrator, etc.)
│   │   │   ├── __init__.py
│   │   │   ├── trading_engine_service.py
│   │   │   ├── ai_orchestrator_service.py
│   │   │   ├── market_data_service.py
│   │   │   ├── order_execution_service.py
│   │   │   ├── portfolio_service.py
│   │   │   ├── strategy_service.py
│   │   │   ├── notification_service.py # Implementación del NotificationService
│   │   │   ├── credential_service.py   # Implementación del CredentialManager
│   │   │   └── config_service.py       # Implementación del ConfigManager
│   │   ├── adapters/           # Adaptadores para servicios externos y la capa de persistencia
│   │   │   ├── __init__.py
│   │   │   ├── binance_adapter.py
│   │   │   ├── telegram_adapter.py
│   │   │   ├── mobula_adapter.py
│   │   │   ├── mcp_tools/        # Herramientas LangChain que encapsulan clientes MCP
│   │   │   └── persistence_service.py # Implementación del DataPersistenceService (Supabase)
│   │   ├── main.py             # Punto de entrada de la aplicación FastAPI
│   │   └── app_config.py       # Configuración específica del backend (ej. carga de variables de entorno)
│   ├── ultibot_ui/             # Módulo principal de la interfaz de usuario con PyQt5
│   │   ├── __init__.py
│   │   ├── windows/            # Ventanas principales de la aplicación
│   │   ├── widgets/            # Widgets personalizados y reutilizables
│   │   ├── assets/             # Recursos de la UI (iconos, imágenes, archivos .ui si se usan)
│   │   ├── services/           # Lógica para interactuar con el backend (si es necesario, ej. cliente HTTP)
│   │   └── main.py             # Punto de entrada de la aplicación PyQt5
│   └── shared/                 # Código o tipos compartidos entre el backend y la UI (si aplica)
│       ├── __init__.py
│       └── data_types.py       # Ej. Definiciones Pydantic comunes si la UI las consume
├── tests/                      # Pruebas automatizadas
│   ├── backend/                # Pruebas para el backend
│   │   ├── unit/               # Pruebas unitarias (reflejando la estructura de ultibot_backend/)
│   │   └── integration/        # Pruebas de integración
│   ├── ui/                     # Pruebas para la UI de PyQt5
│   │   └── unit/
│   └── e2e/                    # Pruebas End-to-End (si aplican para el flujo completo)
├── .env.example                # Ejemplo de variables de entorno requeridas
├── .gitignore                  # Archivos y directorios a ignorar por Git
├── Dockerfile                  # Para construir la imagen Docker del backend (y potencialmente la UI si se empaqueta junta)
├── pyproject.toml              # Definición del proyecto y dependencias para Poetry
└── README.md                   # Visión general del proyecto, instrucciones de configuración y ejecución

### External APIs Consumed

#### Binance API

- **Purpose:** La API de Binance se utiliza para obtener datos de mercado en tiempo real e históricos, ejecutar órdenes de trading (spot), gestionar órdenes, y consultar balances de cuenta y permisos de la API key. Es la plataforma de exchange principal para las operaciones de UltiBotInversiones.

- **Base URL(s):**
  - Production (REST): `https://api.binance.com`
  - Production (WebSockets): `wss://stream.binance.com:9443/ws` o `wss://stream.binance.com:443/ws`
  - _Nota: Se utilizarán URLs específicas para Testnet si se implementa una fase de pruebas en dicho entorno._

- **Authentication:**
  - REST API: Se utiliza `API-Key` (variable de entorno `BINANCE_API_KEY`) en el header `X-MBX-APIKEY` y `HMAC SHA256 signature` de los parámetros de la solicitud (utilizando `API-Secret`, variable de entorno `BINANCE_API_SECRET`). Algunas llamadas (ej. datos de mercado públicos) no requieren autenticación.
  - WebSockets: Generalmente no requieren autenticación para streams de datos públicos. Para streams de datos de usuario (ej. actualizaciones de cuenta/órdenes), se requiere un `listenKey` obtenido a través de un endpoint REST autenticado (`POST /api/v3/userDataStream`).

- **Key Endpoints Used (REST API):**
  - **`GET /api/v3/account`**:
    - Description: Obtiene información de la cuenta, incluyendo balances y permisos de la API key.
    - Request Parameters: `timestamp` (Query), `signature` (Query).
    - Success Response Schema (Code: `200 OK`): Incluye `makerCommission`, `takerCommission`, `balances` (array de `{ asset, free, locked }`), `canTrade`, `canWithdraw`, `canDeposit`, etc.
  - **`POST /api/v3/order`**:
    - Description: Envía una nueva orden de trading (LIMIT, MARKET, STOP\_LOSS\_LIMIT, TAKE\_PROFIT\_LIMIT).
    - Request Body Schema: Incluye `symbol`, `side` (BUY/SELL), `type` (LIMIT, MARKET, etc.), `timeInForce` (GTC, IOC, FOK), `quantity`, `price` (para LIMIT), `stopPrice` (para STOP\_LOSS\_LIMIT), `quoteOrderQty` (para MARKET por cantidad de cotización), etc.
  - **`GET /api/v3/order`**:
    - Description: Consulta el estado de una orden específica.
    - Request Parameters: `symbol`, `orderId` o `origClientOrderId`, `timestamp`, `signature`.
  - **`DELETE /api/v3/order`**:
    - Description: Cancela una orden activa.
    - Request Parameters: `symbol`, `orderId` o `origClientOrderId`, `timestamp`, `signature`.
  - **`GET /api/v3/klines`**:
    - Description: Obtiene datos de velas/klines para un símbolo en un intervalo específico. Útil para gráficos e histórico.
    - Request Parameters: `symbol`, `interval`, `startTime`, `endTime`, `limit`.
  - **`GET /api/v3/ticker/24hr`**:
    - Description: Obtiene estadísticas de ticker de las últimas 24 horas para un símbolo o todos los símbolos. Puede usarse para cambio 24h, volumen 24h si no se obtiene por WebSocket.
    - Request Parameters: `symbol` (opcional).
  - **`POST /api/v3/userDataStream`**:
    - Description: Inicia un stream de datos de usuario y devuelve un `listenKey`.
  - **`PUT /api/v3/userDataStream`**:
    - Description: Mantiene vivo un `listenKey` (keep-alive).
  - **`DELETE /api/v3/userDataStream`**:
    - Description: Cierra un `listenKey`.

- **Key WebSocket Streams Used:**

  - **Kline/Candlestick Streams:** `<symbol>@kline_<interval>` (ej. `btcusdt@kline_1m`)
    - Description: Emite datos de velas en tiempo real.
    - Payload Schema: Incluye tiempo de apertura/cierre de la vela, precios OHLC, volumen, etc.
  - **Individual Symbol Ticker Streams:** `<symbol>@ticker` (ej. `btcusdt@ticker`)
    - Description: Emite estadísticas de ticker de 24h en tiempo real para un símbolo.
  - **All Market Mini Tickers Stream:** `!miniTicker@arr` (o `!miniTicker@arr@1000ms`)
    - Description: Emite un array de tickers simplificados para todos los símbolos cada segundo. Útil para una visión general del mercado.
  - **Depth Chart Stream (Order Book):** `<symbol>@depth<levels>` o `<symbol>@depth<levels>@<speed>` (ej. `btcusdt@depth20@100ms`)
    - Description: Emite actualizaciones del libro de órdenes.
  - **User Data Streams:** (Requiere `listenKey`)
    - Description: Emite actualizaciones sobre el estado de la cuenta, ejecución de órdenes, y cambios en balances.

- **Rate Limits:** Se deben consultar los límites de la API de Binance (por IP, por UID) y gestionarlos adecuadamente (ej. con reintentos 
controlados, priorización de llamadas). Se especifican en [https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#api-clusters](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#api-clusters) y [https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md#general-wss-information](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md#general-wss-information).

- **Link to Official Docs:** [https://binance-docs.github.io/apidocs/spot/en/](https://binance-docs.github.io/apidocs/spot/en/)


#### Telegram Bot API

- **Purpose:** Se utiliza para enviar notificaciones y alertas importantes al usuario directamente en su cuenta de Telegram. Esto incluye confirmaciones de operaciones, alertas de trading generadas por el sistema o por la IA, errores críticos, y otras actualizaciones relevantes sobre la actividad de "UltiBotInversiones".
- **Base URL(s):**
  - Production: `https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/` (donde `<TELEGRAM_BOT_TOKEN>` es el token del bot proporcionado por el usuario y gestionado como variable de entorno).
- **Authentication:**
  - Se realiza a través del `TELEGRAM_BOT_TOKEN` incluido en la URL de la solicitud. Las credenciales (token y chat ID) son proporcionadas por el usuario.
- **Key Endpoints Used:**
  - **`POST /sendMessage`**:
    - Description: Envía un mensaje de texto a un chat específico. Se utilizará para todas las notificaciones principales.
    - Request Body Schema:
      ```json
      {
        "chat_id": "string", // TELEGRAM_CHAT_ID proporcionado por el usuario
        "text": "string", // Contenido del mensaje, formateado con MarkdownV2
        "parse_mode": "MarkdownV2", // Para habilitar formato Markdown
        "reply_markup": { // Opcional, para botones interactivos
          "inline_keyboard": [
            [
              { "text": "string", "callback_data": "string" }
            ]
          ]
        }
      }
      ```
    - Success Response Schema (Code: `200 OK`): Incluye `ok: true` y un objeto `result` con detalles del mensaje enviado.
  - **`POST /answerCallbackQuery`** (si se implementan botones interactivos):
    - Description: Se utiliza para enviar una respuesta a una `callback_query` generada cuando el usuario presiona un botón de un `inline_keyboard`.
    - Request Body Schema:
      ```json
      {
        "callback_query_id": "string", // ID de la callback_query recibida
        "text": "string", // Texto a mostrar al usuario (ej. una notificación emergente) (opcional)
        "show_alert": "boolean" // Si el texto debe mostrarse como una alerta (opcional)
      }
      ```
    - Success Response Schema (Code: `200 OK`): Incluye `ok: true` y `result: true`.

- **Rate Limits:** Se deben respetar los límites de la API de Telegram para evitar el bloqueo del bot (consultar la documentación oficial para detalles específicos sobre la cantidad de mensajes por segundo/minuto a un mismo chat o globalmente).

- **Link to Official Docs:** [https://core.telegram.org/bots/api](https://core.telegram.org/bots/api)


#### Mobula API

- **Purpose:** Se utiliza para la verificación y obtención de datos clave sobre criptoactivos, como metadatos, precios de mercado, capitalización, volumen, direcciones de contrato en diferentes blockchains, y datos históricos. Es especialmente útil para complementar la información de Binance o para obtener datos de activos que podrían no estar listados en Binance.
- **Base URL(s):**
  - Production: `https://api.mobula.io/api/1`
- **Authentication:**
  - Se realiza mediante una API Key (variable de entorno `MOBULA_API_KEY`) enviada en el header `Authorization`. Ejemplo: `Authorization: <MOBULA_API_KEY>`.
- **Key Endpoints Used:**
  - **`GET /search`**:
    - Description: Busca activos por nombre o símbolo.
    - Request Parameters: `query` (string, nombre o símbolo del activo).
    - Success Response Schema (Code: `200 OK`): Un array de objetos de activos que coinciden con la búsqueda, conteniendo información básica como `id`, `name`, `symbol`, `logo`, `contracts` (direcciones de contrato).
  - **`GET /market/data`**:
    - Description: Obtiene datos de mercado detallados (precio, market cap, volumen, supply, etc.) y metadatos (nombre, símbolo, direcciones de contrato, enlaces a redes sociales, sitio web) para un activo específico.
    - Request Parameters: `asset` (string, nombre, símbolo o dirección de contrato del activo), `blockchain` (string, opcional, nombre de la blockchain).
    - Success Response Schema (Code: `200 OK`): Un objeto `data` que contiene la información detallada del activo. Ejemplo conceptual proporcionado por el usuario:
      ```json
      {
        "data": {
          "name": "Ethereum",
          "symbol": "ETH",
          "price": 3800.00,
          "market_cap": "...",
          "contracts": [
            { "blockchain": "Ethereum", "address": "0x..." }
          ]
          // ... más campos
        }
      }
      ```
     
  - **`GET /market/history`**:
    - Description: Obtiene el historial de precios (y opcionalmente market cap y volumen) para un activo.
    - Request Parameters: `asset` (string, nombre, símbolo o dirección de contrato), `blockchain` (string, opcional), `from` (timestamp, opcional), `to` (timestamp, opcional), `max_results` (number, opcional).
    - Success Response Schema (Code: `200 OK`): Un objeto `data` que contiene un array `price_history` con tuplas de `[timestamp, price]`, y opcionalmente `market_cap_history` y `volume_history`.
- **Rate Limits:** Se deben consultar los límites de la API de Mobula en su documentación oficial y asegurar un manejo adecuado para no excederlos.
- **Link to Official Docs:** [https://docs.mobula.io/](https://docs.mobula.io/)


#### Google Gemini API (via `google-generativeai` library and LangChain)

- **Purpose:** El modelo Gemini de Google (específicamente se considera Gemini 1.5 Pro o Flash) se utilizará como el motor de inteligencia artificial principal para "UltiBotInversiones". Sus funciones incluyen el análisis avanzado de oportunidades de trading, la evaluación de confianza de señales, la interpretación de datos de mercado complejos, la toma de decisiones basada en estrategias predefinidas y la interacción dinámica con "Herramientas" (wrappers para APIs de Servidores MCP, Mobula, Binance, etc.) a través de la orquestación con LangChain (Python).
- **Base URL(s):**
  - No aplica directamente, ya que la interacción se realizará a través de la biblioteca cliente `google-generativeai` de Python, la cual maneja las URLs de los endpoints de la API de Google internamente.
- **Authentication:**
  - Se realiza mediante una API Key de Google (variable de entorno `GEMINI_API_KEY`, con el valor `AIzaSyAv6VA8VBLwWwVY5Q_hsj2iQITyJ_CvBDs` proporcionado por el usuario). Esta clave se configurará en el entorno de la aplicación para que la biblioteca `google-generativeai` pueda utilizarla.
- **Key Interaction Patterns (via `google-generativeai` and LangChain):**
  - **Generación de Contenido (Análisis y Razonamiento):**
    - Description: Se enviarán prompts complejos al modelo Gemini (Pro o Flash) para obtener análisis, evaluaciones de riesgo/confianza, sugerencias de trading, o para que el modelo razone sobre qué información adicional necesita.
    - Library Usage: Se utilizarán funciones de la biblioteca `google-generativeai` (ej. `GenerativeModel.generate_content_async`) o abstracciones de LangChain (ej. `ChatGoogleGenerativeAI`, Agentes de LangChain).
    - Request (Prompt) Structure: Los prompts serán elaborados y podrán incluir contexto del mercado, datos de activos, criterios del usuario, y, crucialmente (vía LangChain), una lista de "Herramientas" disponibles que Gemini puede decidir utilizar.
    - Response Structure: Las respuestas del modelo pueden ser texto natural, JSON estructurado (si se solicita explícitamente en el prompt), o una secuencia de "pensamientos" y "acciones" (si se usa un Agente de LangChain) indicando qué herramienta usar y con qué parámetros.
  - **Uso de Herramientas (Tool Use) con LangChain:**
    - Description: El `AI_Orchestrator` definirá herramientas (ej. para consultar un MCP, obtener datos de Mobula, verificar balances en Binance). LangChain permitirá a Gemini solicitar el uso de estas herramientas. El `AI_Orchestrator` ejecutará la herramienta solicitada y devolverá el resultado a Gemini para que continúe su proceso de razonamiento.
    - Library Usage: Se utilizarán las capacidades de definición de herramientas y ejecución de agentes de LangChain.
- **Interacción Asíncrona:** Todas las interacciones con Gemini, especialmente aquellas que involucren cadenas de razonamiento o uso de herramientas, se realizarán de forma asíncrona para no bloquear el sistema.
- **Rate Limits:** Se deben considerar los límites de la API de Google Gemini (consultar la documentación oficial para Requests Per Minute - RPM, Tokens Per Minute - TPM) y asegurar un manejo adecuado, incluyendo reintentos con backoff exponencial si es necesario.
- **Link to Official Docs:**
  - Google AI for Developers (Gemini API): [https://ai.google.dev/docs](https://ai.google.dev/docs)
  - LangChain (Python) Documentation: [https://python.langchain.com/](https://python.langchain.com/)
  - `google-generativeai` (Python library): [https://pypi.org/project/google-generativeai/](https://pypi.org/project/google-generativeai/)


#### Servidores MCP Externos (Model Context Protocol)

- **Purpose:** Los Servidores MCP son servicios o bibliotecas externas que exponen funcionalidades específicas o datos contextuales que pueden ser utilizados por modelos de IA como Gemini. En "UltiBotInversiones", se integrarán como "Herramientas" para LangChain, permitiendo al `AI_Orchestrator` solicitar información específica o análisis de estos servidores para enriquecer su proceso de toma de decisiones. Los usos pueden incluir la obtención de datos de múltiples exchanges, datos on-chain, análisis de sentimiento específicos, o métricas de proyectos web3.
- **Base URL(s) / Interaction Method:**
  - Variable según el MCP específico. Algunos pueden exponer APIs REST/HTTP (requiriendo una URL base y endpoints), mientras que otros podrían ser bibliotecas Python que se ejecutan localmente o en un entorno controlado y se invocan directamente.
  - Para la v1.0, nos enfocaremos en integrar 1 o 2 MCPs como Prueba de Concepto (PoC). Los candidatos iniciales son:
    - **`doggybee/mcp-server-ccxt`**:
        - _Presumed Interaction:_ Probablemente una API REST (JSON) o una biblioteca Python que utiliza CCXT para interactuar con múltiples exchanges. Proporcionaría datos de precios, order books, y potencialmente ejecución de órdenes en exchanges no cubiertos directamente por nuestra integración principal con Binance.
        - _GitHub:_ [https://github.com/doggybee/mcp-server-ccxt](https://github.com/doggybee/mcp-server-ccxt)
    - **`aaronjmars/web3-research-mcp`**:
        - _Presumed Interaction:_ Probablemente una API REST o una biblioteca Python para obtener datos on-chain, información de tokens, o análisis de proyectos web3.
        - _GitHub:_ [https://github.com/aaronjmars/web3-research-mcp](https://github.com/aaronjmars/web3-research-mcp)
  - La arquitectura debe incluir "adaptadores de herramientas" específicos para cada MCP integrado, que traducirán las solicitudes del agente LangChain en llamadas concretas al MCP correspondiente y formatearán la respuesta para el agente.
- **Authentication:**
  - Variable según el MCP. Algunos pueden ser públicos, otros pueden requerir claves API o tokens de autenticación. El `CredentialManager` almacenará las credenciales necesarias para los MCPs que las requieran.
- **Key Endpoints Used / Functions Called:**
  - Esto será específico para cada MCP integrado. Por ejemplo, un MCP basado en CCXT podría tener funciones/endpoints para:
    - `get_ticker(exchange_id, symbol)`
    - `get_order_book(exchange_id, symbol)`
    - `get_balance(exchange_id)`
  - Un MCP de investigación web3 podría tener funciones/endpoints como:
    - `get_token_info(contract_address, blockchain)`
    - `get_onchain_transactions(wallet_address, blockchain)`
  - Estos se definirán en detalle al implementar el adaptador de herramienta LangChain para cada MCP.
- **Rate Limits:** Específicos para cada MCP. Deberán investigarse y gestionarse en los adaptadores de herramientas correspondientes.
- **Link to General MCP Resources:**
  - Lista de Servidores MCP: [https://github.com/punkpeye/awesome-mcp-servers#finance--fintech](https://github.com/punkpeye/awesome-mcp-servers#finance--fintech)
  - Otros MCPs mencionados para investigación: `ariadng/metatrader-mcp-server`, `armorwallet/armor-crypto-mcp`, `ferdousbhai/investor-agent`.

### Internal APIs Provided (If Applicable)

El backend de "UltiBotInversiones", desarrollado con FastAPI, expondrá una API REST interna para ser consumida principalmente por la interfaz de usuario de escritorio (PyQt5). Esta API permitirá a la UI interactuar con la lógica de negocio, acceder a datos y gestionar las operaciones del sistema.

#### API Interna Principal (FastAPI)

- **Purpose:** Servir como la interfaz de comunicación entre la UI de PyQt5 y los servicios del backend, permitiendo a la UI solicitar acciones, obtener datos y recibir actualizaciones de estado.
- **Base URL:**
  - Local: `http://localhost:8000/api/v1/` (El puerto `8000` es el estándar de FastAPI, pero será configurable).
- **Authentication/Security:**
  - Para la v1.0, dado que tanto la UI como el backend se ejecutarán en la máquina local del usuario para esta aplicación personal, la API se enlazará exclusivamente a `localhost`. Esto limita la accesibilidad desde fuera de la máquina local.
  - No se implementará un esquema de autenticación complejo entre la UI y esta API local inicialmente, asumiendo un entorno de ejecución local confiable. La seguridad principal se centrará en la protección de las claves API externas mediante el `CredentialManager` y en asegurar la comunicación con las APIs externas (ej. Binance).
  - Si en futuras versiones se considera acceso remoto o multiusuario, se deberá implementar un mecanismo de autenticación robusto (ej. tokens JWT).

- **Formato de Datos:** JSON.

- **Principales Grupos de Recursos/Endpoints (Conceptuales):**
    A continuación, se listan los grupos de recursos que la API interna probablemente expondrá. Los endpoints específicos dentro de cada grupo se definirán en detalle durante el desarrollo de las historias de usuario correspondientes.

    * **`/auth/`**:
        * Description: (Potencial, si se necesita un handshake inicial o gestión de sesión muy ligera entre UI y backend local, aunque para v1.0 podría no ser estrictamente necesario si solo está en localhost).
    * **`/config/`**:
        * Description: Gestiona la configuración de la aplicación y las preferencias del usuario.
        * Consumers: `ConfigManager`.
        * Example Endpoints: `GET /config/`, `POST /config/`, `GET /config/scan-presets`, `POST /config/scan-presets` (para guardar y cargar los "sistemas de búsqueda" que mencionaste).
    * **`/credentials/`**:
        * Description: Permite a la UI gestionar (añadir, actualizar, verificar estado) las claves API para servicios externos de forma segura.
        * Consumers: `CredentialManager`.
        * Example Endpoints: `GET /credentials/status`, `POST /credentials/binance`, `POST /credentials/telegram`, etc.
    * **`/market/`**:
        * Description: Provee acceso a datos de mercado procesados o listas de activos. (La UI también podría obtener datos en tiempo real directamente vía WebSockets si la arquitectura lo permite para ciertos streams, pero esta API podría servir datos agregados o para configuración de visualizaciones).
        * Consumers: `MarketDataMgr`.
        * Example Endpoints: `GET /market/available-pairs`, `GET /market/historical-data?pair=BTCUSDT&interval=1h`.
    * **`/portfolio/`**:
        * Description: Expone información sobre el estado del portafolio del usuario (simulado y real), incluyendo balances, P&L, y activos poseídos.
        * Consumers: `PortfolioManager`.
        * Example Endpoints: `GET /portfolio/summary`, `GET /portfolio/paper/balance`, `GET /portfolio/real/balance`.
    * **`/strategies/`**:
        * Description: Permite a la UI listar, configurar (parámetros), activar/desactivar las estrategias de trading.
        * Consumers: `StrategyManager`.
        * Example Endpoints: `GET /strategies/`, `GET /strategies/{strategy_id}/config`, `POST /strategies/{strategy_id}/config`, `POST /strategies/{strategy_id}/activate`.
    * **`/trading/`**:
        * Description: Permite a la UI interactuar con el motor de trading, como iniciar/detener el motor, obtener su estado, y para la operativa real limitada, presentar oportunidades de alta confianza para confirmación.
        * Consumers: `TradingEngine`, `AI_Orchestrator`.
        * Example Endpoints: `GET /trading/status`, `POST /trading/paper/execute-trade` (si se permite entrada manual en paper), `POST /trading/real/confirm-opportunity/{opportunity_id}`.
    * **`/orders/`**:
        * Description: Provee información sobre el historial de órdenes y el estado de las órdenes activas (simuladas y reales).
        * Consumers: `OrderExecutor` (o a través del `TradingEngine`/`PortfolioManager`).
        * Example Endpoints: `GET /orders/history`, `GET /orders/active`.
    * **`/notifications/`**:
        * Description: Permite a la UI obtener un historial de notificaciones internas del sistema o marcarlas.
        * Consumers: `NotificationService`.
        * Example Endpoints: `GET /notifications/history`, `POST /notifications/{notification_id}/mark-as-read`.
    * **`/analysis/` o `/ai/`**:
        * Description: Permite a la UI solicitar análisis específicos al `AI_Orchestrator` o recuperar resultados de análisis asíncronos.
        * Consumers: `AI_Orchestrator`.
        * Example Endpoints: `POST /analysis/request`, `GET /analysis/results/{request_id}`.

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


## Core Workflow / Sequence Diagrams

    sequenceDiagram
        participant User as Usuario (via UI)
        participant UI as Interfaz de Usuario (PyQt5)
        participant MCPs as Servidores MCP Externos
        participant TradingEngine as Motor de Trading
        participant ConfigManager as Gestor de Configuración
        participant DataPersistenceService as Servicio de Persistencia (Supabase)
        participant AI_Orchestrator as Orquestador IA (LangChain + Gemini)
        participant CredentialManager as Gestor de Credenciales
        participant BinanceAPI as API de Binance
        participant MobulaAPI as API de Mobula (Ej. Herramienta IA)
        participant NotificationService as Servicio de Notificaciones
        participant TelegramAPI as API de Telegram
    
        Note over MCPs, TradingEngine: Fase 1: Detección y Registro de Oportunidad
        MCPs->>TradingEngine: Notifica nueva oportunidad (ej. vía webhook)
        TradingEngine->>DataPersistenceService: Crea registro de Oportunidad (O_ID, datos_iniciales, estado: nueva)
        DataPersistenceService-->>TradingEngine: Oportunidad Creada (O_ID)
        TradingEngine->>AI_Orchestrator: Solicita análisis (O_ID)
    
        Note over AI_Orchestrator, DataPersistenceService, GeminiAPI, BinanceAPI, MobulaAPI: Fase 2: Análisis y Enriquecimiento por IA
        AI_Orchestrator->>DataPersistenceService: Obtiene datos de Oportunidad (O_ID)
        DataPersistenceService-->>AI_Orchestrator: Datos de Oportunidad
        AI_Orchestrator->>AI_Orchestrator: Prepara prompt inicial con datos y herramientas disponibles
    
        loop Ciclo de Invocación de Herramientas (LangChain)
            AI_Orchestrator->>GeminiAPI: Envía prompt/solicitud de siguiente paso
            GeminiAPI-->>AI_Orchestrator: Decide (ej: usar Herramienta_Binance_MarketData)
            alt Usar Herramienta Binance
                AI_Orchestrator->>CredentialManager: Solicita credenciales para herramienta Binance (si aplica y no cacheadas)
                CredentialManager-->>AI_Orchestrator: Credenciales
                AI_Orchestrator->>BinanceAPI: Obtiene datos de mercado adicionales
                BinanceAPI-->>AI_Orchestrator: Datos de mercado
                AI_Orchestrator->>GeminiAPI: Devuelve resultado de Herramienta_Binance
            else Usar Herramienta Mobula (ejemplo)
                AI_Orchestrator->>CredentialManager: Solicita credenciales para herramienta Mobula
                CredentialManager-->>AI_Orchestrator: Credenciales
                AI_Orchestrator->>MobulaAPI: Verifica/enriquece datos del activo
                MobulaAPI-->>AI_Orchestrator: Datos del activo
                AI_Orchestrator->>GeminiAPI: Devuelve resultado de Herramienta_Mobula
            else Otras Herramientas o Análisis Final
                GeminiAPI-->>AI_Orchestrator: Resultado final del análisis (confianza, parámetros, lógica)
            end
        end
        AI_Orchestrator->>DataPersistenceService: Actualiza Oportunidad (O_ID, análisis_IA, estado: analizada)
        DataPersistenceService-->>AI_Orchestrator: Confirmación de actualización
        AI_Orchestrator-->>TradingEngine: Devuelve resumen del análisis (O_ID, confianza, parámetros)
    
        Note over TradingEngine, ConfigManager, UI, User: Fase 3: Presentación y Confirmación (si es necesaria)
        TradingEngine->>DataPersistenceService: Obtiene Oportunidad analizada (O_ID)
        DataPersistenceService-->>TradingEngine: Datos completos de Oportunidad
        TradingEngine->>ConfigManager: Consulta configuración de usuario (ej. umbral realTrading, confirmación manual)
        ConfigManager-->>TradingEngine: Preferencias del usuario
        alt Requiere Confirmación del Usuario y Alta Confianza
            TradingEngine->>UI: Presenta oportunidad de alta confianza al usuario (O_ID, detalles)
            UI->>User: Muestra detalles y solicita confirmación para operación real
            User->>UI: Confirma ejecución de la operación (O_ID)
            UI->>TradingEngine: Envía confirmación del usuario para ejecutar (O_ID)
        else Decisión Automatizada (No mostrado en este flujo de "orden real con confirmación")
            TradingEngine->>TradingEngine: Procede basado en reglas (ej. paper trading o real si configurado)
        end
    
        Note over TradingEngine, CredentialManager, BinanceAPI, DataPersistenceService: Fase 4: Ejecución de Orden Real
        TradingEngine->>CredentialManager: Solicita credenciales de Binance (API Key Real)
        CredentialManager-->>TradingEngine: Credenciales de Binance
        TradingEngine->>BinanceAPI: Coloca orden de compra/venta (parámetros de O_ID, credenciales)
        BinanceAPI-->>TradingEngine: Respuesta de la orden (ID_Orden_Exchange, estado_orden)
        TradingEngine->>DataPersistenceService: Crea registro de Trade (basado en O_ID, ID_Orden_Exchange, detalles)
        DataPersistenceService-->>TradingEngine: Trade Creado
        TradingEngine->>DataPersistenceService: Actualiza Oportunidad (O_ID, estado: convertida_a_trade_real, Trade_ID)
        DataPersistenceService-->>TradingEngine: Confirmación
        TradingEngine->>TradingEngine: Llama a PortfolioManager para actualizar estado (no detallado aquí)
    
        Note over TradingEngine, NotificationService, UI, TelegramAPI: Fase 5: Gestión Post-Ejecución y Notificación
        TradingEngine->>NotificationService: Notifica ejecución de la operación (detalles del Trade)
        NotificationService->>DataPersistenceService: Guarda Notificación (opcional, para historial)
        DataPersistenceService-->>NotificationService: Confirmación
        NotificationService->>UI: Envía notificación a la UI (si está activa)
        NotificationService->>TelegramAPI: Envía notificación a Telegram (si configurado)
        TelegramAPI-->>NotificationService: Confirmación de envío (opcional)
        UI->>User: Muestra notificación

## Definitive Tech Stack Selections

¡Entendido, Carlos! Comprendo perfectamente la directiva: agilidad, estabilidad y potencia para poner "UltiBotInversiones" en marcha lo antes posible, manteniendo la simplicidad en esta v1.0, especialmente siendo una aplicación de uso personal y local.

Con ese enfoque, tomaré la iniciativa de responder las preguntas pendientes sobre el stack tecnológico, buscando el equilibrio entre robustez y mínima complejidad para esta fase.

**Integración de tus Adiciones y Respuestas a las Preguntas Pendientes:**

1.  **Herramientas de Calidad de Código (`Black`, `Ruff`, `pytest`):**
    * `pytest` es fundamental como framework de pruebas y debe estar en el stack.
    * `Black` (formateador) y `Ruff` (linter extremadamente rápido que puede reemplazar a `Flake8` y otros) son herramientas de desarrollo esenciales para mantener la calidad y consistencia del código. Las detallaremos más en la sección "Coding Standards", pero podemos listarlas aquí como herramientas de desarrollo.
    * Añadiré `pytest-asyncio` ya que trabajaremos con código asíncrono (FastAPI, `httpx`).

2.  **Manejo de Migraciones de Base de Datos (Supabase):**
    * Dado que Supabase facilita esto, actualizaré la descripción de PostgreSQL para reflejar que las migraciones se manejarán principalmente a través de las herramientas que provee Supabase (su CLI y/o interfaz de usuario). Esto evita añadir una dependencia como Alembic si no es estrictamente necesaria para la v1.0.

3.  **Cloud Platform:**
    * Para la v1.0, y enfocándonos en una aplicación local, nuestra dependencia principal es Supabase para el BaaS/DBaaS. No introduciremos una plataforma cloud adicional (AWS, Azure, GCP) para otros servicios, para mantener la simplicidad.

4.  **Cloud Services:**
    * Consecuentemente, no se prevén servicios cloud específicos más allá de los inherentes a Supabase.

5.  **Infrastructure as Code (IaC):**
    * Para una aplicación de escritorio/local v1.0, IaC (Terraform, CDK, etc.) no es necesario y añadiría complejidad.

6.  **CI/CD:**
    * Un pipeline formal de CI/CD es más de lo que necesitamos para la v1.0 de una aplicación local. Las pruebas y builds se ejecutarán localmente. Se podrían usar scripts de Poetry/make/shell para automatizar tareas comunes.

Aquí está la tabla **"Definitive Tech Stack Selections"** actualizada con estas consideraciones. 

| Categoría     | Tecnología | Versión / Detalles | Descripción / Propósito | Justificación (Opcional) |
| :------------ | :--------- | :----------------- | :---------------------- | :----------------------- |
| **Lenguajes** | Python | `3.11.9` | Lenguaje principal para el backend, lógica del bot, scripts y orquestación de IA. | Versatilidad, ecosistema robusto para IA y web, rendimiento mejorado en versiones 3.11+. Versión específica para consistencia.|
| **Runtime** | Python Interpreter | `Corresponde a Python 3.11.9` | Entorno de ejecución para el código Python. |
| | SQL | `Estándar SQL implementado por PostgreSQL 15` | Lenguaje para consultas y gestión de la base de datos relacional. | Estándar para bases de datos relacionales; PostgreSQL ofrece un dialecto SQL rico y eficiente. |
| **Frameworks** | FastAPI | `0.111.0` | Framework de alto rendimiento para construir las APIs del backend. | Moderno, rápido (comparable a NodeJS y Go), basado en type hints de Python, auto-documentación OpenAPI, asíncrono nativo. |
| | PyQt5 | `5.15.11 (Vinculado a Qt 5.15.x LTS)` | Framework para la Interfaz de Usuario (UI) de escritorio. | Requisito del proyecto; bindings maduros y completos de Qt para Python, amplio conjunto de widgets. |
| | LangChain (Python) | `Core: 0.2.5` | Orquestación de interacciones con Modelos de Lenguaje (LLM) y construcción de apl. basadas en IA. | Facilita el patrón Agente-Herramientas con Gemini, gestión de prompts, cadenas de LLMs, e integraciones. |
| **Bases de Datos** | PostgreSQL (via Supabase) | `15.6 o sup. (Gestionada por Supabase)` | Almacén de datos relacional principal. Migraciones gestionadas vía Supabase CLI/UI. | Robustez, escalabilidad. Supabase facilita gestión, auth y APIs en tiempo real. |
| | Redis | `7.2.5` | Caché L2, colas de tareas (potencial), almacenamiento de sesión (potencial). | Alta velocidad, estructuras de datos versátiles, ideal para reducir latencia. |
| **Proveedor IA** | Google Gemini (via API) | `Modelos: Gemini 1.5 Pro/Flash (seleccionables)` | Motor principal de Inteligencia Artificial. | Capacidades avanzadas de razonamiento multimodal, ventana de contexto grande, integración con herramientas. |
| **Bibliotecas Clave** | `google-generativeai` | `0.5.4` | Cliente Python oficial para la API de Google Gemini. | Interacción directa y eficiente con los modelos Gemini. |
| | `langchain-core` | `0.2.5` | Núcleo de LangChain. | Base para el ecosistema LangChain. |
| | `langchain-google-genai` | `0.1.7 (o compatible con LC Core 0.2.x)` | Integración LangChain para modelos Gemini. | Permite usar Gemini fluidamente dentro de LangChain. |
| | `langchain-community` | `0.2.5 (o compatible con LC Core 0.2.x)` | Componentes comunitarios de LangChain. | Amplía capacidades de LangChain con diversas herramientas. |
| | `pydantic` | `2.7.1 (Compatible con FastAPI 0.111.0)` | Validación de datos y gestión de configuraciones. | Usado por FastAPI para validación y modelos de datos; robusto. |
| | `supabase-py` | `2.5.0` | Cliente Python para API de Supabase (PostgreSQL). | Facilita la comunicación con la BD gestionada por Supabase. |
| | `httpx` | `0.27.0` | Cliente HTTP asíncrono para APIs externas (Binance, MCPs, Mobula). | Comunicación eficiente y no bloqueante, esencial para baja latencia. |
| | `websockets` | `12.0` | Biblioteca para conexiones WebSocket (ej. streams de Binance). | Comunicación en tiempo real bidireccional, crucial para datos de mercado. |
| **Gestión Dependencias**| Poetry | `1.8.3` | Gestión de dependencias, empaquetado y entornos virtuales. | Entornos reproducibles, resolución robusta, `pyproject.toml`. |
| **Containerización** | Docker Engine | `26.1.4 (o más reciente estable)` | Creación, gestión y despliegue de la aplicación en contenedores (opcional para v1.0 local). | Consistencia entre entornos; útil para dependencias complejas como Redis si no se instala nativo. |
| **Servidor ASGI** | Uvicorn | `0.29.0 (o compatible con FastAPI)` | Servidor ASGI para ejecutar FastAPI. | Alto rendimiento para FastAPI; se puede usar con Gunicorn en producción (pero para v1.0 local, Uvicorn solo es suficiente). |
| **Testing** | `pytest` | `(Versión específica compatible?)` | Framework principal para pruebas unitarias y de integración. | Popular, flexible y con amplio ecosistema de plugins en Python. |
| | `pytest-asyncio` | `(Versión específica compatible?)` | Plugin de Pytest para soportar pruebas de código asíncrono. | Necesario para probar endpoints y lógica de FastAPI/httpx. |
| **Herramientas de Desarrollo y Calidad** | `Ruff` | `(Versión específica?)` | Linter y formateador de Python extremadamente rápido. | Eficiencia y consistencia en el formato y calidad del código. Puede reemplazar Black, Flake8, isort. |
| | `Black` (Opcional si se usa Ruff para formateo) | `(Versión específica?)` | Formateador de código Python. | Consistencia en el formato del código (puede ser redundante si Ruff se usa para formateo). |
| **Cloud Platform** | N/A | N/A | Principalmente Supabase para DBaaS; no se prevé otra plataforma cloud principal para v1.0. | Simplificación para v1.0 de aplicación local. |
| **Cloud Services** | N/A | N/A | No se utilizan servicios cloud adicionales más allá de Supabase para v1.0. | Simplificación para v1.0. |
| **Infrastructure as Code (IaC)** | N/A | N/A | No aplica para v1.0 (aplicación de escritorio/local). | Simplificación para v1.0. |
| **CI/CD** | N/A | N/A | Pruebas y builds ejecutados localmente para v1.0. Scripts locales para automatización. | Simplificación para v1.0. |


##  Infrastructure and Deployment Overview

Dada la naturaleza de "UltiBotInversiones" como una aplicación de escritorio/local para uso personal en su v1.0, la infraestructura y el despliegue se simplifican significativamente:

-   **Cloud Provider(s):**
    -   El proveedor principal de servicios en la nube es **Supabase** para la funcionalidad de Base de Datos como Servicio (DBaaS) con PostgreSQL, autenticación y APIs de datos si se utilizan.
    -   No se prevé el uso de otras plataformas cloud (AWS, Azure, GCP) para componentes de backend o infraestructura central en la v1.0.
-   **Core Services Used:**
    -   Los servicios principales son los proporcionados por **Supabase** (PostgreSQL, Auth, APIs).
    -   **Redis** (listado en el stack) se ejecutará localmente (ej. vía Docker o instalación nativa) o se podría considerar una instancia gestionada simple si fuera estrictamente necesario y Supabase no ofreciera una alternativa integrada suficiente para cach L2. Para v1.0, se prioriza la ejecución local de Redis para simplicidad.
-   **Infrastructure as Code (IaC):**
    -   No aplica (N/A) para la v1.0, ya que no se gestionará infraestructura cloud compleja.
-   **Deployment Strategy:**
    -   El "despliegue" consistirá en la ejecución local de la aplicación Python (backend FastAPI y UI PyQt5) desde el código fuente gestionado con Git.
    -   Se utilizará Poetry para gestionar el entorno y las dependencias.
    -   La aplicación se iniciará mediante scripts (ej. `poetry run python src/ultibot_backend/main.py` y `poetry run python src/ultibot_ui/main.py`).
    -   Si se utiliza Docker para servicios como Redis, se gestionará con `docker-compose.yml` localmente.
-   **Environments:**
    -   Principalmente un entorno de **desarrollo local**.
    -   No se definen entornos formales de `staging` o `production` en servidores remotos para la v1.0.
-   **Environment Promotion:**
    -   No aplica (N/A) en el sentido tradicional. Las "promociones" se gestionan a través de commits y ramas en Git.
-   **Rollback Strategy:**
    -   Se basará en el control de versiones con **Git**. Las reversiones a estados anteriores del código se realizarán mediante comandos de Git (ej. `git revert`, `git checkout <commit>`).
    -   Para la base de datos (Supabase), los rollbacks de esquema o datos dependerán de las capacidades de Supabase para backups y restauración, o de migraciones reversibles si se implementan.


## Error Handling Strategy

-   **General Approach:**
    
    -   Utilizaremos excepciones de Python como el mecanismo principal para el manejo de errores en el backend.
    -   FastAPI tiene un buen manejo de excepciones incorporado que convierte excepciones HTTP estándar y personalizadas en respuestas HTTP apropiadas.
    -   Definiremos excepciones personalizadas (`CustomException`) que hereden de `Exception` para errores específicos del dominio de la aplicación, lo que permitirá un manejo más granular.
-   **Logging:**
    
    -   **Library/Method:** Utilizaremos la biblioteca `logging` estándar de Python, configurada para ofrecer la flexibilidad necesaria. Se podría considerar `Loguru` por su simplicidad de configuración si la estándar resulta verbosa para nuestros propósitos iniciales. Para la v1.0, `logging` es suficiente.
    -   **Format:** Los logs se escribirán en formato de **texto plano** para la consola durante el desarrollo local, con un formato claro que incluya: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`. Para un posible futuro archivo de log, se podría considerar JSON, pero para la v1.0 local, texto es más directo.
    -   **Levels:**
        -   `DEBUG`: Información detallada, típicamente de interés solo al diagnosticar problemas.
        -   `INFO`: Confirmación de que las cosas funcionan como se esperaba.
        -   `WARNING`: Una indicación de que algo inesperado sucedió, o una advertencia de posibles problemas futuros (ej. uso de API deprecada).
        -   `ERROR`: Debido a un problema más serio, el software no ha podido realizar alguna función.
        -   `CRITICAL`: Un error serio, que indica que el programa mismo puede ser incapaz de continuar ejecutándose.
    -   **Context:** Además del timestamp, nombre del logger y nivel, se incluirá el nombre del módulo/función donde se origina el log siempre que sea posible. Para errores en el manejo de solicitudes API, se podría incluir un ID de solicitud si se implementa.
-   **Specific Handling Patterns:**
    
    -   **External API Calls (usando `httpx`):**
        -   Se capturarán las excepciones de `httpx` (ej. `httpx.RequestError`, `httpx.HTTPStatusError`).
        -   **Timeouts:** Se configurarán timeouts explícitos (conexión y lectura) en las instancias del cliente `httpx` para evitar bloqueos indefinidos.
        -   **Retries:** Para la v1.0, implementaremos reintentos simples para errores transitorios (ej. problemas de red, errores 5xx) con un número limitado de intentos (ej. 2-3 reintentos) y un backoff fijo o lineal simple. Bibliotecas como `tenacity` podrían considerarse si la lógica de reintentos se vuelve compleja, pero para iniciar, una implementación manual básica será suficiente.
        -   Los errores persistentes de APIs externas se registrarán como `ERROR` y se propagarán como una excepción personalizada apropiada (ej. `BinanceAPIError`, `MCPServiceError`).
    -   **Internal Errors / Business Logic Exceptions:**
        -   Se utilizarán excepciones personalizadas (ej. `InsufficientFundsError`, `InvalidStrategyParametersError`) para señalar problemas en la lógica de negocio.
        -   Estas excepciones serán capturadas por los manejadores de errores de FastAPI o por la lógica de la aplicación para devolver respuestas adecuadas al cliente (UI) y registrar el error con nivel `ERROR` o `WARNING` según la severidad.
    -   **Transaction Management (con Supabase/PostgreSQL):**
        -   Para operaciones que requieran múltiples escrituras en la base de datos y necesiten atomicidad (ej. registrar un trade y actualizar el portafolio), se utilizarán transacciones de base de datos.
        -   El cliente `supabase-py` o la biblioteca subyacente (`psycopg` o similar si se interactúa más directamente) deberá permitir la gestión de `BEGIN`, `COMMIT`, `ROLLBACK`.
        -   En caso de error dentro de una transacción, se realizará un `ROLLBACK` para asegurar la consistencia de los datos, y se registrará el error.


## Coding Standards

En esta sección, estableceremos las reglas y convenciones que todo el código (generado por IA o escrito manualmente) deberá seguir. Esto es vital para mantener la legibilidad, consistencia, calidad y mantenibilidad del proyecto "UltiBotInversiones". El cumplimiento de estos estándares es obligatorio.

1.  **Primary Runtime(s):**
    
    -   Python: `3.11.9` (según nuestro stack tecnológico). Todo el código Python deberá ser compatible con esta versión específica para garantizar la consistencia y evitar problemas de compatibilidad.
2.  **Style Guide & Linter:**
    
    -   **Herramienta Principal:** `Ruff` se utilizará como linter y formateador único y principal.
        -   _Justificación:_ Su velocidad excepcional y la integración de funcionalidades de múltiples herramientas (Flake8, isort, pyupgrade, pydocstyle, e incluso formateo compatible con Black) simplifican el toolchain y aceleran el feedback.
    -   **Configuración de Ruff:**
        -   Se definirá en el archivo `pyproject.toml` bajo la sección `[tool.ruff]`.
        -   _Reglas Habilitadas:_ Se activará un conjunto robusto y explícito de reglas. Como mínimo:
            -   `E, W`: Errores y advertencias de PEP 8 (similares a Pyflakes).
            -   `F`: Errores lógicos (Pyflakes).
            -   `I`: Ordenación de imports (isort).
            -   `UP`: Actualizaciones de sintaxis (pyupgrade).
            -   `D`: Convenciones de Docstrings (pydocstyle) – ver sección "Comments & Documentation".
            -   Considerar `B` (flake8-bugbear) para detectar posibles bugs y malas prácticas de diseño.
            -   Explorar las reglas de `pylint` (`PLC, PLE`) que Ruff está incorporando progresivamente si se desea un análisis más profundo.
        -   _Formateo:_ Se utilizará el formateador integrado de Ruff.
            -   `Line Length:` Se establece en `100` caracteres. Esta decisión debe ser firme para asegurar consistencia.
        -   _Conformidad:_ El código debe adherirse estrictamente a PEP 8, con las configuraciones específicas gestionadas por Ruff.
    -   **Automatización (Mandatorio para v1.0):**
        -   Se configurarán `pre-commit hooks` utilizando la herramienta `pre-commit`.
        -   Los hooks incluirán, como mínimo, `ruff check --fix` y `ruff format`.
        -   Esto asegura que todo el código subido al repositorio cumpla con los estándares automáticamente, crucial cuando la IA genera código.
3.  **Naming Conventions:**
    
    -   Variables y Funciones: `snake_case` (ej. `mi_variable`, `calcular_valor_neto()`).
    -   Métodos de Instancia y Clase: `snake_case` (ej. `obj.hacer_algo()`, `Clase.metodo_de_clase()`).
    -   Clases, Tipos (Pydantic models), y Excepciones: `PascalCase` (ej. `MiClasePrincipal`, `DatosDeConfiguracionUsuario`, `ErrorDeValidacionCustom`).
    -   Constantes: `UPPER_SNAKE_CASE` (ej. `TASA_DE_INTERES_MAXIMA`, `CONFIG_PATH`).
    -   Módulos (archivos `.py`): `snake_case.py` (ej. `gestor_ordenes.py`, `estrategias_scalping.py`).
    -   Paquetes (directorios que contienen `__init__.py`): `snake_case` (ej. `utilidades_core`, `adaptadores_api`).
    -   Atributos/Métodos Internos/Privados:
        -   Un guion bajo (`_nombre_interno`): para uso interno dentro de un módulo o clase. No se considera una API pública.
        -   Doble guion bajo (`__nombre_mangled`): solo si se requiere name mangling explícitamente (raramente necesario). Evitar si no se comprende completamente su propósito.
    -   Funciones Asíncronas: Seguirán `snake_case`. No se requiere un sufijo especial como `_async` a menos que exista una contraparte síncrona con el mismo nombre y sea necesario diferenciarlas claramente.
4.  **File Structure:**
    
    -   Se adherirá estrictamente a la estructura definida en la sección "Project Structure" del `Architecture.md`. La consistencia aquí es clave para la navegabilidad y la comprensión del proyecto.
5.  **Unit Test File Organization:**
    
    -   **Ubicación:** Los archivos de pruebas unitarias se ubicarán en el directorio `tests/unit/`, replicando la estructura del directorio `src/` correspondiente al módulo bajo prueba (ej. `tests/unit/services/` para `src/ultibot_backend/services/`).
    -   **Nomenclatura de Archivos:** `test_<nombre_del_modulo_bajo_prueba>.py` (ej. `tests/unit/services/test_trading_engine_service.py`).
    -   **Nomenclatura de Funciones/Métodos de Prueba:** `test_<condicion_o_comportamiento_esperado>` (ej. `test_calcula_pnl_correctamente_para_trade_positivo`, `test_levanta_excepcion_si_falta_parametro_obligatorio`). Usar nombres descriptivos.
6.  **Asynchronous Operations (`async`/`await`):**
    
    -   Se utilizará `async` y `await` para todas las operaciones de I/O que puedan ser no bloqueantes:
        -   Llamadas a APIs externas (`httpx`).
        -   Interacciones con la base de datos si se utiliza un driver asíncrono con `supabase-py` o directamente con PostgreSQL.
        -   Comunicaciones WebSocket.
        -   Operaciones de lectura/escritura de archivos si son intensivas y pueden beneficiarse del asincronismo (raro en este contexto, pero posible).
    -   Todas las funciones de endpoint de FastAPI (definidas con `@router.get`, `@router.post`, etc.) serán `async def` por defecto, a menos que una operación sea puramente síncrona, computacionalmente intensiva y muy corta (en cuyo caso FastAPI puede manejarla eficientemente en un threadpool separado, pero `async def` es la norma).
    -   Evitar mezclar código bloqueante síncrono dentro de funciones `async` sin delegarlo explícitamente a un ejecutor de hilos (ej. `asyncio.to_thread` en Python 3.9+).
7.  **Type Safety:**
    
    -   **Type Hints Obligatorios:** Se utilizarán type hints de Python de forma exhaustiva y precisa en:
        -   Firmas de funciones y métodos (argumentos y tipo de retorno).
        -   Declaraciones de variables donde el tipo no sea obvio o para mayor claridad.
    -   **Pydantic Models:** Se usarán de forma preferente para:
        -   Validación de datos en endpoints de FastAPI (request bodies, query/path parameters, response models).
        -   Definición de modelos de datos claros y estructurados dentro de la lógica de negocio.
        -   Configuraciones de la aplicación.
    -   **Análisis Estático de Tipos (Mandatorio para v1.0):**
        -   _Ruff Type Checking:_ Se configurarán y habilitarán las reglas de chequeo de tipos de `Ruff` (`PYI` para type checking y otras que puedan aplicar).
        -   _MyPy (Alternativa/Complemento):_ Si las capacidades de Ruff no son suficientes o se prefiere un chequeo más exhaustivo y configurable, se integrará `MyPy`. La configuración (ej. `strict = true` o un subconjunto de opciones estrictas) se definirá en `pyproject.toml`. Recomendación: Empezar con las capacidades de Ruff y evaluar MyPy si se encuentran limitaciones. Para un proyecto de esta naturaleza, un chequeo estático fuerte es muy valioso.
    -   **Type Definitions:**
        -   Los tipos complejos o compartidos se definirán en archivos `types.py` dentro de los módulos correspondientes o en un directorio `shared/domain_types.py` o similar si son transversales.
        -   Se evitará el uso de `typing.Any` en la medida de lo posible. Su uso debe ser una excepción justificada y documentada con un comentario `# type: ignore[misc]` si es necesario para MyPy/Ruff, explicando por qué `Any` es la única opción viable. Preferir `TypeVar`, `ParamSpec`, `Protocol`, o uniones más específicas.
        -   Utilizar los tipos genéricos de `collections.abc` (ej. `Mapping`, `Sequence`) en lugar de `dict`, `list` en type hints para mayor flexibilidad, a menos que se requiera la mutabilidad específica de `list` o `dict`.
8.  **Comments & Documentation:**
    
    -   **Comentarios en Código:**
        -   Deben explicar el "porqué" de una decisión de diseño o una lógica compleja, no el "qué" hace el código (el código bien escrito debe ser autoexplicativo en el "qué").
        -   Evitar comentarios obvios o que parafrasean el código.
        -   Usar `TODO:`, `FIXME:`, `XXX:` para marcar tareas pendientes o problemas, idealmente con una referencia a un issue tracker si existe.
    -   **Docstrings (Mandatorio y Estilo Único):**
        -   Todas las funciones públicas, clases, métodos y módulos (archivos `.py`) deberán tener docstrings.
        -   _Estilo Adoptado:_ Se utilizará **Google Style** para los docstrings. Esto incluye secciones como `Args:`, `Returns:`, `Raises:`.
        -   `Ruff` (con reglas de `pydocstyle`) se configurará para verificar la conformidad con este estilo.
        -   El contenido debe ser conciso pero completo, explicando el propósito, los parámetros, el valor de retorno, y las excepciones que puede lanzar.
    -   **READMEs:**
        -   El `README.md` principal del proyecto es fundamental y debe estar bien mantenido.
        -   Módulos o componentes complejos (ej. `ultibot_backend`, `ultibot_ui`) deben tener su propio `README.md` explicando su propósito, cómo configurarlo (si aplica), y cómo usarlo o probarlo. Para la v1.0, esto puede ser conciso pero útil.
    -   **Documentación de API:** Se aprovechará la generación automática de documentación OpenAPI (Swagger UI / ReDoc) proporcionada por FastAPI. Los docstrings de los endpoints y los modelos Pydantic contribuirán a esta documentación.
9.  **Dependency Management:**
    
    -   **Herramienta:** Poetry `1.8.3` (o la versión definida en el stack).
    -   **Archivo de Definición:** Todas las dependencias (producción y desarrollo) se gestionarán exclusivamente a través del archivo `pyproject.toml`.
    -   **Versionado:**
        -   Se preferirán rangos de versiones específicos y restrictivos (ej. `~1.2.3` que permite `1.2.x` pero no `1.3.0`, o `^1.2.3` que permite `1.x.y` donde `x >= 2` y `y >= 3` pero no `2.0.0`).
        -   Para dependencias críticas o aquellas con APIs menos estables, se considerará el "pineo" a versiones exactas (`package = "1.2.3"`) en `pyproject.toml` si es necesario, aunque `poetry.lock` siempre contendrá versiones exactas.
        -   El archivo `poetry.lock` debe ser versionado en Git para asegurar compilaciones reproducibles.
    -   **Política de Adición de Dependencias:**
        -   Antes de añadir una nueva dependencia, se debe evaluar críticamente si su funcionalidad ya puede ser cubierta por dependencias existentes o por la librería estándar de Python.
        -   Se priorizarán dependencias bien mantenidas, con buena documentación y una comunidad activa.
        -   Se analizará el impacto de la nueva dependencia en el tamaño total del proyecto y el grafo de sub-dependencias.
10.  **Detailed Language & Framework Conventions:**
    
    -   **Python General:**
        -   _Inmutabilidad:_ Preferir estructuras de datos inmutables (ej. tuplas en lugar de listas para colecciones que no deben cambiar después de su creación) donde sea práctico y mejore la previsibilidad.
        -   _Expresividad:_ Utilizar comprensiones de listas/diccionarios/conjuntos y expresiones generadoras por su concisión y eficiencia cuando sean legibles.
        -   _Manejo de Recursos:_ Utilizar `with` statements (context managers) para la gestión de recursos que necesitan ser liberados explícitamente (ej. archivos, locks, conexiones de red si el cliente no lo gestiona automáticamente).
        -   _Manejo de Errores:_
            -   Usar excepciones personalizadas (heredando de `Exception` o excepciones estándar más específicas) para errores de dominio propios de la aplicación.
            -   Ser específico al capturar excepciones (`except MiErrorCustom:` en lugar de `except Exception:`).
            -   Utilizar bloques `try...except...else...finally` apropiadamente. El bloque `else` es útil para código que debe ejecutarse si no hay excepciones. `finally` para limpieza.
        -   _Imports Circulares:_ Deben evitarse activamente mediante un diseño modular adecuado y, si es necesario, refactorización o el uso de imports dentro de funciones/métodos (aunque esto último es menos ideal).
        -   _Principio de Responsabilidad Única (SRP):_ Funciones, métodos y clases deben ser cortos, cohesivos y tener una única responsabilidad bien definida.
        -   _Logging:_
            -   Utilizar el módulo `logging` estándar de Python.
            -   Configurar el logging de forma centralizada (ej. en `main.py` o un módulo de configuración).
            -   Utilizar niveles de log apropiados (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            -   En los logs, incluir información contextual útil (ej. timestamps, nombre del módulo, ID de correlación si aplica). Considerar logging estructurado (ej. JSON) para facilitar el análisis por máquinas en producción.
        -   _Configuración:_
            -   Utilizar modelos Pydantic (específicamente `BaseSettings`) para gestionar la configuración de la aplicación (cargada desde variables de entorno, archivos `.env`, etc.). Esto proporciona validación y type hints para la configuración.
        -   _Zen de Python (PEP 20):_ Mantener los principios del Zen de Python en mente al escribir código ("Bello es mejor que feo", "Explícito es mejor que implícito", "Simple es mejor que complejo", etc.).
    -   **FastAPI Específico:**
        -   _Inyección de Dependencias (`Depends`):_ Utilizarla extensivamente para gestionar dependencias como servicios de negocio, conexiones a bases de datos, configuración, y la obtención del usuario actual (si se implementa autenticación). Promueve código desacoplado y fácil de probar.
        -   _Modelos Pydantic:_ Son la base para la validación automática de request/response bodies, path/query parameters y headers. Definir `response_model` explícitamente en los endpoints para asegurar la estructura de la respuesta y para la documentación automática.
        -   _Routers Modulares (`APIRouter`):_ Organizar los endpoints en routers separados por recurso o funcionalidad (ej. `trading_router.py`, `users_router.py`) e incluirlos en la aplicación principal FastAPI. Esto se alinea con tu estructura de proyecto.
        -   _Manejo de Errores HTTP:_ Utilizar `HTTPException` de FastAPI para devolver respuestas de error HTTP estándar. Considerar la creación de manejadores de excepciones personalizados (`@app.exception_handler(MiErrorCustom)`) para convertir errores de dominio en respuestas `HTTPException` consistentes.
        -   _Tareas en Segundo Plano:_ Para tareas cortas que no necesitan bloquear la respuesta, usar `BackgroundTasks`. Para tareas más largas o complejas, considerar una solución más robusta como Celery (aunque para v1.0, `BackgroundTasks` es un buen inicio según tu `Architecture.md`).
        -   _Path Operation Functions:_ Mantener las funciones de los endpoints (decoradas con `@router.get`, etc.) lo más delgadas posible, delegando la lógica de negocio a servicios o "casos de uso" separados.


## Overall Testing Strategy

Considerando nuestro enfoque en una v1.0 ágil y estable para una aplicación local, propongo la siguiente estrategia:

-   **Tools:**
    
    -   **Framework Principal de Pruebas:** `pytest` (ya definido en el stack).
    -   **Pruebas Asíncronas:** `pytest-asyncio` (ya definido en el stack).
    -   **Mocking/Stubbing:** La biblioteca `unittest.mock` (parte de la librería estándar de Python) será nuestra herramienta principal para crear mocks y stubs.
    -   **E2E Testing (si se considera para v1.0 muy limitada):** Para una aplicación de escritorio como esta, las pruebas E2E completas pueden ser complejas de automatizar. Para la v1.0, podríamos enfocarnos en pruebas de integración más robustas y pruebas manuales exhaustivas de los flujos de UI. Si se decide automatizar algo de UI, `Playwright` (mencionado en la plantilla como ejemplo) podría ser una opción, pero su implementación completa podría quedar fuera del alcance de la v1.0 para mantener la simplicidad. _Propongo priorizar pruebas manuales y de integración para la UI en v1.0._
-   **Unit Tests:**
    
    -   **Scope:** Probar unidades individuales de código (funciones, métodos, clases) de forma aislada. Se centrarán en la lógica de negocio de los servicios, funciones de utilidad, y la lógica interna de los componentes (sin UI).
    -   **Location:** `tests/unit/` replicando la estructura de `src/`, con archivos `test_<nombre_modulo>.py`, como se definió en "Coding Standards".
    -   **Mocking/Stubbing:** Todas las dependencias externas (llamadas a API con `httpx`, interacciones con base de datos, llamadas a otros servicios internos) _deben_ ser mockeadas usando `unittest.mock`.
    -   **AI Agent Responsibility:** El agente IA encargado de desarrollar una función o módulo _debe_ generar pruebas unitarias que cubran los caminos lógicos principales, casos límite y manejo de errores esperados para el código que produce.
-   **Integration Tests:**
    
    -   **Scope:** Probar la interacción entre varios componentes o módulos del backend. Por ejemplo:
        -   Interacción entre un endpoint de API (FastAPI), el servicio de negocio que invoca y su interacción con un mock de `DataPersistenceService` o mocks de clientes de API externas.
        -   Flujos que involucren al `TradingEngine` y el `AI_Orchestrator` (con el `AI_Orchestrator` mockeado o sus dependencias externas mockeadas).
    -   **Location:** `tests/integration/`.
    -   **Environment:** Las pruebas de integración pueden requerir una instancia de base de datos de prueba (Supabase ofrece entornos de desarrollo) o mocks muy bien definidos para servicios externos. Se evitará depender de servicios externos reales en pruebas automatizadas para asegurar su fiabilidad y velocidad.
    -   **AI Agent Responsibility:** El agente IA puede ser instruido para generar pruebas de integración para los flujos de API que implementa, asegurando que los diferentes servicios internos se comunican correctamente según los contratos definidos.
-   **End-to-End (E2E) Tests:**
    
    -   **Scope:** Para la v1.0 de una aplicación local, las pruebas E2E automatizadas de la UI (PyQt5) pueden ser complejas y llevar tiempo.
        -   **Propuesta v1.0:** Nos enfocaremos en **pruebas manuales exhaustivas** de los flujos de usuario clave directamente en la aplicación PyQt5.
        -   Si hay lógica crítica en el backend que representa un "flujo completo" sin UI directa (ej. un proceso de análisis de oportunidad disparado internamente), se podría cubrir con una prueba de integración de alto nivel.
    -   **AI Agent Responsibility:** N/A para pruebas E2E automatizadas en v1.0. El agente debe asegurar que los componentes individuales y sus integraciones (probadas unitaria y por integración) funcionen, lo que facilitará las pruebas manuales.
-   **Test Coverage:**
    
    -   **Target:** Si bien no estableceremos un porcentaje estricto de cobertura de código para la v1.0 para no ralentizar el desarrollo, se espera una "cobertura razonable" de la lógica crítica a través de pruebas unitarias y de integración. La calidad y el propósito de las pruebas son más importantes que el porcentaje bruto.
    -   **Measurement:** `pytest-cov` (un plugin de `pytest`) se puede utilizar localmente para generar informes de cobertura si se desea analizar.
-   **Mocking/Stubbing Strategy (General):**
    
    -   Preferir mocks claros y específicos para cada prueba. Evitar mocks globales o demasiado complejos si es posible.
    -   El objetivo es que las pruebas sean rápidas, fiables y fáciles de entender.
-   **Test Data Management:**
    
    -   Para pruebas unitarias y de integración, los datos de prueba se definirán directamente en los archivos de prueba o mediante fixtures de `pytest`.
    -   Se evitará depender de estados de base de datos preexistentes; cada prueba debe configurar y, si es necesario, limpiar sus propios datos.


## Security Best Practices

-   **Input Sanitization/Validation:**
    
    -   Toda entrada de API recibida por el backend FastAPI **debe** ser validada usando modelos Pydantic. Esto incluye tipos de datos, formatos esperados y rangos (si aplican).
        
    -   Las entradas en la UI de PyQt5 (ej. campos de texto para claves API, parámetros de estrategias) deben tener validaciones básicas en el lado del cliente para mejorar la UX, pero la validación autoritativa y final **siempre** ocurrirá en el backend.
-   **Output Encoding:**
    
    -   Dado que la UI es una aplicación de escritorio PyQt5 y no una aplicación web tradicional, los riesgos de XSS a través de la renderización de HTML son diferentes. Sin embargo, si se muestra contenido dinámico que podría originarse de fuentes externas (ej. nombres de monedas, mensajes de error de API), PyQt5 generalmente maneja bien la renderización segura de texto.
    -   Al enviar datos a Telegram, se utilizará el `parse_mode="MarkdownV2"` o `HTML` según se defina en la API de Telegram, asegurándose de escapar correctamente cualquier carácter especial para evitar problemas de formato o inyección si el contenido proviene de entradas no confiables.
-   **Secrets Management:**
    
    -   Las claves API (Binance, Telegram, Mobula, Gemini) **nunca** deben estar hardcodeadas en el código fuente.
    -   Se almacenarán de forma segura. Como se detalló en `Architecture.md` y los esquemas de base de datos, las claves se guardarán en la tabla `api_credentials` de la base de datos Supabase/PostgreSQL, con los campos sensibles (`encrypted_api_key`, `encrypted_api_secret`, `encrypted_other_details`) **encriptados en la capa de aplicación antes de la persistencia**. La clave de encriptación para estos datos debe ser gestionada de forma segura por el usuario (ej. ingresada al iniciar la aplicación y mantenida en memoria, o derivada de una contraseña maestra).
    -   El acceso a los secretos en el código se realizará a través del `CredentialManager`, que se encargará de la desencriptación en el momento del uso.
        
    -   Las variables de entorno (gestionadas con modelos Pydantic `BaseSettings` como se mencionó en "Coding Standards") pueden usarse para configuración no sensible o para la clave de encriptación maestra si se obtiene de forma segura del entorno. No se deben usar para almacenar directamente las claves API externas.
-   **Dependency Security:**
    
    -   Se utilizará `Poetry` para la gestión de dependencias. El archivo `poetry.lock` asegura builds reproducibles.
    -   Se recomienda ejecutar `poetry show --outdated` periódicamente y antes de "releases" (aunque sea para uso personal) para revisar dependencias desactualizadas.
    -   Se puede usar `pip-audit` (integrable con Poetry) o herramientas similares para escanear vulnerabilidades conocidas en las dependencias. Para la v1.0, esto puede ser un proceso manual periódico.
-   **Authentication/Authorization Checks (para la API interna):**
    
    -   La API interna de FastAPI, aunque se ejecute localmente para la UI, podría considerar un mecanismo de autenticación muy ligero (ej. un token simple generado al inicio, o protección de que solo acepte conexiones de `localhost`) si se desea una capa extra de seguridad, aunque para la v1.0, al ser una aplicación local y personal, esto podría simplificarse.
    -   _Propuesta v1.0:_ Dado que es una aplicación de escritorio donde backend y UI corren en la misma máquina para uso personal, la API FastAPI se enlazará exclusivamente a `localhost`, lo que limita la accesibilidad externa. No implementaremos un esquema de autenticación complejo entre la UI y esta API local inicialmente.
-   **Principle of Least Privilege (Implementación):**
    
    -   Las claves API de Binance deben configurarse con los permisos mínimos necesarios para las operaciones que UltiBotInversiones realizará (ej. habilitar trading para spot, pero no necesariamente retiros si el bot no los necesita). Esto se configura en la plataforma de Binance al crear la API key.
    -   El acceso a la base de datos (Supabase) también debe seguir este principio si se definen roles o políticas específicas.
-   **API Security (General - para llamadas salientes):**
    
    -   Todas las llamadas a APIs externas (Binance, Mobula, Gemini, Telegram) **deben** realizarse sobre HTTPS. `httpx` lo hará por defecto.
-   **Error Handling & Information Disclosure:**
    
    -   Como se definió en la "Error Handling Strategy", los mensajes de error detallados (stack traces, SQL errors) no se expondrán directamente en la UI ni se enviarán a Telegram sin sanitizar. Se registrarán detalladamente en el backend y se presentarán mensajes genéricos o códigos de error al usuario.
        
-   **File System Access:**
    
    -   Si la aplicación necesita leer/escribir en el sistema de archivos local (ej. para logs, configuraciones locales adicionales, exportaciones), debe hacerlo en directorios designados y con los permisos adecuados, evitando accesos a rutas sensibles del sistema.


## Key Reference Documents

-   **`Project Brief.md`**
    -   Descripción: El documento inicial que captura la idea del proyecto, los objetivos y el problema a resolver.
-   **`PRD.md` (Product Requirements Document)**
    -   Descripción: Define el qué y el porqué del producto, los objetivos, el alcance del MVP, los requisitos funcionales y no funcionales.
-   **`Epics.md`**
    -   Descripción: Contiene el desglose detallado de las Épicas y las historias de usuario asociadas.
-   **`PM_CHECKLIST.md` (Completado)**
    -   Descripción: Documenta la validación y las decisiones tomadas sobre el PRD.
-   **`Architecture.md` (este documento)**
    -   Descripción: Detalla la arquitectura técnica general del sistema.
-   **UI/UX Specification** (cuando se cree)
    -   Descripción: Especificaciones detalladas de la interfaz y experiencia de usuario.
-   **Frontend Architecture Document** (cuando se cree)
    -   Descripción: Detalles técnicos de la arquitectura frontend.
-   **Agent Configuration File** (ej. `agent-config.txt`)
    -   Descripción: Define los agentes IA, sus roles, personas y tareas.
-   **BMAD Method Core Documents** (ej. `personas.txt`, `tasks.txt`, `templates.txt`, `checklists.txt`, `data.txt`)
    -   Descripción: Plantillas y definiciones base del método BMAD.


## Change Log

Esta sección se utilizará para rastrear las versiones y los cambios significativos realizados en este Documento de Arquitectura. Para esta primera versión que estamos creando, podemos registrarla como la inicial.

Versión	Fecha	Autor(es)	Resumen de Cambios
0.1	2025-05-28	Carlos & Fred (Architect)	Creación inicial del Documento de Arquitectura.

----------

# **Prompt for Design Architect**

Esta sección proporciona un conjunto de instrucciones o un prompt que se puede entregar a un agente de IA especializado como "Diana, la Arquitecta de Diseño". El objetivo es que este agente genere el "Documento de Especificación de UI/UX" y, potencialmente, un "Documento de Arquitectura Frontend" para "UltiBotInversiones".

El prompt debe basarse en la información ya definida en el `PRD.md` y en este `Architecture.md`.

Aquí tienes una propuesta de prompt:

```
**Prompt para Diana, Arquitecta de Diseño de UI/UX (o Agente Equivalente):**

**Proyecto:** UltiBotInversiones

**Objetivo Principal:** Diseñar la Interfaz de Usuario (UI) y la Experiencia de Usuario (UX) para "UltiBotInversiones", una plataforma de trading personal avanzada. El diseño debe ser profesional, moderno, intuitivo y de alto rendimiento, implementado con PyQt5.

**Documentos de Referencia Primarios (adjuntos o con acceso provisto):**
1.  `PRD.md` (Product Requirements Document para UltiBotInversiones)
2.  `Architecture.md` (System Architecture Document para UltiBotInversiones)

**Entregables Clave Esperados:**
1.  **Documento de Especificación de UI/UX Detallado:**
    * Wireframes y mockups para todas las pantallas y vistas clave identificadas en el PRD (Dashboard Principal, Configuración, Gestión de Estrategias, Historial de Operaciones, etc.).
    * Definición del flujo de navegación del usuario.
    * Guía de estilo visual (incluyendo paleta de colores del tema oscuro, tipografía, iconografía).
    * Principios de interacción y componentes de UI reutilizables.
    * Consideraciones de accesibilidad de alto nivel.
2.  **(Opcional, si se considera necesario) Documento de Arquitectura Frontend:**
    * Estructura de componentes de la UI en PyQt5 (ventanas, widgets personalizados).
    * Estrategia para la comunicación entre la UI (PyQt5) y el backend (FastAPI API interna).
    * Manejo del estado en la UI (si aplica).

**Directrices y Requisitos Clave del Diseño (extraídos y expandidos del PRD y Architecture.md):**

* **Stack Tecnológico UI:** La implementación será con **PyQt5 (versión 5.15.11+)**. Se debe utilizar **QDarkStyleSheet** o un enfoque similar para lograr un tema oscuro consistente y profesional.
* **Visión General y Experiencia Deseada:**
    * **Look and Feel:** Profesional, moderno, claro, tema oscuro consistente.
    * **UX:** Intuitiva, fluida, de gran apoyo al usuario (que no es experto técnico ni en trading algorítmico). El sistema debe asistir activamente, simplificando decisiones complejas.
* **Paradigmas de Interacción Clave (del PRD):**
    * Dashboard Centralizado (mercado, portafolio, gráficos, notificaciones).
    * Configuración Simplificada.
    * Interacción con Gráficos (selección de par, temporalidades).
    * Notificaciones Integradas (UI y Telegram).
    * Confirmaciones Explícitas para acciones críticas con capital real.
* **Pantallas/Vistas Centrales a Diseñar (basado en PRD y Épicas):**
    * Autenticación de Usuario (si se decide implementar un login local ligero, de lo contrario, el inicio directo).
    * Dashboard Principal:
        * Resumen de Datos de Mercado (tiempo real, configurable).
        * Estado del Portafolio (diferenciando Paper Trading y Real).
        * Visualización de Gráficos Financieros (velas, volumen, temporalidades).
        * Centro de Notificaciones del Sistema (integrado en la UI).
    * Configuración del Sistema:
        * Gestión de Conexiones y Credenciales (Binance, Telegram, etc. - CRUD seguro).
        * Configuración de la aplicación (ej. preferencias de usuario, listas de seguimiento, perfiles de riesgo, configuración de IA).
    * Panel de Gestión de Estrategias:
        * Listar, configurar parámetros, activar/desactivar estrategias (Scalping, Day Trading, Arbitraje Simple) para modos Paper y Real.
        * Monitoreo básico del desempeño por estrategia.
    * Historial y Detalles de Operaciones:
        * Revisar historial de operaciones cerradas y estado de activas (P&L, estrategia, etc.).
    * (Considerar vistas para la gestión de oportunidades, si la UI lo requiere más allá de las notificaciones).
* **Requisitos No Funcionales a Considerar en el Diseño:**
    * **Rendimiento:** La UI debe ser fluida y responsiva, sin bloqueos. Actualización de datos en tiempo real o cuasi real.
    * **Usabilidad:** Clara, intuitiva, profesional. Layout bien organizado. Notificaciones claras y oportunas.
    * **Fiabilidad:** El diseño debe contribuir a un manejo de errores claro para el usuario.
* **Branding:** Profesional, tecnológico, confiable.
* **Output:** Los entregables deben ser claros, bien documentados y listos para ser utilizados por un agente de desarrollo frontend o un desarrollador Python con PyQt5.

Por favor, revisa el `PRD.md` (sección "Metas de Interacción del Usuario y Diseño") y el `Architecture.md` (especialmente las secciones "Project Structure > src/ultibot_ui/", "Internal APIs Provided", y los "Data Models" que la UI podría necesitar consumir/presentar) para un contexto completo.

```

----------
