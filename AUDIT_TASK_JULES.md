# UltiBotInversiones - Audit Action Plan (AUDIT_TASK_JULES.md)

## Introduction

This document outlines a structured action plan based on the findings of the `AUDIT_REPORT.md`. It breaks down the identified issues into phases, tasks, and subtasks to guide the development process towards a more robust, secure, and functional UltiBotInversiones product. The goal is to transition from an MVP state to a production-ready system.

Each task corresponds to an issue highlighted in the audit report, and subtasks are derived from the "Suggested Actions" provided therein.

---

## Phase 1: Address Critical Architectural and Security Flaws

This phase focuses on resolving fundamental architectural problems and security vulnerabilities that impact the stability, security, and scalability of the application.

### Task 1.1: (Critical Issue 1) UI Application Incorrectly Initializes and Uses Backend Services and Credentials
**Original Title:** UI Application (`src/ultibot_ui/main.py`) Incorrectly Initializes and Uses Backend Services and Credentials.
*   **Description:** The UI's `main.py` and several widgets directly initialize/use backend services, database connections, and handle sensitive credentials. This is a major architectural flaw.
*   **Subtasks:**
    *   **[x] 1.1.1:** Refactor `src/ultibot_ui/main.py` to remove all backend service initialization, database connections, and credential handling.
    *   **[x] 1.1.2:** Ensure the UI relies exclusively on `src/ultibot_ui/services/api_client.py` for all backend interactions.
    *   **[x] 1.1.3:** Modify UI widgets and windows (`ChartWidget`, `NotificationWidget`, `PortfolioWidget`, `DashboardView`, `MainWindow`) to obtain data through UI-specific services that use the `APIClient`, instead of direct backend service usage.
    *   **[x] 1.1.4:** Ensure the backend is architected and documented to run as a separate FastAPI server process, distinct from the UI client. (Verified frontend changes are consistent with this).

### Task 1.2: (Critical Issue 5) `FIXED_USER_ID` Hardcoding and Inconsistent Usage
**Original Title:** `FIXED_USER_ID` Hardcoding and Inconsistent Usage.
*   **Description:** A hardcoded `FIXED_USER_ID` is prevalent, limiting the application to a single-user context and posing a security risk.
*   **Subtasks:**
    *   **[ ] 1.2.1:** Design and implement a proper user authentication and authorization system (e.g., JWT-based).
        *   **[x] 1.2.1.1:** Add dependencies (`python-jose[cryptography]`, `passlib[bcrypt]`) to `pyproject.toml`. (UI dependencies temporarily commented out to allow installation).
        *   **[x] 1.2.1.2:** Create Pydantic models for User (UserCreate, UserInDB, User) and Token (Token, TokenData) in `src/ultibot_backend/security/schemas.py`.
        *   **[x] 1.2.1.3:** Add JWT configuration settings (SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES) to `src/ultibot_backend/app_config.py`. (JWT_SECRET_KEY must be set in `.env`).
        *   **[x] 1.2.1.4:** Implement utility functions for password hashing/verification and JWT creation/decoding in `src/ultibot_backend/security/core.py`. Includes placeholder for `get_current_user` dependency.
        *   **[x] 1.2.1.5:** Create API endpoints for user registration (`/auth/register`) and login (`/auth/login`) in `src/ultibot_backend/api/v1/endpoints/auth.py` (uses placeholder DB interaction for now). Includes `/auth/me` endpoint.
        *   **[x] 1.2.1.6:** Register the authentication router in `src/ultibot_backend/main.py`.
        *   **[x] 1.2.1.7:** Implement actual database interaction for user creation and retrieval in `auth.py` and `security/core.py` (replacing placeholders, integrating with `SupabasePersistenceService`). This includes creating/managing a 'users' table in Supabase.
        *   **[x] 1.2.1.8:** Secure relevant API endpoints using the `get_current_active_user` dependency.
            *   **[x] `config.py`**
            *   **[x] `notifications.py`**
            *   **[x] `reports.py`**
            *   **[x] `portfolio.py`**
            *   **[x] `trades.py`**
            *   **[x] `performance.py`**
            *   **[x] `opportunities.py`**
            *   **[x] `strategies.py`**
            *   **[x] `trading.py`**
            *   **[x] `market_data.py`**
            *   **[x] `capital_management.py`**
            *   **[ ] `binance_status.py` (Evaluado como no necesario)**
            *   **[ ] `telegram_status.py` (Evaluado como no necesario)**
            *   **[ ] `gemini.py` (Evaluado como no necesario, asumiendo uso general)**
    *   **[x] 1.2.2:** Remove all hardcoded `FIXED_USER_ID` instances from backend files (e.g., `main.py`, `app_config.py`, routers for `ConfigService`, `TelegramStatus`, `Reports`, `Opportunities`) and UI. (UI part completed by refactoring widgets to accept user_id and loading from .env in main.py; backend part completed).
    *   **[x] 1.2.3:** Propagate the authenticated user's ID throughout the system, from API endpoints down to services and persistence layers. (Completado para los endpoints modificados).
    *   **[x] 1.2.4:** Update all services and API endpoints (including `TradingEngineService` for credential fetching) to operate based on the authenticated user context. (Verificado que TradingEngineService y CredentialService usan user_id propagado desde los endpoints API autenticados).

