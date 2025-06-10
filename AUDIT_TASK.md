### INFORME DE ESTADO Y PLAN DE ACCIÓN - 2025-06-09 18:58:44

**ESTADO ACTUAL:**
* Fallo persistente al eliminar el entorno virtual `.venv` debido a archivos bloqueados por procesos externos.

**1. OBSERVACIONES (Resultados de FASE 1):**
* El comando `poetry install` falló con "Unable to find installation candidates for propcache (0.3.2)".
* Se intentó regenerar `poetry.lock` y actualizar `propcache` sin éxito.
* Se intentó eliminar el entorno virtual `.venv` con `rm -r .venv` y `Remove-Item -Recurse -Force .venv`, ambos fallaron con errores de "Acceso denegado" y "El proceso no tiene acceso al archivo porque está siendo utilizado por otro proceso".
* Esto indica que hay procesos activos que están utilizando archivos dentro del entorno virtual, impidiendo su eliminación.

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**
* La causa raíz de los problemas de instalación y la imposibilidad de eliminar el entorno virtual es la existencia de procesos activos que mantienen bloqueados los archivos dentro de `.venv`. Hasta que estos procesos no sean terminados, no se podrá limpiar y recrear el entorno para una instalación exitosa.

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**
| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| N/A | **Intervención manual del usuario requerida.** | Los archivos dentro del entorno virtual `.venv` están bloqueados por procesos externos. Es necesario que el usuario identifique y cierre manualmente cualquier aplicación o terminal que esté utilizando archivos dentro de `C:\Users\zamor\UltiBotInversiones\.venv`. Esto incluye cualquier terminal de Python, servidores en ejecución, o incluso el propio VS Code si tiene el entorno activado. Una vez que los procesos estén cerrados, se podrá eliminar el directorio `.venv` y proceder con una instalación limpia. |

**4. RIESGOS POTENCIALES:**
* Si los procesos que bloquean los archivos no se cierran correctamente, no será posible eliminar el entorno virtual, lo que impedirá cualquier progreso en la instalación de dependencias.
* La identificación y cierre manual de procesos puede ser compleja para el usuario si no está familiarizado con la gestión de procesos en Windows.

**5. SOLICITUD:**
* **PAUSA** Espero la confirmación del usuario de que ha cerrado todos los procesos que puedan estar utilizando el entorno virtual `.venv`. Una vez confirmada la liberación de los archivos, procederé a intentar eliminar el directorio `.venv` nuevamente y luego a recrear el entorno e instalar las dependencias.
**Hipótesis Central:** El fallo de inicio de la aplicación se debe a un conflicto en el `ApiWorker` de la UI, que intenta ejecutar una tarea en el bucle de eventos `asyncio` principal que ya está en uso, causando un `RuntimeError` silencioso. El plan aborda esta causa raíz y, simultáneamente, implementa mejoras de robustez clave en el backend.

**Archivos a Modificar:**
1.  `src/ultibot_ui/workers.py`
2.  `src/ultibot_backend/adapters/binance_adapter.py`
3.  `src/ultibot_backend/services/ai_orchestrator_service.py`
4.  `src/ultibot_backend/services/strategy_service.py`

**Justificación:** Este enfoque integral resuelve el bloqueo crítico del frontend y adelanta tareas de robustecimiento del backend, optimizando el tiempo de desarrollo y asegurando que, una vez que la UI inicie, se comunique con un backend más estable y observable.

---

## Phase 6: [PENDING] Final Integration and Data Flow

### Task 6.1: [PENDING] Stabilize Asynchronous UI Updates
*   **Status:** PENDING

### Task 6.2: [PENDING] Refactorización de Inyección de Dependencias en UI
*   **Status:** PENDING

---

## Phase 7: [IN PROGRESS] UI Data Rendering and Final Polish

This phase focuses on ensuring that the data fetched from the backend is correctly displayed and updated in the corresponding UI widgets. The core infrastructure is in place; now we connect the data to the views.

