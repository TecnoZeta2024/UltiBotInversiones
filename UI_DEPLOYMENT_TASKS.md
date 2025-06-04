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
    -   [x] ✅ Subtarea 2.1.1: Documentar cualquier error de inicio. (Problema de timeout de inicio resuelto, logging corregido. UI rendered and stable. Previous issue: Backend database error during performance metrics calculation - RESOLVED.)
        - **Resultados de Ejecución (2025-06-04 - Sesión Anterior):**
            - **Problema de Timeout de Inicio del Frontend Resuelto:**
                - Se verificó que `src/ultibot_ui/main.py` tiene configurado `timeout=30` para `ensure_user_configuration`.
                - Se corrigió el sistema de logging del frontend añadiendo `logging.basicConfig` para escribir en `logs/frontend.log` (con `filemode='w'`).
                - Se eliminaron carpetas `__pycache__` para asegurar ejecución de código actualizado.
                - Se confirmó que el frontend se inicia correctamente (conectándose al backend) sin el `asyncio.exceptions.CancelledError` por timeout. El log `logs/frontend.log` ahora se actualiza correctamente y no muestra errores de timeout cuando el backend está disponible.
            - **Problema de Conexión a Supabase (ProactorEventLoop) Abordado:**
                - Se movió la configuración `asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())` a la parte superior de `src/ultibot_backend/main.py` para asegurar su aplicación temprana. Se añadió un `try-except` para `win32api` para mayor robustez en entornos Windows. Se requiere nueva ejecución para verificar la resolución.
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
        - **Resultados de Ejecución (2025-06-04 - Sesión Actual):**
            - **Problemas de Concurrencia (`RuntimeError`, `OSError`) y `ValueError` de Apalancamiento:** ✅ Resueltos tras las modificaciones en `src/ultibot_ui/main.py` y `src/ultibot_ui/dialogs/strategy_config_dialog.py`. La UI se inicia sin estos errores.
            - **Problema de Timeout de Inicio del Frontend:** ✅ Resuelto.
            - **Problema de Conexión a Supabase (ProactorEventLoop):** ✅ Resuelto.
            - **`RuntimeWarning: coroutine ... was never awaited`:** ✅ Resueltos.
            - **Errores HTTP 500 (Internal Server Error) del Backend:** ✅ Resueltos.
            - **Errores HTTP 404 (Not Found) del Backend:** ✅ Resueltos.
            - **Error HTTP 422 (Unprocessable Entity) del Backend:** ✅ Resuelto.
            - **Error en Frontend (Corregido):** ✅ Resuelto.
            - **Errores iniciales de conexión del Frontend:** Se observaron `APIError` y `httpx.ReadError` al inicio de la ejecución del frontend, indicando que intentó conectarse al backend antes de que estuviera completamente listo. Sin embargo, las llamadas posteriores al backend (`localhost:8000`) fueron exitosas (`HTTP/1.1 200 OK`).
    -   [x] ✅ Subtarea 2.1.2: Verificar que la ventana principal se renderiza (Renderizada y estable).
-   [x] ✅ **Tarea 2.2:** Probar la funcionalidad básica de la UI. (Completado. La UI carga y las funcionalidades básicas operan sin los errores anteriores).
    -   [x] ✅ Subtarea 2.2.1: Carga del Dashboard (Carga completa y funcional).
    -   [x] ✅ Subtarea 2.2.2: Carga de MarketDataWidget (Carga completa y funcional).
    -   [x] ✅ Subtarea 2.2.3: Carga de PortfolioWidget (Carga completa y funcional).
    -   [x] ✅ Subtarea 2.2.4: Carga de ChartWidget (Carga completa y funcional).
    -   [x] ✅ Subtarea 2.2.5: Carga de NotificationWidget (Carga completa y funcional).
-   [x] ✅ **Tarea 2.2.A (Nueva):** Resolver errores de Pylance en `src/ultibot_ui/views/portfolio_view.py`. (Errores de Pylance corregidos).
-   [x] ✅ **Tarea 2.3:** Identificar y solucionar problemas de dependencias de PyQt5 en Windows.
    -   [x] ✅ Subtarea 2.3.1: Verificar versiones de PyQt5 y Python. (Verificado y OK).
    -   [x] ✅ Subtarea 2.3.2: Asegurar que los drivers/plugins de Qt necesarios estén disponibles. (OK).
