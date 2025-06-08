# UltiBotInversiones - Focused Action Plan (AUDIT_TASK_JULES.md)

## Introduction

This document outlines a structured action plan based on the refocused findings of the `AUDIT_REPORT.md`. It prioritizes tasks to accelerate the development of UltiBotInversiones as a rapid-deployment, single-user application focused on AI-driven opportunity generation.

---

## Phase 1: [COMPLETED] Address Critical Architectural and Security Flaws

This phase, focused on resolving fundamental architectural problems, is now considered complete. The application has been stabilized with a clear client-server separation and has been simplified to a single-user model.

### Task 1.0: [COMPLETED] Eliminar Sistema de Autenticación y Login
*   **Status:** Completed. The application now operates under a consistent, single-user model using a `FIXED_USER_ID`.

### Task 1.1: [COMPLETED] UI Application Incorrectly Initializes and Uses Backend Services
*   **Status:** Completed. The UI is now a pure client using the `APIClient`.

### Task 1.2: [ANULADO] `FIXED_USER_ID` Hardcoding and Inconsistent Usage
*   **Status:** Anulado por decisión estratégica (Task 1.0).

### Task 1.3: [COMPLETED] Incorrect Service Dependency Initialization in `CredentialService`
*   **Status:** Completed. `CredentialService` now uses dependency injection.

### Task 1.4: [COMPLETED] Real Trade Exit Logic Potentially Unsafe if OCO Fails
*   **Status:** Completed. Logic has been verified and enhanced.

### Task 1.5: [COMPLETED] Unregistered `trading.py` Router in Backend
*   **Status:** Completed. The router is correctly registered.

### Task 1.6: [ANULADO] Lack of Granular Authorization for API Endpoints
*   **Status:** Anulado por decisión estratégica (Task 1.0).

### Task 1.7: [COMPLETED] Default Supabase Credentials in `app_config.py`
*   **Status:** Completed. Default placeholders have been removed.

### Task 1.8: [COMPLETED] Manual Loading of `CREDENTIAL_ENCRYPTION_KEY`
*   **Status:** Completed. Loading is handled correctly by `pydantic-settings`.

### Task 1.9: [COMPLETED] Preparación y Verificación Inicial de la Interfaz de Usuario (UI)
*   **Status:** Completed. UI dependencies are resolved.

### Task 1.10: [COMPLETED] Resolver Error de Importación Circular en el Frontend
*   **Status:** Completed. Circular dependency has been resolved.

### Task 1.11: [ANULADO] Implementar Botón de Login Rápido para Administrador
*   **Status:** Anulado por decisión estratégica (Task 1.0).

### Task 1.12: [COMPLETED] Corregir el Despliegue del Backend
*   **Status:** Completed. The backend now launches correctly as an ASGI server.

### Task 1.13: [COMPLETED] Estabilizar el Arranque del Backend
*   **Status:** Completed. Dependency injection and startup errors have been resolved.

### Task 1.14: [COMPLETED] Corregir el Despliegue del Frontend
*   **Status:** Completed. Se han resuelto múltiples errores en cascada que impedían el despliegue de la UI. Se corrigieron `ImportError` en `ui_market_data_service.py` y `ui_strategy_service.py` por nombres de clase incorrectos. Se solucionó un `RuntimeWarning` al llamar una corutina de forma síncrona en `main_window.py` mediante el uso de un `ApiWorker` en un hilo separado. Finalmente, se añadió un método `cleanup` faltante en `PaperTradingReportWidget` para prevenir un `AttributeError` al cerrar la aplicación. La UI ahora se despliega y cierra de forma estable.

---

## Phase 2: [COMPLETED] Implement Core Application Functionality

This phase focuses on building out the primary features of the application, now that the architecture is stable.

### Task 2.1: [COMPLETED] Implementar Almacenamiento Persistente de Datos de Mercado
*   **Description:** The system now has a mechanism to persistently store granular market data (klines, tickers). This is a critical step for enabling the Gemini AI to perform meaningful analysis.
*   **Subtasks:**
    *   **[x] 2.1.1:** Design a robust database schema for storing time-series market data (e.g., a `market_data` table with columns for `symbol`, `timestamp`, `open`, `high`, `low`, `close`, `volume`).
    *   **[x] 2.1.2:** Implement methods in `src/ultibot_backend/adapters/persistence_service.py` for efficiently writing and reading this market data.
    *   **[x] 2.1.3:** Modify `src/ultibot_backend/services/market_data_service.py` to use the new persistence methods, ensuring that all fetched or streamed data is saved to the database.
    *   **[x] 2.1.4:** Refactor `src/ultibot_backend/services/ai_orchestrator_service.py` to query this internal data store, providing the Gemini LLM with rich, immediate historical context for its analysis instead of relying on fresh, limited API calls.

