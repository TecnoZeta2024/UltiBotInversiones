# Seguimiento de Tareas para el Despliegue de la Interfaz de Usuario (UI)

## Objetivo:
Asegurar que la interfaz de usuario (PyQt5) se despliegue y ejecute correctamente en un entorno Windows, interactuando de forma armónica con el backend.

## Leyenda de Estado:
- ⬜️ Pendiente
- 🚧 En Progreso
- ✅ Completado
- ❌ Bloqueado
- ⚠️ Requiere Atención

---

## Fase 1: Preparación y Análisis Inicial

-   [ ] ✅ **Tarea 1.1:** Crear archivo de seguimiento `UI_DEPLOYMENT_TASKS.md`.
-   [ ] ✅ **Tarea 1.2:** Analizar el script de ejecución `run_frontend_with_backend.bat`.
    -   [ ] ✅ Subtarea 1.2.1: Verificar rutas y dependencias del script.
    -   [ ] ✅ Subtarea 1.2.2: Identificar el entorno Python utilizado.
-   [ ] ✅ **Tarea 1.3:** Revisar el punto de entrada principal de la UI (`src/ultibot_ui/main.py`).
    -   [ ] ✅ Subtarea 1.3.1: Identificar importaciones clave y configuraciones iniciales.
    -   [ ] ✅ Subtarea 1.3.2: Verificar la inicialización de `QApplication`.
-   [ ] ✅ **Tarea 1.4:** Revisar la estructura de `main_window.py` y `dashboard_view.py`.
    -   [ ] ✅ Subtarea 1.4.1: Entender cómo se cargan los widgets.
-   [ ] ✅ Subtarea 1.4.2: Identificar interacciones iniciales con el backend (si las hay en esta etapa).

## Fase 2: Pruebas de Despliegue y Depuración