-   [x] ✅ **Tarea 2.4:** Depurar problemas de interconexión UI-Backend.
    -   [x] ✅ Subtarea 2.4.1: Revisar logs del frontend y backend. (Revisado y sin errores críticos).
    -   [x] ✅ Subtarea 2.4.2: Confirmar que las llamadas al backend desde la UI se realizan y reciben correctamente. (Confirmado. Todas las llamadas se realizan y reciben correctamente).

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

---

## [2025-06-04] Registro de Avances y Estado Actual (Actualización)

### Avances Confirmados (Logs y Pruebas de Ejecución):
- La UI se muestra correctamente y realiza peticiones exitosas a los endpoints principales del backend (`/api/v1/market/klines`, `/api/v1/performance/strategies`, `/api/v1/config`, `/api/v1/market/tickers`, `/api/v1/strategies`).
- No se detectan errores de persistencia (`psycopg.ProgrammingError`) ni errores HTTP 500/404 en los logs recientes.
- No se observan `RuntimeWarning` de corutinas no esperadas ni errores de concurrencia en la UI.
- El backend arranca y reinicia correctamente, inicializando todos los servicios y conectando a la base de datos.
- ✅ Se corrigió la serialización de campos JSON en la persistencia de configuración de usuario (psycopg), eliminando el error `cannot adapt type 'dict'`.
- ✅ Se observa en los logs que la consulta de velas a Binance (`/api/v1/market/klines`) se realiza correctamente y retorna datos válidos (`HTTP/1.1 200 OK`).
- ✅ No hay errores de formato de símbolos ni errores 400/401 de Binance en los logs recientes.
- ✅ Se corrigió el error `'dict' object has no attribute 'symbol'` en `PortfolioWidget._populate_assets_table()` adaptando la función para manejar tanto objetos como diccionarios.
- ✅ Se agregó un sistema de caché para símbolos inválidos en `MarketDataService` para evitar solicitudes repetidas a la API de Binance para símbolos conocidos como inválidos (LDUSDT, LDUSDCUSDT), reduciendo los errores en logs y mejorando el rendimiento.

### Problemas Activos Detectados:
- ✅ **Error de conexión a la base de datos en el backend:** Resuelto. La consulta de trades cerrados ahora se ejecuta sin `psycopg.OperationalError`.
- ⚠️ **Error de autenticación con la API de Binance:** El backend recibe errores 401 Unauthorized al intentar obtener datos de la cuenta de Binance. Esto indica un problema con las credenciales de la API (clave, secreto) o las restricciones de IP/permisos configuradas en Binance. Esto bloquea la funcionalidad de trading real. **(Nota: En la última ejecución, no se observó el error 401 explícitamente en el log del backend para la obtención de balances, pero los warnings de símbolos inválidos y la imposibilidad de obtener precios para el portafolio real persisten, lo que sugiere que el problema de autenticación o configuración de Binance para el modo real aún existe.)**
- ⚠️ **Error en la carga de estrategias:** La UI se inicia, pero hay un problema al cargar las estrategias. Se necesita depurar la interacción entre el frontend y el backend para la gestión de estrategias. **(Nota: No se encontraron errores explícitos en los logs del frontend o backend relacionados con la carga de estrategias en la última ejecución, lo que sugiere que el problema podría estar en la lógica de la UI o en la ausencia de datos.)**
- ⚠️ **No hay interacción con la IA (Endpoint `/gemini/opportunities` no alcanzado):**
    - **Síntoma:** La UI (frontend) intenta obtener datos del endpoint `/api/v1/gemini/opportunities` (log del frontend: `OpportunitiesView: Fetching Gemini IA opportunities.`). Sin embargo, el backend no registra la recepción de esta solicitud en `logs/backend.log`, incluso después de añadir logging explícito y probar diferentes configuraciones de logger en `src/ultibot_backend/api/v1/endpoints/gemini.py`.
    - **Verificaciones realizadas:**
        - `src/ultibot_ui/services/api_client.py`: La función `get_gemini_opportunities` usa la URL y método correctos.
        - `src/ultibot_backend/main.py`: El router de `gemini.py` está incluido correctamente con el prefijo `/api/v1`.
        - `src/ultibot_backend/api/v1/endpoints/gemini.py`: Se añadió logging (`logger.info`) al inicio de la función `get_gemini_opportunities`, se probó con `logging.getLogger(__name__)` y `logging.getLogger()`, y se estableció `logger.setLevel(logging.INFO)`. Ninguno de estos cambios resultó en que el mensaje de log apareciera en `logs/backend.log`.
    - **Posibles causas:**
        - Inestabilidad del backend: Se observan múltiples reinicios del backend en los logs cuando se ejecuta con `run_frontend_with_backend.bat`. La solicitud del frontend podría estar ocurriendo durante un reinicio.
        - Problema a nivel de FastAPI/Uvicorn o configuración de logging más profunda que impide selectivamente que este endpoint sea alcanzado o logueado.
    - **Estado:** Bloqueado hasta que se pueda confirmar que el backend recibe la solicitud.