### Task 7.1: [PENDING] Implement Data Rendering in PortfolioView
*   **Description:** Connect the `ApiWorker` responsible for fetching the portfolio snapshot to the `PortfolioView` to display assets, quantities, and P&L.
*   **Subtasks:**
    *   **[ ] 7.1.1:** In `PortfolioView`, create a slot method (e.g., `_on_portfolio_update(data)`).
    *   **[ ] 7.1.2:** Connect the `finished` signal of the `ApiWorker` that calls `get_portfolio_snapshot` to this new slot.
    *   **[ ] 7.1.3:** (Pseudocode) Implement the logic within `_on_portfolio_update` to clear the existing portfolio table and populate it with the new data received. Update summary labels (Total Value, P&L, etc.).

### Task 7.2: [PENDING] Implement Data Rendering in OpportunitiesView
*   **Description:** Connect the worker that fetches AI-generated opportunities to the `OpportunitiesView` to display them in a list or table.
*   **Subtasks:**
    *   **[ ] 7.2.1:** In `OpportunitiesView`, create a slot method (e.g., `_on_opportunities_received(data)`).
    *   **[ ] 7.2.2:** Connect the `ApiWorker`'s `finished` signal to this slot.
    *   **[ ] 7.2.3:** (Pseudocode) Implement the logic to parse the opportunities and add them as items to a `QListWidget` or rows to a `QTableWidget`.

### Task 7.3: [PENDING] Implement Chart Updates in ChartWidget
*   **Description:** Ensure the `ChartWidget` correctly receives and plots OHLCV data.
*   **Subtasks:**
    *   **[ ] 7.3.1:** In `ChartWidget`, create a slot method (e.g., `_on_chart_data_received(data)`).
    *   **[ ] 7.3.2:** Connect the `ApiWorker` that calls `get_ohlcv_data` to this slot.
    *   **[ ] 7.3.3:** (Pseudocode) Implement the logic to process the OHLCV data and update the candlestick series of the chart.

### Task 7.4: [PENDING] Implement Strategy Display in StrategiesView
*   **Description:** Connect the strategy data fetched from the backend to the `StrategiesView` to display the list of available strategies and their current status (active/inactive).
*   **Subtasks:**
    *   **[ ] 7.4.1:** In `StrategiesView`, create a slot method (e.g., `_on_strategies_update(data)`).
    *   **[ ] 7.4.2:** Connect the `ApiWorker`'s `finished` signal to this slot.
    *   **[ ] 7.4.3:** (Pseudocode) Implement the logic to display the strategies, for example, in a table with columns for "Name", "Type", and "Status".

### Task 7.5: [PENDING] Implement Data Rendering in PaperTradingReportWidget
*   **Description:** Ensure the trading history report in `HistoryView` is correctly populated with data from the backend.
*   **Subtasks:**
    *   **[ ] 7.5.1:** In `PaperTradingReportWidget`, create a slot method (e.g., `_on_history_received(data)`).
    *   **[ ] 7.5.2:** Connect the `ApiWorker` that fetches the trading history to this slot.
    *   **[ ] 7.5.3:** (Pseudocode) Implement the logic to populate the report table with the historical trade data.

---

## Phase 8: [IN PROGRESS] Backend Production Hardening

This phase implements the robustness and observability improvements identified in the backend audit.

### Task 8.1: [PENDING] Implement Retry Mechanism in BinanceAdapter
*   **Description:** Improve the resilience of the Binance integration by adding a retry mechanism for transient errors.
*   **Subtasks:**
    *   **[ ] 8.1.1:** (Pseudocode) In `src/ultibot_backend/adapters/binance_adapter.py`, apply a retry decorator (e.g., from the `tenacity` library) to methods making API calls.
    *   **[ ] 8.1.2:** Configure the decorator to retry on specific exceptions (e.g., `httpx.ConnectError`, `httpx.ReadTimeout`) and specific HTTP status codes (e.g., 500, 502, 503, 504).

### Task 8.2: [PENDING] Enhance Logging Context
*   **Description:** Add more context to backend logs to facilitate easier debugging and tracing.
*   **Subtasks:**
    *   **[ ] 8.2.1:** (Pseudocode) Investigate and integrate a library like `asgi-correlation-id` into `src/ultibot_backend/main.py` to add a unique request ID to all log entries associated with a single API request.
    *   **[ ] 8.2.2:** (Pseudocode) In `src/ultibot_backend/services/strategy_service.py`, add explicit `logger.info()` lines for `activate_strategy` and `deactivate_strategy` calls, including the strategy ID.