### Task 1.3: (Critical Issue 6) Incorrect Service Dependency Initialization in `CredentialService`
**Original Title:** Incorrect Service Dependency Initialization in `CredentialService`.
*   **Description:** `CredentialService` initializes its own instances of `BinanceAdapter` and `SupabasePersistenceService` instead of receiving them via constructor injection.
*   **Subtasks:**
    *   **[x] 1.3.1:** Modify `CredentialService` constructor in `src/ultibot_backend/services/credential_service.py` to accept `BinanceAdapter` and `SupabasePersistenceService` instances.
    *   **[x] 1.3.2:** Update `src/ultibot_backend/main.py` and any other instantiation points of `CredentialService` to inject these dependencies.

### Task 1.4: (Critical Issue 7) Real Trade Exit Logic Potentially Unsafe if OCO Fails
**Original Title:** Real Trade Exit Logic Potentially Unsafe if OCO Fails.
*   **Description:** Fallback logic for real trade exits if OCO orders fail may not execute market orders to prevent losses.
*   **Subtasks:**
    *   **[x] 1.4.1:** Enhance `monitor_and_manage_real_trade_exit` in `src/ultibot_backend/services/trading_engine_service.py` to actively execute market sell/buy orders via `OrderExecutionService` if a non-OCO managed real trade hits its TSL or TP based on live price monitoring. (Verified existing logic addresses this)
    *   **[x] 1.4.2:** Implement robust error reporting and alerts if OCO placement fails, prompting manual intervention if necessary. (Infrastructure for error capture, trade update, and notification service integration added to `TradingEngineService.create_trade_from_decision`. Actual OCO placement logic and its specific error handling in lower services like `OrderExecutionService` or `BinanceAdapter` still pending full review/implementation if not already present).

### Task 1.5: (Critical Issue 8) Unregistered `trading.py` Router in Backend
**Original Title:** Unregistered `trading.py` Router in Backend.
*   **Description:** The API router in `src/ultibot_backend/api/v1/endpoints/trading.py` (for confirming real trades) is not registered in `main.py`.
*   **Subtasks:**
    *   **[x] 1.5.1:** Add `app.include_router(trading.router, prefix="/api/v1", tags=["trading"])` (or similar) to `src/ultibot_backend/main.py` to activate the trading endpoints. (Verified as already implemented in `src/ultibot_backend/main.py`)

### Task 1.6: (Relevant Issue 2) Lack of Granular Authorization for API Endpoints
**Original Title:** Lack of Granular Authorization for API Endpoints.
*   **Description:** No robust mechanism ensures a user can only access/modify their own resources.
*   **Subtasks:**
    *   **[x] 1.6.1:** After implementing user authentication (Task 1.2.1), implement resource-based authorization checks in API endpoints and services. (Endpoints revisados: `config.py`, `notifications.py`, `reports.py`, `portfolio.py`, `trades.py`, `performance.py`, `opportunities.py`, `strategies.py`, `trading.py`, `market_data.py`, `capital_management.py`. Se añadió verificación de propiedad de oportunidad en `trading.py`.)
    *   **[ ] 1.6.2:** Ensure `user_id` from the authentication context is used to filter database queries for user-specific data (configurations, notifications, portfolio, etc.).