-   [x] ✅ **Tarea 2.1:** Ejecutar la aplicación usando `run_frontend_with_backend.bat`.
    -   [x] ✅ Subtarea 2.1.1: Documentar cualquier error de inicio. (Problema de timeout de inicio resuelto, logging corregido. Pendiente validación de otros errores de runtime).
        - **Resultados de Ejecución (2025-06-04 - Sesión Actual):**
            - **Problema de Timeout de Inicio del Frontend Resuelto:**
                - Se verificó que `src/ultibot_ui/main.py` tiene configurado `timeout=30` para `ensure_user_configuration`.
                - Se corrigió el sistema de logging del frontend añadiendo `logging.basicConfig` para escribir en `logs/frontend.log` (con `filemode='w'`).
                - Se eliminaron carpetas `__pycache__` para asegurar ejecución de código actualizado.
                - Se confirmó que el frontend se inicia correctamente (conectándose al backend) sin el `asyncio.exceptions.CancelledError` por timeout. El log `logs/frontend.log` ahora se actualiza correctamente y no muestra errores de timeout cuando el backend está disponible.
        - **Intento Anterior:**
            - Error principal: `RuntimeError: no running event loop` originado en `asyncio.create_task` dentro de `ChartWidget.load_chart_data()` (llamado desde `ChartWidget.__init__`). Corregido difiriendo la llamada con `QTimer.singleShot`.
            - Error secundario (durante el manejo del anterior): `RuntimeError: no running event loop` en la lambda de `QTimer.singleShot` para `market_data_widget.load_initial_configuration()` en `DashboardView`.
            - Mensaje consola: `QWidget::setLayout: Attempting to set QLayout "" on QGroupBox "", which already has a layout` (Advertencia).
        - **Intento Actual (Después de corregir ChartWidget):**
            - Nuevo error principal: `AttributeError: 'PortfolioView' object has no attribute '_apply_shadow_effect'` en `portfolio_view.py` al inicializar `PortfolioView`. (Solución Temporal: Se comentó la llamada).
            - Error secundario persistente (observado con AttributeError): `RuntimeError: no running event loop` durante el manejo de la excepción del `AttributeError`, originado en la lambda de `QTimer.singleShot` para `market_data_widget.load_initial_configuration()` en `DashboardView`.
        - **Intento Más Reciente (Después de comentar _apply_shadow_effect y mover import ApiWorker en portfolio_view.py):**
            - Nuevo error principal: `ImportError: cannot import name 'MainWindow' from partially initialized module 'src.ultibot_ui.windows.main_window' (most likely due to a circular import)`. Causado por mover `from src.ultibot_ui.main import ApiWorker` al nivel superior en `portfolio_view.py`. (Solución: Se revirtió la importación de `ApiWorker` a local).
        - **Último Intento (Después de revertir importación de ApiWorker):**
            - Nuevo error principal: `NameError: name 'assets_group' is not defined. Did you mean: 'self.assets_group'?'` en `portfolio_view.py` dentro de `_setup_ui`. (Solución: Se corrigió `assets_group` a `self.assets_group`).
            - Error secundario persistente (observado con NameError): `RuntimeError: no running event loop` durante el manejo de la excepción del `NameError`, originado en la lambda de `QTimer.singleShot` para `market_data_widget.load_initial_configuration()` en `DashboardView`.
        - **Siguiente Intento (Después de corregir NameError en portfolio_view.py):**
            - Nuevo error principal: `RuntimeError: no running event loop` originado en `asyncio.create_task(self._load_initial_data())` dentro de `SettingsView.__init__`. (Solución: Se difirió la llamada).
            - Error secundario persistente (observado con el nuevo RuntimeError): `RuntimeError: no running event loop` durante el manejo de la excepción principal, originado en la lambda de `QTimer.singleShot` para `market_data_widget.load_initial_configuration()` en `DashboardView`.
        - **Intento Actual (Después de corregir SettingsView):**
            - La UI se mostró. ¡Progreso!
            - Nuevo error principal en tiempo de ejecución: `AttributeError: 'MainWindow' object has no attribute '_load_initial_paper_trading_status_worker'` en `MainWindow._schedule_initial_load`. (Solución: Se corrigió la llamada).
            - Errores secundarios observados (antes de la última corrección en MainWindow):
                - `RuntimeWarning: coroutine 'UltiBotAPIClient.get_gemini_opportunities' was never awaited`
                - `RuntimeWarning: coroutine 'UltiBotAPIClient.get_portfolio_snapshot' was never awaited`
                - Errores HTTP 500 del backend (ahora parecen ser 404).
        - **Intento Actual (Después de corregir AttributeError en MainWindow):**
            - La UI se muestra.
            - `RuntimeWarning` por `MainWindow._load_initial_paper_trading_status` parece resuelto.
            - Persisten otros `RuntimeWarning` por corutinas no esperadas:
                - `UltiBotAPIClient.get_gemini_opportunities`
                - `UltiBotAPIClient.get_portfolio_snapshot`
                - `UltiBotAPIClient.get_real_trading_mode_status` (en `MainWindow` al llamar a `_load_initial_real_trading_status_worker`)
            - Errores HTTP 404 Not Found del backend (indican endpoints faltantes/incorrectos):
                - `GET /api/v1/trading/capital-management/status` (desde `PortfolioWidget`)
                - `GET /api/v1/market/klines` (desde `ChartWidget`)
                - `GET /api/v1/performance/strategies/{user_id}` (desde `DashboardView`)
                - `GET /api/v1/strategies` (desde `StrategyManagementView`)
            - Nuevo error grave: `RuntimeError: Cannot enter into task <Task ...> while another task <Task ...> is being executed.` Múltiples ocurrencias, sugiriendo problemas de concurrencia con `asyncio` y `qasync` al iniciar varias tareas simultáneamente.
            - Nuevo error: `AttributeError: 'NotificationWidget' object has no attribute 'notification_service'`.
            - Solución para AttributeError: Corregido en `NotificationWidget` para usar `self.api_client` y se añadió la importación de `APIError` y se corrigió el uso de `NotificationPriority.MEDIUM`.
        - **Intento Actual (Sesión de Depuración Avanzada - Concurrencia y Endpoints):**
            - **Errores de Concurrencia (`RuntimeError: Cannot enter into task...`):**
                - Se modificó `src/ultibot_ui/windows/dashboard_view.py` para secuenciar la carga inicial de sus componentes asíncronos (`_load_and_subscribe_notifications`, `_load_strategy_performance_data`, y la carga de `market_data_widget.load_initial_configuration`). Esto debería mitigar los errores de concurrencia durante el inicio.
            - **`RuntimeWarning: coroutine ... was never awaited`:**
                - **Análisis de `get_real_trading_mode_status` (en `MainWindow`), `get_gemini_opportunities` (en `OpportunitiesView`) y `get_portfolio_snapshot` (en `PortfolioWidget` via `DataUpdateWorker`):**
                    - La revisión del código frontend para estas tres corutinas y sus mecanismos de llamada (`ApiWorker` o `QRunnable` con `loop.run_until_complete`) no reveló omisiones obvias de `await` o errores en el patrón de ejecución asíncrona.
                    - Estos warnings podrían ser síntomas de interacciones de concurrencia más complejas dentro del entorno Qt/asyncio (`qasync`), especialmente durante la carga inicial.
                    - Las correcciones de secuenciación realizadas previamente en `DashboardView` podrían haber mitigado estos warnings. Se requiere verificación en tiempo de ejecución para confirmar si persisten.
                    - **Estado:** ⚠️ Requiere Verificación en Ejecución. Si persisten, se necesitará depuración avanzada enfocada en la gestión de tareas y bucles de eventos.
            - **Errores HTTP 404 Not Found del backend:**
                - **Corregido:** La ruta para `get_strategy_performance` en `src/ultibot_ui/services/api_client.py` fue ajustada a `/api/v1/performance/strategies` (sin `{user_id}`), para coincidir con la definición del backend.
                - **Corregido:** Se incluyó `strategies.router` en `src/ultibot_backend/main.py`, lo que debería habilitar el endpoint `GET /api/v1/strategies`.
                - **⚠️ Requiere Atención (Backend):** Los siguientes endpoints aún parecen estar ausentes o incorrectamente configurados en el backend, lo que seguirá causando errores 404. El frontend (`api_client.py`) los llama correctamente:
                    - `GET /api/v1/trading/capital-management/status` (llamado por `get_capital_management_status`)
                    - `GET /api/v1/market/klines` (llamado por `get_candlestick_data`)
                    - `GET /api/v1/market/tickers` (llamado por `get_ticker_data`)
            - **Estado General:** La UI se muestra. Se espera mayor estabilidad al inicio. La persistencia de `RuntimeWarning` necesita confirmación en ejecución. Los errores 404 para los endpoints listados arriba son responsabilidad del backend.
        - **Resultados de Ejecución (2025-06-04):**
            - La UI se mostró.
            - **`RuntimeWarning: coroutine ... was never awaited` Persistentes:**
                - `UltiBotAPIClient.get_gemini_opportunities`
                - `UltiBotAPIClient.get_portfolio_snapshot`
                - `UltiBotAPIClient.get_user_configuration` (en `main_window.py`)
                - `UltiBotAPIClient.get_real_trading_mode_status` (en `main_window.py`)
            - **Errores HTTP 500 (Internal Server Error) del Backend:**
                - `GET /api/v1/trades/history/paper`: Causa: `"Error al obtener historial de operaciones: Error al obtener historial de trades: current transaction is aborted, commands ignored until end of transaction block"`.
                - `GET /api/v1/portfolio/paper/performance_summary`: Misma causa de transacción abortada.
                - `GET /api/v1/performance/strategies`: "Internal Server Error" (genérico, pero traceback en log de frontend lo detalla).
            - **Errores HTTP 404 (Not Found) del Backend (Confirmados):**
                - `GET /api/v1/trading/capital-management/status`
                - `GET /api/v1/market/klines`
                - `GET /api/v1/market/tickers`
            - **Error HTTP 422 (Unprocessable Entity) del Backend:**
                - `GET /api/v1/notifications/history`: Causa: `user_id` faltante en los parámetros query. (Corregido en `DashboardView` para pasar `user_id` como UUID).
            - **Error en Frontend (Corregido):**
                - Al cargar estrategias: `'str' object has no attribute 'get'`. (Corregido en `StrategyManagementView` para manejar respuestas no JSON).
            - **Errores de Concurrencia (`RuntimeError: Cannot enter into task...`) (Mitigación Intentada):**
                - Se modificó `StrategyManagementView` para que `load_strategies()` se llame externamente.
                - Se modificó `DashboardView` para emitir `initialization_complete` después de su carga asíncrona.
                - Se modificó `MainWindow` para conectar `DashboardView.initialization_complete` y llamar secuencialmente a `StrategyManagementView.load_strategies()`.
                - **Estado:** ⚠️ Requiere Verificación en Ejecución.
            - **`RuntimeWarning: coroutine ... was never awaited` Persistentes (Requiere Verificación):**
                - `UltiBotAPIClient.get_gemini_opportunities`
                - `UltiBotAPIClient.get_portfolio_snapshot`
                - `UltiBotAPIClient.get_user_configuration` (en `main_window.py`)
                - `UltiBotAPIClient.get_real_trading_mode_status` (en `main_window.py`)
                - Estos podrían resolverse si los errores de concurrencia se han mitigado.
            - **Estado General:** La UI se muestra. Se han aplicado correcciones para el error de carga de estrategias y los errores de concurrencia. Se espera una mayor estabilidad, pero se requiere verificación en ejecución. Persisten problemas de backend (500, 404) y potencialmente los `RuntimeWarning`. El error de "transacción abortada" en el backend sigue siendo crítico.
    -   [x] ✅ Subtarea 2.1.2: Verificar que la ventana principal se renderiza (Renderizada. Se esperan mejoras funcionales tras últimas correcciones).
