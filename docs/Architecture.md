# UltiBotInversiones Architecture Document

## Introduction / Preamble

Este documento detalla la arquitectura técnica general de UltiBotInversiones, una plataforma avanzada de trading personal diseñada para ejecutar múltiples estrategias sofisticadas de trading (scalping, day trading y arbitraje) en tiempo real. La arquitectura está diseñada para garantizar latencia ultra-baja, procesamiento paralelo eficiente y una integración fluida con servicios externos críticos como Binance, Telegram y Gemini AI.

La arquitectura ha sido concebida para satisfacer los requisitos no funcionales exigentes (rendimiento, seguridad, fiabilidad) mientras mantiene la flexibilidad para evolucionar más allá de la v1.0. Su objetivo principal es servir como el plano técnico definitivo para el desarrollo impulsado por IA, asegurando consistencia y adherencia a los patrones y tecnologías elegidos.

**Relationship to Frontend Architecture:**
Dado que UltiBotInversiones incluye una interfaz de usuario significativa implementada con PyQt5, se desarrollará un Documento de Arquitectura Frontend separado que detallará los aspectos específicos de la UI. Este documento principal establece las decisiones tecnológicas fundamentales para todo el proyecto, incluyendo la interfaz de usuario.

## Technical Summary

UltiBotInversiones se implementará como un **Monolito Modular** dentro de una estructura de **Monorepo**, con módulos claramente definidos que incluyen la interfaz de usuario (UI con **PyQt5**), la lógica del núcleo de trading (para operaciones simuladas y reales), la gestión de datos, los servicios de Inteligencia Artificial (IA) y las notificaciones. El sistema utilizará **Python 3.11+** como lenguaje principal para el backend, apoyándose en **FastAPI** para la creación de servicios internos. La persistencia de datos se gestionará con **PostgreSQL** (a través de **Supabase**), utilizando el cliente `supabase-py`, y se empleará **Redis** para la caché L2. Las interacciones HTTP asíncronas se realizarán con `httpx` y las conexiones WebSocket (ej. con Binance) mediante la biblioteca `websockets`. Las tareas en segundo plano, como los análisis de IA complejos, se gestionarán inicialmente con las `BackgroundTasks` de FastAPI.

El motor de análisis de IA se basará en **Gemini** (específicamente modelos como Gemini 1.5 Pro o Flash), orquestado mediante **LangChain (Python)**. Esta aproximación permitirá a Gemini interactuar con "Herramientas" desarrolladas como wrappers para APIs externas, incluyendo la **API de Binance** (para datos de mercado y ejecución de operaciones), y la **API de Mobula** (para verificación de datos de activos). Otras integraciones clave incluyen la **API de Telegram** para notificaciones al usuario.

La arquitectura está optimizada para una **latencia ultra-baja** (objetivo <500ms para el ciclo completo de detección-análisis-ejecución) y un eficiente **procesamiento asíncrono/paralelo**. El diseño se adhiere a principios de Domain-Driven Design (DDD) y, donde sea aplicable, Command Query Responsibility Segregation (CQRS), con un fuerte énfasis en la modularidad para facilitar la posible evolución futura hacia una Arquitectura Orientada a Eventos con Microservicios Opcionales post-v1.0.

## High-Level Overview

UltiBotInversiones adopta un **Monolito Modular** como su estilo arquitectónico principal para la v1.0, siguiendo la decisión documentada en el PRD. Esta elección favorece la velocidad de desarrollo inicial manteniendo una clara separación de responsabilidades a través de módulos bien definidos. El sistema está organizado como un **Monorepo**, facilitando la gestión de dependencias y la coherencia entre componentes, mientras prepara el terreno para una posible evolución futura hacia una arquitectura más distribuida.

El sistema implementa un patrón de **flujo de datos unidireccional** para su funcionamiento principal: desde la captura de datos del mercado y detección de oportunidades (utilizando datos de mercado y análisis de IA), pasando por un análisis y toma de decisiones sofisticados —orquestados por **LangChain (Python)** que permite a **Gemini** utilizar diversas herramientas (como datos de Binance y Mobula)—, hasta la ejecución de la operación (simulada o real) y la notificación al usuario (vía UI y Telegram). Este flujo garantiza un procesamiento predecible y una clara trazabilidad de las decisiones operativas.

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
    * _Rationale/Referencia:_ Para la interacción con la IA (Gemini), se utilizará el patrón Agente-Herramientas facilitado por LangChain (Python). El agente (impulsado por Gemini) podrá decidir dinámicamente qué "herramienta" (wrappers para APIs de Binance, Mobula API, etc.) utilizar para recopilar información o ejecutar acciones, permitiendo un análisis y toma de decisiones más flexibles y potentes.

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


## Core Workflow / Sequence Diagrams

    sequenceDiagram
        participant User as Usuario (via UI)
        participant UI as Interfaz de Usuario (PyQt5)
        participant MarketDataMgr as Gestor de Datos de Mercado (Binance WS)
        participant TradingEngine as Motor de Trading
        participant ConfigManager as Gestor de Configuración
        participant DataPersistenceService as Servicio de Persistencia (Supabase)
        participant AI_Orchestrator as Orquestador IA (LangChain + Gemini)
        participant CredentialManager as Gestor de Credenciales
        participant BinanceAPI as API de Binance (REST)
        participant MobulaAPI as API de Mobula (Ej. Herramienta IA)
        participant NotificationService as Servicio de Notificaciones
        participant TelegramAPI as API de Telegram
    
        Note over MarketDataMgr, TradingEngine: Fase 1: Detección y Registro de Oportunidad (Flujo Iniciado por Datos de Mercado)
        MarketDataMgr->>TradingEngine: Notifica evento de mercado relevante (ej. datos de klines, ticker)
        TradingEngine->>TradingEngine: Evalúa evento con estrategias activas
        alt Oportunidad Potencial Detectada por Estrategia Interna
            TradingEngine->>DataPersistenceService: Crea/Actualiza registro de Oportunidad (O_ID, datos_iniciales, estado: nueva/actualizada)
            DataPersistenceService-->>TradingEngine: Oportunidad Creada/Actualizada (O_ID)
            TradingEngine->>AI_Orchestrator: Solicita análisis para Oportunidad (O_ID)
        end
    
        Note over AI_Orchestrator, DataPersistenceService, GeminiAPI, BinanceAPI, MobulaAPI: Fase 2: Análisis y Enriquecimiento por IA
        AI_Orchestrator->>DataPersistenceService: Obtiene datos de Oportunidad (O_ID)
        DataPersistenceService-->>AI_Orchestrator: Datos de Oportunidad
        AI_Orchestrator->>AI_Orchestrator: Prepara prompt inicial con datos y herramientas disponibles
    
        loop Ciclo de Invocación de Herramientas (LangChain)
            AI_Orchestrator->>GeminiAPI: Envía prompt/solicitud de siguiente paso
            GeminiAPI-->>AI_Orchestrator: Decide (ej: usar Herramienta_Binance_MarketData)
            alt Usar Herramienta Binance (REST)
                AI_Orchestrator->>CredentialManager: Solicita credenciales para herramienta Binance (si aplica y no cacheadas)
                CredentialManager-->>AI_Orchestrator: Credenciales
                AI_Orchestrator->>BinanceAPI: Obtiene datos de mercado adicionales (REST)
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