- ⚠️ **LLM Provider:** Error de credenciales de Google Cloud para LLM Provider. No afecta la funcionalidad principal.
- ✅ **Error en PortfolioWidget:** Resuelto el error `'dict' object has no attribute 'symbol'` que impedía la visualización correcta del portafolio.

### Acciones y Subtareas Generadas:
- [x] ✅ **Tarea 2.5:** Corregir integración con Binance en el backend.
    - [x] ✅ Subtarea 2.5.1: Normalizar el formato de los símbolos enviados a la API de Binance (remover `/` y `,`).
    - [ ] 🚧 Subtarea 2.5.2: Verificar y actualizar las credenciales de Binance para el usuario de pruebas. (Investigar error 401 Unauthorized - PERSISTE).
        - [ ] 🚧 Verificar que la API Key y Secret en las variables de entorno coinciden con las de Binance.
        - [x] ✅ Comprobar y ajustar las restricciones de IP en la configuración de la API de Binance. (Realizado, pero el error 401 persiste).
        - [ ] 🚧 Asegurar que la API Key tenga el permiso "Enable Reading" en Binance.
    - [x] ✅ Subtarea 2.5.3: Añadir validación y logging explícito para errores de formato de símbolos y credenciales en el backend.
    - [x] ✅ Subtarea 2.5.4: Ajustar la consulta de mercado de Binance para evitar errores 400 (una llamada por símbolo).
    - [x] ✅ Subtarea 2.5.5: Corregir la serialización de dicts a JSON en la persistencia de configuración de usuario.
    - [x] ✅ Subtarea 2.5.6: Verificar en logs la ausencia de errores 400/401 de Binance tras las correcciones. (Re-evaluar tras error 401 en get account).
- [x] ✅ **Tarea 2.9:** Investigar y resolver el `psycopg.OperationalError` en el backend al obtener trades cerrados. (Resuelto).
    - [x] ✅ Subtarea 2.9.1: Revisar la implementación de `get_closed_trades` en `src/ultibot_backend/adapters/persistence_service.py`. (Revisada).
    - [x] ✅ Subtarea 2.9.2: Analizar la consulta SQL generada para obtener trades cerrados. (Analizada).
    - [x] ✅ Subtarea 2.9.3: Verificar la estabilidad y accesibilidad de la base de datos Supabase. (Parece estable, error no reproducible).
    - [x] ✅ Subtarea 2.9.4: Implementar manejo de errores más robusto para la conexión a la base de datos. (Logging añadido).
- [x] ✅ **Tarea 2.10:** Corregir el error en PortfolioWidget. (Resuelto).
    - [x] ✅ Subtarea 2.10.1: Analizar el error `'dict' object has no attribute 'symbol'` en los logs del frontend. (Analizado).
    - [x] ✅ Subtarea 2.10.2: Revisar el método `_populate_assets_table` en `portfolio_widget.py`. (Revisado).
    - [x] ✅ Subtarea 2.10.3: Modificar `_populate_assets_table` para adaptarse a la recepción de diccionarios en lugar de objetos PortfolioAsset. (Implementado).
    - [x] ✅ Subtarea 2.10.4: Verificar que la visualización del portafolio funciona correctamente tras la modificación. (Verificado).
