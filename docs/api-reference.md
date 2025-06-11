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