### Task 1.7: (Relevant Issue 5) Default Supabase Credentials in `app_config.py`
**Original Title:** Default Supabase Credentials in `app_config.py`.
*   **Description:** `app_config.py` contains default placeholder values for Supabase credentials.
*   **Subtasks:**
    *   **[x] 1.7.1:** Remove default placeholder values for sensitive keys (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, etc.) from `src/ultibot_backend/app_config.py`.
    *   **[x] 1.7.2:** Implement a configuration error at startup if these essential credentials are not found in the environment (loaded from `.env`). (Achieved by removing defaults; Pydantic will raise ValidationError if not set).

### Task 1.8: (Relevant Issue 6) Manual Loading of `CREDENTIAL_ENCRYPTION_KEY` in Backend `main.py`
**Original Title:** Manual Loading of `CREDENTIAL_ENCRYPTION_KEY` in Backend `main.py`.
*   **Description:** Backend `main.py` manually reads `CREDENTIAL_ENCRYPTION_KEY` from `.env`.
*   **Subtasks:**
    *   **[x] 1.8.1:** Investigate and ensure `pydantic-settings` reliably loads `CREDENTIAL_ENCRYPTION_KEY`. (Verified: `settings.CREDENTIAL_ENCRYPTION_KEY` in `main.py` confirms loading via `pydantic-settings`).
    *   **[x] 1.8.2:** If reliable loading via `pydantic-settings` is confirmed, remove the manual loading code from `src/ultibot_backend/main.py`. If manual loading is necessary, document the reason clearly. (No manual loading code found in `main.py` for this variable; it's accessed via `settings` object).

### Task 1.9: Preparación y Verificación Inicial de la Interfaz de Usuario (UI)
*   **Description:** Asegurar que la UI pueda ser lanzada y que las dependencias estén correctamente instaladas como prerrequisito para la verificación completa del flujo de autenticación/autorización y otras pruebas funcionales.
*   **Subtasks:**
    *   **[x] 1.9.1:** Resolver problemas de dependencia de la UI.
        *   **[x] 1.9.1.1:** Descomentar `PyQt5` y `qdarkstyle` en `pyproject.toml`.
        *   **[x] 1.9.1.2:** Resolver problemas de instalación/conflicto para `PyQt5` y `qdarkstyle`. (Instalados mediante `poetry run pip install`)
    *   **[ ] 1.9.2:** Verificar la funcionalidad completa del flujo de autenticación y autorización.
        *   **[x] 1.9.2.1:** Refactorizar `src/ultibot_ui/dialogs/login_dialog.py` para utilizar el `ApiWorker` real, conectar las señales correctamente y resolver errores de análisis estático, preparando el terreno para las pruebas de UI.
        *   **[ ] 1.9.2.2:** Una vez que la UI pueda ser lanzada, realizar pruebas manuales exhaustivas del flujo de registro, login, acceso a endpoints protegidos, y operaciones CRUD sobre recursos específicos del usuario.
        *   **[ ] 1.9.2.3:** Asegurar que un usuario no pueda acceder ni modificar datos de otro usuario.
        *   **[ ] 1.9.2.3:** (Opcional) Considerar la creación de pruebas de integración si el tiempo lo permite.

### Task 1.10: Resolver Error de Importación Circular en el Frontend
*   **Description:** Al iniciar, el frontend fallaba con un `ImportError` debido a una dependencia circular entre `src/ultibot_ui/main.py` y `src/ultibot_ui/dialogs/login_dialog.py`.
*   **Subtasks:**
    *   **[x] 1.10.1:** Identificar la causa del ciclo de importación (la clase `ApiWorker` definida en `main.py` e importada en `login_dialog.py`).
    *   **[x] 1.10.2:** Crear un nuevo módulo `src/ultibot_ui/workers.py` para alojar la clase `ApiWorker`, rompiendo la dependencia directa.
    *   **[x] 1.10.3:** Refactorizar `src/ultibot_ui/main.py` y `src/ultibot_ui/dialogs/login_dialog.py` para importar `ApiWorker` desde el nuevo módulo `workers.py`.
    *   **[x] 1.10.4:** Verificar que la aplicación se inicia correctamente sin el `ImportError` utilizando el script `run_frontend_with_backend.bat`.

### Task 1.11: Implementar Botón de Login Rápido para Administrador
*   **Description:** A petición del usuario, se ha añadido un botón para saltar el ingreso manual de credenciales, utilizando un perfil de administrador preconfigurado.
*   **Subtasks:**
    *   **[x] 1.11.1:** Añadir variables `ADMIN_EMAIL` y `ADMIN_PASSWORD` al archivo de entorno `.env`.
    *   **[x] 1.11.2:** Modificar `src/ultibot_ui/dialogs/login_dialog.py` para añadir un botón "Admin Login".
    *   **[x] 1.11.3:** Implementar la lógica para que el botón "Admin Login" lea las credenciales del `.env`, las inserte en los campos de texto y proceda con el login automático.

---

## Phase 2: Implement Core Missing Functionality

This phase addresses unimplemented services and missing API functionalities that are crucial for the application's core purpose.

### Task 2.1: (Critical Issue 2) `StrategyService` is Unimplemented
**Original Title:** `StrategyService` is Unimplemented.
*   **Description:** `src/ultibot_backend/services/strategy_service.py` is a stub. No backend logic for managing trading strategies exists.
*   **Subtasks:**
    *   **2.1.1:** Design and implement `StrategyService` with CRUD operations for `TradingStrategyConfig` objects (defined in `src/ultibot_backend/shared/data_types.py`).
    *   **2.1.2:** Define how strategies are stored (e.g., dedicated table vs. JSON in `UserConfiguration`). If a dedicated table is chosen, update `PersistenceService` accordingly. (Note: Currently stored in `UserConfiguration`).
    *   **2.1.3:** Integrate `StrategyService` with `AIOrchestratorService` to provide strategy context/prompts to the LLM.
    *   **2.1.4:** Develop corresponding API endpoints in the backend for managing strategies through the `StrategyService`.

### Task 2.2: (Critical Issue 3) UI `APIClient` is Missing Key Methods for Data Fetching
**Original Title:** UI `APIClient` is Missing Key Methods for Data Fetching.
*   **Description:** `src/ultibot_ui/services/api_client.py` lacks methods needed by UI components for fetching various data types.
*   **Subtasks:**
    *   **2.2.1:** Implement `get_market_historical_data` (for klines) in `APIClient`.
    *   **2.2.2:** Implement `get_tickers_data` in `APIClient`.
    *   **2.2.3:** Implement `get_portfolio_summary` in `APIClient`.
    *   **2.2.4:** Implement `get_notification_history` in `APIClient`.
    *   **2.2.5:** Ensure corresponding backend API endpoints exist and are functional for these new `APIClient` methods.

### Task 2.3: (Critical Issue 4 & Specific Investigation) Strategy Display Functionality is Missing in UI
**Original Title:** Strategy Display Functionality is Missing in UI.
*   **Description:** The "Strategies" section in the UI is a placeholder. No components or logic exist to display strategies. This is also highlighted in the "Strategy Export to Interface" specific investigation.
*   **Subtasks:**
    *   **2.3.1:** Design and implement a new UI view (e.g., `StrategiesView.py`) and associated widgets for displaying strategy configurations.
    *   **2.3.2:** This new view should use a UI service (e.g., `UIConfigService` or a new `UIStrategyService`) that utilizes `APIClient` to fetch strategy data (likely via `APIClient.get_user_configuration()` or new strategy-specific endpoints from Task 2.1.4).
    *   **2.3.3:** Update `src/ultibot_ui/windows/main_window.py` to use the new `StrategiesView` instead of the current `QLabel` placeholder.

---

## Phase 3: Enhance Data Management and Flow

This phase is dedicated to improving how market data, trading data, and configurations are stored, managed, and accessed throughout the application.

### Task 3.1: (Specific Investigation) Implement Persistent Storage for Granular Market Data
**Original Title:** Derived from "Specific Investigation Findings - Market Data Recording and LLM Opportunity Generation" - No persistent storage of granular market data.
*   **Description:** Granular market data (klines, tickers, WebSocket stream data) is not persistently stored, which is a critical gap for backtesting, AI model training, and providing historical context to the LLM.
*   **Subtasks:**
    *   **3.1.1:** Design a database schema for storing time-series market data (klines, tickers, trades).
    *   **3.1.2:** Implement methods in `PersistenceService` for saving and retrieving this granular market data.
    *   **3.1.3:** Modify `MarketDataService` to use `PersistenceService` to store fetched/streamed market data.
    *   **3.1.4:** Update `AIOrchestratorService` and any other relevant services to leverage this persistent market data store for richer context, reducing direct API calls where possible.

### Task 3.2: (Optimizable Issue 3) Persistence of Paper Trading Asset Holdings
**Original Title:** Persistence of Paper Trading Asset Holdings.
*   **Description:** Paper trading asset holdings are in-memory and lost on application restart.
*   **Subtasks:**
    *   **3.2.1:** Design a schema for storing paper trading asset holdings (e.g., extend `UserConfiguration` with a new field or create a dedicated table).
    *   **3.2.2:** Update `PortfolioService` (`src/ultibot_backend/services/portfolio_service.py`) to load and save these holdings via `PersistenceService`.
    *   **3.2.3:** Ensure `PaperOrderExecutionService` correctly updates these persisted holdings.

### Task 3.3: (Relevant Issue 4) UI `TradingModeService` and Backend `UserConfiguration.paperTradingActive` Synchronization
**Original Title:** UI `TradingModeService` and Backend `UserConfiguration.paperTradingActive`.
*   **Description:** Unclear synchronization between UI's local trading mode and backend's `paperTradingActive` flag.
*   **Subtasks:**
    *   **3.3.1:** Clarify and document the intended relationship: should UI mode selection update the backend persisted state?
    *   **3.3.2:** If UI selection is authoritative, ensure `TradingModeService` in `src/ultibot_ui/services/trading_mode_service.py` calls the `APIClient` to update `UserConfiguration.paperTradingActive` on the backend when the mode is switched. (Note: `SettingsView` might already do this; ensure consistency with the global service).
    *   **3.3.3:** Ensure backend services like `TradingEngineService` consistently use the `paperTradingActive` flag from the persisted `UserConfiguration`.

---

## Phase 4: Improve Code Quality, Consistency, and Robustness

This phase focuses on refactoring and optimizing existing code for better clarity, maintainability, efficiency, and error handling.

### Task 4.1: (Optimizable Issue 1) Incorrect Service Dependency Initialization in Some API Routers
**Original Title:** Incorrect Service Dependency Initialization in Some API Routers.
*   **Description:** Some API routers (`binance_status.py`, `notifications.py`) re-initialize services already available globally.
*   **Subtasks:**
    *   **4.1.1:** Refactor routers in `src/ultibot_backend/api/v1/endpoints/binance_status.py` and `src/ultibot_backend/api/v1/endpoints/notifications.py` to use FastAPI's `Depends` with the globally initialized service instances from `main.py`.

### Task 4.2: (Optimizable Issue 2) Excessive Business Logic in `opportunities.py` API Router
**Original Title:** Excessive Business Logic in `opportunities.py` API Router.
*   **Description:** The `get_real_trading_candidates` endpoint in `src/ultibot_backend/api/v1/endpoints/opportunities.py` contains significant business logic.
*   **Subtasks:**
    *   **4.2.1:** Identify and move the business logic (fetching user config, checking trading mode, querying trade/opportunity statuses) from the `opportunities.py` router into appropriate services (e.g., `TradingEngineService`, `AIOrchestratorService`, or `ConfigService`).
    *   **4.2.2:** Ensure the router primarily handles request/response validation and delegation to these services.

### Task 4.3: (Optimizable Issue 4) Manual Data Mapping in `PersistenceService`
**Original Title:** Manual Data Mapping in `PersistenceService`.
*   **Description:** `SupabasePersistenceService` manually maps database snake_case column names to Pydantic model field names.
*   **Subtasks:**
    *   **4.3.1:** Review Pydantic models involved in database interaction (e.g., `OpenTrade`, `Opportunity`).
    *   **4.3.2:** Utilize Pydantic's aliasing features (e.g., `AliasGenerator`, `model_config = {"populate_by_name": True}` with field aliases like `Field(alias='db_column_name')`) in these models to handle snake_case to camelCase/PascalCase conversion automatically.
    *   **4.3.3:** Update `SupabasePersistenceService` methods (e.g., `get_open_paper_trades`, `get_opportunity_by_id`) to rely on this automatic mapping, removing manual dictionary key conversions.

### Task 4.4: (Optimizable Issue 5) Ambiguous Market Data Fetching Logic in `MobulaAdapter`
**Original Title:** Ambiguous Market Data Fetching Logic in `MobulaAdapter`.
*   **Description:** `MobulaAdapter.get_market_data` has complex logic for trying different endpoints and parsing, which could be brittle.
*   **Subtasks:**
    *   **4.4.1:** Review the Mobula API documentation to clarify the exact endpoints and expected response structures for fetching market data by symbol.
    *   **4.4.2:** Simplify the fetching and parsing logic in `src/ultibot_backend/adapters/mobula_adapter.py` based on documented API behavior to improve robustness.

### Task 4.5: (Optimizable Issue 6) LLM Output Parsing Fallback is Brittle
**Original Title:** LLM Output Parsing Fallback is Brittle.
*   **Description:** `AIOrchestratorService.analyze_opportunity_with_ai` falls back to regex if JSON parsing of LLM output fails.
*   **Subtasks:**
    *   **4.5.1:** Refine prompts provided to the LLM to more strictly enforce structured JSON output.
    *   **4.5.2:** Investigate and implement LangChain's structured output parsers (e.g., `PydanticOutputParser` or `StructuredOutputParser`) in `src/ultibot_backend/services/ai_orchestrator_service.py`.
    *   **4.5.3:** Improve error handling for cases where structured output still cannot be obtained, avoiding reliance on fragile regex.

### Task 4.6: (Relevant Issue 1) Inconsistent API Endpoint Path for Opportunities Router
**Original Title:** Inconsistent API Endpoint Path for Opportunities Router.
*   **Description:** `opportunities.router` is registered at application root, but UI calls it via `/api/v1/opportunities/...`.
*   **Subtasks:**
    *   **4.6.1:** Standardize router registration in `src/ultibot_backend/main.py`. Change the registration of `opportunities.router` to include the `/api/v1` prefix (e.g., `app.include_router(opportunities.router, prefix="/api/v1", tags=["opportunities"])`).
    *   **4.6.2:** Verify that `src/ultibot_ui/services/api_client.py` calls align with this standardized path.

### Task 4.7: (Relevant Issue 3) Test Helper Methods in Production `PersistenceService`
**Original Title:** Test Helper Methods in Production `PersistenceService`.
*   **Description:** `SupabasePersistenceService` contains test-specific helper methods.
*   **Subtasks:**
    *   **4.7.1:** Identify all methods prefixed with `execute_test_...` or `fetchrow_test_...` in `src/ultibot_backend/adapters/persistence_service.py`.
    *   **4.7.2:** Move these test helper methods to a separate test utility module within the test directory structure or a test-specific subclass not part of production code.

---

## Phase 5: Address UI-Backend Integration and Feature Gaps

This phase handles specific UI interactions, WebSocket management, and ensures that the UI correctly reflects backend states and data.

### Task 5.1: (Relevant Issue 7) WebSocket Error Handling in `BinanceAdapter`
**Original Title:** WebSocket Error Handling in `BinanceAdapter`.
*   **Description:** `BinanceAdapter`'s WebSocket error handling primarily prints errors and doesn't robustly propagate them for higher-level reaction.
*   **Subtasks:**
    *   **5.1.1:** Implement a more robust error handling and health-checking mechanism for WebSocket connections within `src/ultibot_backend/adapters/binance_adapter.py`. This could involve status flags or callback mechanisms for persistent failures.
    *   **5.1.2:** Allow `MarketDataService` or other consumers (including UI-facing data services via the backend API) to be notified of persistent WebSocket failures.
    *   **5.1.3:** Design mechanisms for UI components to react to these notifications (e.g., display warnings, attempt reconnection via backend).

---

This structured plan should provide a clear path for addressing the audit findings.