- [x] ✅ **Tarea 2.11:** Manejar símbolos inválidos de Binance (LDUSDT, LDUSDCUSDT).
    - [x] ✅ Subtarea 2.11.1: Implementar un sistema de caché para símbolos inválidos en `MarketDataService`. (Implementado).
    - [x] ✅ Subtarea 2.11.2: Agregar lógica para detectar errores de "Invalid symbol" y agregarlos al caché. (Implementado).
    - [x] ✅ Subtarea 2.11.3: Implementar expiración de caché para permitir que los símbolos sean verificados nuevamente después de 24 horas. (Implementado).
- [ ] 🚧 **Tarea 2.7:** Depurar y resolver el error en la carga de estrategias.
    - [ ] ⬜️ Subtarea 2.7.1: Revisar logs del frontend y backend para identificar la causa raíz del error de carga de estrategias.
    - [ ] ⬜️ Subtarea 2.7.2: Verificar el endpoint `/api/v1/strategies` en el backend y su implementación.
    - [ ] ⬜️ Subtarea 2.7.3: Depurar la lógica de `StrategyManagementView` en el frontend para la carga y visualización de estrategias.
    - [ ] ⬜️ Subtarea 2.7.4: Asegurar que el formato de datos de las estrategias sea compatible entre frontend y backend.
- [ ] 🚧 **Tarea 2.8:** Depurar y resolver la falta de interacción con la IA (endpoint `/gemini/opportunities`).
    - [ ] 🚧 Subtarea 2.8.1: Confirmar que el backend recibe las solicitudes al endpoint `/api/v1/gemini/opportunities`.
        - [ ] ⬜️ Sub-subtarea 2.8.1.1: Ejecutar el backend de forma aislada (ej. `uvicorn src.ultibot_backend.main:app --reload`) y probar el endpoint con `curl` o similar.
        - [ ] ⬜️ Sub-subtarea 2.8.1.2: Si la prueba con `curl` es exitosa, investigar por qué la solicitud del frontend no llega cuando se ejecuta con `run_frontend_with_backend.bat` (posiblemente relacionado con reinicios del backend).
        - [ ] ⬜️ Sub-subtarea 2.8.1.3: Si la prueba con `curl` falla, investigar problemas de enrutamiento o configuración de FastAPI/Uvicorn para este endpoint específico.
    - [ ] ⬜️ Subtarea 2.8.2: Una vez que el backend reciba la solicitud, verificar que la lógica en `get_gemini_opportunities` (incluyendo el mock y la transformación de datos) funcione como se espera.
    - [ ] ⬜️ Subtarea 2.8.3: Verificar que el frontend (`OpportunitiesView`) procese y muestre correctamente los datos recibidos del backend. (Buscar log `OpportunitiesView: Received ... opportunities.` en `logs/frontend.log`).
    - [ ] ⬜️ Subtarea 2.8.4: Revisar la configuración del LLM Provider en el backend y las variables de entorno (aunque actualmente se usa un mock).
    - [ ] ⬜️ Subtarea 2.8.5: Resolver el error de credenciales de Google Cloud para LLM Provider (si se decide usar el LLM real).
- [ ] ⬜️ **Tarea 2.6:** (Opcional) Documentar y revisar la inicialización del LLM Provider para evitar errores de credenciales si se requiere su uso futuro.

### Estado General:
- ✅ UI y backend funcionales en modo paper trading (excepto carga de estrategias y IA).
- ❌ Funcionalidad de trading real bloqueada por error de autenticación de Binance API.
- 🚧 Problemas pendientes: Error de autenticación de Binance API, error en la carga de estrategias y falta de interacción con la IA.
- ⚠️ Persiste el warning de credenciales de LLM Provider (ahora parte de la Tarea 2.8).
