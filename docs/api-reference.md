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
        * Description: Gestiona la configuración de la aplicación y las preferencias del usuario, incluyendo el estado de activación del modo Paper Trading y el capital virtual.
        * Consumers: `ConfigManager`, UI (Settings View).
        * Example Endpoints: 
            * `GET /config/`: Obtiene la configuración completa del usuario (`UserConfiguration`).
            * `PATCH /config/`: Actualiza parcialmente la configuración del usuario. Utiliza `UpdateUserConfigurationRequest` (ver `docs/data-models.md`).
            * `GET /config/scan-presets`: Obtiene presets de escaneo.
            * `POST /config/scan-presets`: Guarda presets de escaneo.
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