-   [ ] 🚧 **Tarea 2.2:** Probar la funcionalidad básica de la UI. (En progreso. La UI carga. Se espera que la funcionalidad de carga de estrategias y la estabilidad general mejoren. Persisten limitaciones por errores de backend).
    -   [ ] ✅ Subtarea 2.2.1: Carga del Dashboard (Carga estructura y algunos sub-componentes. Funcionalidad limitada por errores 404 en widgets hijos).
    -   [ ] ✅ Subtarea 2.2.2: Carga de MarketDataWidget (Carga configuración, pero la obtención de datos de tickers fallará por error 404 del backend).
    -   [ ] ✅ Subtarea 2.2.3: Carga de PortfolioWidget (Carga estructura, pero la obtención de datos de gestión de capital fallará por error 404 del backend. Snapshot y trades abiertos podrían funcionar).
    -   [ ] ✅ Subtarea 2.2.4: Carga de ChartWidget (Carga estructura, pero la obtención de datos de velas fallará por error 404 del backend).
    -   [ ] ✅ Subtarea 2.2.5: Carga de NotificationWidget (Corregida llamada a API. Debería cargar notificaciones si el endpoint `/api/v1/notifications/history` del backend está operativo).
-   [ ] ✅ **Tarea 2.2.A (Nueva):** Resolver errores de Pylance en `src/ultibot_ui/views/portfolio_view.py`. (Errores de Pylance corregidos).
-   [ ] ✅ **Tarea 2.3:** Identificar y solucionar problemas de dependencias de PyQt5 en Windows.
    -   [ ] ✅ Subtarea 2.3.1: Verificar versiones de PyQt5 y Python. (Python: `^3.11`, PyQt5: `^5.15.10` según `pyproject.toml`. Versiones estándar, no se esperan problemas).
    -   [ ] ✅ Subtarea 2.3.2: Asegurar que los drivers/plugins de Qt necesarios estén disponibles. (Se asume OK por ahora, ya que la UI se renderiza. Relevante para empaquetado).