### Task 8.3: [PENDING] Refine Gemini API Error Handling
*   **Description:** Make the error handling for Gemini API calls more specific and informative.
*   **Subtasks:**
    *   **[ ] 8.3.1:** (Pseudocode) In `src/ultibot_backend/services/ai_orchestrator_service.py`, add specific `except` blocks for exceptions from the `google.api_core.exceptions` module before the generic `except Exception`. This allows for tailored responses or actions based on the error type (e.g., authentication, quota).

### Task 8.4: [PENDING] Monitor Fallback LLM Output Parser
*   **Description:** Add specific logging to track how often the less reliable `OutputFixingParser` is used.
*   **Subtasks:**
    *   **[ ] 8.4.1:** (Pseudocode) In `src/ultibot_backend/services/ai_orchestrator_service.py`, add a `logger.warning()` statement inside the `except` block where `OutputFixingParser` is invoked.

### Task 8.5: [PENDING] Ensure Explicit Service Shutdown
*   **Description:** Make the application shutdown sequence more robust and explicit.
*   **Subtasks:**
    *   **[ ] 8.5.1:** (Pseudocode) In `src/ultibot_backend/dependencies.py`, modify the `DependencyContainer.shutdown` method to explicitly call the `.close()` method of each service that has one (e.g., `market_data_service`, `notification_service`).
    *   **[ ] 8.5.2:** Ensure the `close()` methods on these services are idempotent (can be called multiple times without error).

---

## Phase 9: [IN PROGRESS] Visual Enhancements & Final Touches

This phase focuses on polishing the UI's visual appeal and conducting a final, comprehensive verification of the entire application flow.

### Task 9.1: [PENDING] Explore Visual Improvements with Magic UI
*   **Description:** Identify and select visual components and effects from the `@magicuidesign/mcp` toolset that can be adapted to enhance the PyQt5 UI.
*   **Subtasks:**
    *   **[ ] 9.1.1:** Use the `getComponents`, `getSpecialEffects`, `getTextAnimations`, etc., tools from the `@magicuidesign/mcp` server.
    *   **[ ] 9.1.2:** Create a shortlist of effects that can be realistically implemented or mimicked with PyQt's styling capabilities (e.g., `ShineBorder`, `NumberTicker`, animated gradients).

### Task 9.2: [PENDING] Integrate Selected Visual Enhancements
*   **Description:** Apply the selected visual improvements to the UI.
*   **Subtasks:**
    *   **[ ] 9.2.1:** (Pseudocode) Create a custom `ShineBorderFrame` widget that uses `QPainter` and animations to replicate the `ShineBorder` effect, and apply it to the main view containers.
    *   **[ ] 9.2.2:** (Pseudocode) Create a `NumberTickerLabel` widget that uses `QPropertyAnimation` to animate number changes, and use it in `PortfolioView`.

### Task 9.3: [PENDING] Perform Full User Flow Verification
*   **Description:** Conduct a final manual "smoke test" of the entire application to ensure all components work together seamlessly.
*   **Subtasks:**
    *   **[ ] 9.3.1:** Execute `run_frontend_with_backend.bat`.
    *   **[ ] 9.3.2:** Verify that the UI launches and correctly displays initial portfolio/strategy data.
    *   **[ ] 9.3.3:** Manually trigger (or simulate) an AI opportunity and verify it appears in the UI.
    *   **[ ] 9.3.4:** Execute a paper trade based on the opportunity.
    *   **[ ] 9.3.5:** Verify that the portfolio and trade history views update correctly.
    *   **[ ] 9.3.6:** Check `logs/frontend.log` and `logs/backend.log` for any errors.

### Task 9.4: [PENDING] Final Documentation and Cleanup
*   **Description:** Prepare the project for its "final" state.
*   **Subtasks:**
    *   **[ ] 9.4.1:** Review and update `README.md` with the final, simplified instructions for running the application.
    *   **[ ] 9.4.2:** Remove any leftover debugging code, print statements, or temporary files.

---

This focused plan provides a clear path for deploying a powerful, AI-driven investment tool.