### Task 2.2: [COMPLETADO] `StrategyService` is Unimplemented
*   **Status:** La auditoría original era incorrecta. El servicio está implementado y verificado. **COMPLETADO**.

### Task 2.3: [COMPLETADO] UI `APIClient` is Missing Key Methods for Data Fetching
*   **Status:** Los métodos necesarios del `APIClient` han sido implementados y los endpoints del backend verificados. **COMPLETADO**.

### Task 2.4: [COMPLETED] Strategy Display Functionality is Missing in UI
*   **Description:** The "Strategies" section in the UI is a placeholder. No components or logic exist to display strategies.
*   **Subtasks:**
    *   **[x] 2.4.1:** Design and implement a new UI view (`src/ultibot_ui/views/strategies_view.py`) and associated widgets for displaying strategy configurations.
    *   **[x] 2.4.2:** The new view must use the `APIClient` to fetch strategy data from the backend.
    *   **[x] 2.4.3:** Update `src/ultibot_ui/windows/main_window.py` to use the new `StrategiesView` instead of the current `QLabel` placeholder.

---

## Phase 3: [COMPLETED] Enhance and Optimize Core Systems

This phase is dedicated to improving the quality, performance, and robustness of existing features.

### Task 3.1: [COMPLETED] Persistence of Paper Trading Asset Holdings
*   **Description:** Paper trading asset holdings are in-memory and lost on application restart. The logic for loading and saving holdings via `PortfolioService` and `PersistenceService` has been implemented.
*   **Subtasks:**
    *   **[x] 3.1.1:** Design a schema for storing paper trading asset holdings (e.g., extend `UserConfiguration` or create a dedicated table).
    *   **[x] 3.1.2:** Update `PortfolioService` (`src/ultibot_backend/services/portfolio_service.py`) to load and save these holdings via `PersistenceService`.

### Task 3.2: [COMPLETADO] Inconsistent API Endpoint Paths
*   **Status:** Todos los enrutadores del backend han sido estandarizados bajo el prefijo `/api/v1`. **COMPLETADO**.

### Task 3.3: [COMPLETADO] Corregir Errores 404 y 422 en la UI
*   **Status:** Se han corregido las inconsistencias en `api_client.py` y el formato de fechas, resolviendo los errores de comunicación entre UI y backend. **COMPLETADO**.

### Task 3.4: [COMPLETADO] Estabilización Final del Backend y Modelos de Datos
*   **Status:** Se han resuelto los errores en cascada de Pylance y de tiempo de ejecución, logrando un arranque estable. **COMPLETADO**.

### Task 3.5: [COMPLETED] LLM Output Parsing Fallback is Brittle
*   **Description:** `AIOrchestratorService` falls back to regex if JSON parsing of LLM output fails. This has been replaced with a robust, structured output mechanism using LangChain.
*   **Subtasks:**
    *   **[x] 3.5.1:** Refine prompts provided to the Gemini LLM to more strictly enforce structured JSON output.
    *   **[x] 3.5.2:** Implement LangChain's structured output parsers (e.g., `PydanticOutputParser` and `OutputFixingParser`) in `src/ultibot_backend/services/ai_orchestrator_service.py` to ensure reliable parsing.

---

## Phase 4: [COMPLETED] Deployment and Stability Fixes

This phase addresses issues discovered during final deployment and testing, ensuring the application runs like a "reloj atómico óptico".

### Task 4.1: [COMPLETED] Backend `ImportError` on `OutputFixingParser`
*   **Description:** The backend failed to start due to an `ImportError` for `OutputFixingParser`, which was incorrectly imported from `langchain_core`.
*   **Solution:** The import path was corrected from `langchain_core.output_parsers` to `langchain.output_parsers`. This resolved the startup failure.