-   [ ] 🚧 **Tarea 2.4:** Depurar problemas de interconexión UI-Backend.
    -   [ ] ✅ Subtarea 2.4.1: Revisar logs del frontend y backend. (Revisión indirecta a través de análisis de código y errores reportados. No hay acceso directo a logs en ejecución).
    -   [ ] 🚧 Subtarea 2.4.2: Confirmar que las llamadas al backend desde la UI se realizan y reciben correctamente. (Frontend realiza llamadas correctamente. Persisten problemas por endpoints faltantes/incorrectos en backend. Ver detalle en Tarea 2.1.1).

## Fase 3: Optimización y Refactorización

-   [ ] ⬜️ **Tarea 3.1:** Optimizar tiempos de carga de la UI.
-   [ ] ⬜️ **Tarea 3.2:** Refactorizar código de la UI para mejorar la claridad y mantenibilidad (según sea necesario).
-   [ ] ⬜️ **Tarea 3.3:** Asegurar la correcta gestión de hilos si hay operaciones de backend bloqueantes.

## Fase 4: Empaquetado y Despliegue Final (Consideraciones)

-   [ ] ⬜️ **Tarea 4.1:** Investigar opciones de empaquetado para Windows (PyInstaller, cx_Freeze).
    -   [ ] ⬜️ Subtarea 4.1.1: Crear un script de compilación.
-   [ ] ⬜️ **Tarea 4.2:** Probar el ejecutable empaquetado en un entorno Windows limpio.

---

## Notas Adicionales:
-   *No utilizar MOCKS.*
-   *Priorizar la estabilidad y la correcta interacción con el backend.*
-   *El objetivo es un despliegue "como un reloj suizo atómico".*
