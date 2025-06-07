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

## Phase 2: Implement Core Application Functionality

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

## Phase 3: Enhance and Optimize Core Systems

This phase is dedicated to improving the quality, performance, and robustness of existing features.

### Task 3.1: Persistence of Paper Trading Asset Holdings
*   **Description:** Paper trading asset holdings are in-memory and lost on application restart.
*   **Subtasks:**
    *   **[ ] 3.1.1:** Design a schema for storing paper trading asset holdings (e.g., extend `UserConfiguration` or create a dedicated table).
    *   **[ ] 3.1.2:** Update `PortfolioService` (`src/ultibot_backend/services/portfolio_service.py`) to load and save these holdings via `PersistenceService`.

### Task 3.2: [COMPLETADO] Inconsistent API Endpoint Paths
*   **Status:** Todos los enrutadores del backend han sido estandarizados bajo el prefijo `/api/v1`. **COMPLETADO**.

### Task 3.3: [COMPLETADO] Corregir Errores 404 y 422 en la UI
*   **Status:** Se han corregido las inconsistencias en `api_client.py` y el formato de fechas, resolviendo los errores de comunicación entre UI y backend. **COMPLETADO**.

### Task 3.4: [COMPLETADO] Estabilización Final del Backend y Modelos de Datos
*   **Status:** Se han resuelto los errores en cascada de Pylance y de tiempo de ejecución, logrando un arranque estable. **COMPLETADO**.

### Task 3.5: LLM Output Parsing Fallback is Brittle
*   **Description:** `AIOrchestratorService` falls back to regex if JSON parsing of LLM output fails.
*   **Subtasks:**
    *   **[ ] 3.5.1:** Refine prompts provided to the Gemini LLM to more strictly enforce structured JSON output.
    *   **[ ] 3.5.2:** Implement LangChain's structured output parsers (e.g., `PydanticOutputParser`) in `src/ultibot_backend/services/ai_orchestrator_service.py` to ensure reliable parsing.

---

This focused plan provides a clear path for deploying a powerful, AI-driven investment tool.