### Task 4.2: [COMPLETED] Frontend Fails to Connect to Backend (`All connection attempts failed`)
*   **Description:** The frontend UI failed to launch, showing a connection error. The initial hypothesis was a race condition.
*   **Attempt 1 (Failed):** The startup delay in `run_frontend_with_backend.bat` was increased from 15 to 25 seconds. The error persisted.
*   **Solution:** The root cause was not timing but a likely name resolution issue. The API client in `src/ultibot_ui/main.py` was changed to connect to `127.0.0.1` instead of `localhost`, which resolved the connection error.

### Task 4.3: [COMPLETED] Backend `ImportError` on `get_app_config`
*   **Description:** The backend failed to start due to an `ImportError` for `get_app_config` in `ai_orchestrator_service.py`.
*   **Solution:** The import was corrected to use the global `settings` instance from `app_config`. Subsequent Pylance errors were also resolved, stabilizing the service.

### Task 4.4: [COMPLETED] Frontend Renders an Empty Window
*   **Description:** After fixing the connection and backend startup issues, the frontend launches but displays an empty window. The logs show a clean startup and shutdown sequence, suggesting a layout or rendering issue rather than a crash.
*   **Solution:** The issue was hypothesized to be related to Qt layout management. `MainWindow` in `src/ultibot_ui/windows/main_window.py` was refactored to ensure the central widget and its layout are correctly configured and have a minimum size.

### Task 4.5: [COMPLETED] Verify UI Rendering
*   **Description:** Despite the layout fixes, the UI still appeared empty. The logs are clean, which points to a subtle rendering or event loop issue. A visual confirmation is needed.
*   **Solution:** A screenshot confirmed the UI was rendering correctly, but the application was closing immediately due to leftover debugging code. The `QTimer` and `app.quit()` call in `src/ultibot_ui/main.py` were removed, allowing the application to run normally.
*   **Subtasks:**
    *   **[x] 4.5.1:** Modify `src/ultibot_ui/main.py` to programmatically take a screenshot of the main window after a short delay (e.g., 5 seconds) and save it to a file (e.g., `logs/ui_screenshot.png`).
    *   **[x] 4.5.2:** Execute `run_frontend_with_backend.bat`.
    *   **[x] 4.5.3:** Analyze the resulting screenshot to determine the true state of the UI.

### Task 4.6: [COMPLETED] Restore and Stabilize `main.py`
*   **Description:** The main entry point of the UI, `src/ultibot_ui/main.py`, was restored to its functional version after a deep debugging session. The restoration introduced several Pylance errors due to outdated references.
*   **Solution:** The file was systematically refactored to align with the current architecture. This involved:
    *   Correcting the `APIClient` import to `UltiBotAPIClient`.
    *   Replacing the obsolete `InitializationWorker` with the generic `ApiWorker`.
    *   Implementing a new `AppController` class to manage the asynchronous initialization flow, ensuring the `user_id` is fetched *before* the `MainWindow` is created.
    *   Fixing all subsequent Pylance errors related to missing arguments and incorrect method calls.
*   **Status:** The `main.py` file is now stable, free of static errors, and correctly handles the application's startup sequence.

---

## Phase 5: [COMPLETED] UI/UX Overhaul

This phase focuses on transforming the visual appearance of the application from a standard desktop look to a modern, professional financial dashboard, based on `UI_ejemplos/Ejemplo_3.png`.

### Task 5.1: [COMPLETED] Implement a Modern UI Theme
*   **Description:** The current UI uses default Qt widgets. A complete visual overhaul is needed to match the target design.
*   **Subtasks:**
    *   **[x] 5.1.1:** Create a global stylesheet (`src/ultibot_ui/assets/style.qss`) that defines the dark theme, color palette (dark blues, grays, accent colors), fonts, and base widget styles (buttons, labels, etc.).
    *   **[x] 5.1.2:** Load and apply this stylesheet in `src/ultibot_ui/main.py` to ensure a consistent look and feel across the entire application.
    *   **[x] 5.1.3:** Refactor existing views and widgets to use `QFrame`s with rounded corners and shadows to create the "card" effect seen in the target design.
    *   **[x] 5.1.4:** Replace default widgets with custom-styled versions where necessary (e.g., custom buttons, styled tables).
    *   **[x] 5.1.5:** Integrate a modern icon set (e.g., Font Awesome, Material Design Icons) to replace text-based navigation and actions where appropriate.

---

This focused plan provides a clear path for deploying a powerful, AI-driven investment tool.
