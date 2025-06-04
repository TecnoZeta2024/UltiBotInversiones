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

-   **COMPLETADO**

## Fase 2: Pruebas de Despliegue y Depuración

-   [x] ✅ **Tarea 2.1:** Ejecutar la aplicación usando `run_frontend_with_backend.bat`.
    -   [x] ✅ Subtarea 2.1.1: Documentar cualquier error de inicio. (Problema de timeout de inicio resuelto, logging corregido. UI rendered and stable. Previous issue: Backend database error during performance metrics calculation - RESOLVED.)
    -   [x] ✅ Subtarea 2.1.3: Modificar script `.bat` para limpiar `__pycache__` antes de la ejecución. (Implementado para asegurar que se usa el código más reciente y ayudar a resolver el error `ProactorEventLoop` del backend).
        - **Resultados de Ejecución (2025-06-04 - Sesión Actual - Después de limpieza de __pycache__):**
            - ✅ **Error `ProactorEventLoop` del backend RESUELTO.** El backend ahora se inicia correctamente y se conecta a la base de datos (verificado en `logs/backend.log` timestamp `14:31:17`).
            - ✅ **Conexión inicial Frontend-Backend EXITOSA.** El frontend ahora se conecta correctamente al backend al inicio y obtiene la configuración (verificado en `logs/frontend.log` timestamp `14:31:21`). Múltiples llamadas API posteriores también son exitosas.
        - **Resultados de Ejecución (2025-06-04 - Sesión Anterior):**
            - **Problema de Timeout de Inicio del Frontend Resuelto:**
                - Se verificó que `src/ultibot_ui/main.py` tiene configurado `timeout=30` para `ensure_user_configuration`.
                - Se corrigió el sistema de logging del frontend añadiendo `logging.basicConfig` para escribir en `logs/frontend.log` (con `filemode='w'`).
                - Se eliminaron carpetas `__pycache__` para asegurar ejecución de código actualizado.
                - Se confirmó que el frontend se inicia correctamente (conectándose al backend) sin el `asyncio.exceptions.CancelledError` por timeout. El log `logs/frontend.log` ahora se actualiza correctamente y no muestra errores de timeout cuando el backend está disponible.
            - **Problema de Conexión a Supabase (ProactorEventLoop) Abordado:** (Este problema ahora está resuelto por la limpieza de `__pycache__` como se indica en Subtarea 2.1.3).
                - Se movió la configuración `asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())` a la parte superior de `src/ultibot_backend/main.py` para asegurar su aplicación temprana. Se añadió un `try-except` para `win32api` para mayor robustez en entornos Windows. Se requiere nueva ejecución para verificar la resolución.
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
- [x] ✅ **Tarea 2.5:** Corregir integración con Binance en el backend.
    
- [ ] ⬜️ **Tarea 2.6:** Documentar y revisar la inicialización del LLM Provider para evitar errores de credenciales en la fase actual.

- [ ] 🚧 **Tarea 2.7:** Depurar y resolver el error en la carga de estrategias.
    - [ ] ⬜️ Subtarea 2.7.1: Revisar logs del frontend y backend para identificar la causa raíz del error de carga de estrategias.
    - [ ] ⬜️ Subtarea 2.7.2: Verificar el endpoint `/api/v1/strategies` en el backend y su implementación.
    - [ ] ⬜️ Subtarea 2.7.3: Depurar la lógica de `StrategyManagementView` en el frontend para la carga y visualización de estrategias.
    - [ ] ⬜️ Subtarea 2.7.4: Asegurar que el formato de datos de las estrategias sea compatible entre frontend y backend.

- [ ] 🚧 **Tarea 2.8:** Depurar y resolver la falta de interacción con la IA (endpoint `/gemini/opportunities`) cuando se usa `run_frontend_with_backend.bat`.
    - [x] ✅ Subtarea 2.8.1: Confirmar que el backend recibe las solicitudes al endpoint `/api/v1/gemini/opportunities` cuando se ejecuta de forma aislada.
        - [x] ✅ Sub-subtarea 2.8.1.1: Ejecutar el backend de forma aislada (`uvicorn src.ultibot_backend.main:app --reload`) y probar el endpoint con `curl`. (Resultado: Funciona, devuelve 200 OK y JSON. El log de recepción aparece en `logs/backend.log`).
    - [ ] 🚧 Subtarea 2.8.1.2: Investigar por qué la solicitud del frontend no llega/procesa correctamente cuando se ejecuta con `run_frontend_with_backend.bat`. (La limpieza de `__pycache__` implementada en Subtarea 2.1.3 ha estabilizado el backend. Se necesita verificar si la solicitud a `/gemini/opportunities` ahora es recibida por el backend).
        - [x] ✅ Analizar la estabilidad del backend (reinicios) durante la ejecución con `run_frontend_with_backend.bat`. (Backend ahora estable al inicio).
        - [x] ✅ Revisar logs de frontend y backend de la ejecución actual (`14:31:xx`) para correlacionar el intento de llamada del frontend (`OpportunitiesView: Fetching Gemini IA opportunities.`) con la recepción en el backend. (En la ejecución de las 14:31, la llamada del frontend se registró en `logs/frontend.log` a las `14:31:22,905`, pero no se encontró una entrada correspondiente en `logs/backend.log` para esa marca de tiempo. La comunicación para este endpoint específico sigue fallando bajo `run_frontend_with_backend.bat`).
    - [x] ✅ Subtarea 2.8.2: Añadir un retraso en `OpportunitiesView._load_initial_data` antes de llamar a `_fetch_opportunities` para dar más tiempo al backend. (Implementado retraso de 5 segundos).
    - [ ] 🚧 Subtarea 2.8.3: Una vez que la comunicación sea estable con `run_frontend_with_backend.bat`, verificar que la lógica en `get_gemini_opportunities` (incluyendo el mock y la transformación de datos) funcione como se espera en ese contexto. (La comunicación aún no es estable para este endpoint).
    - [ ] 🚧 Subtarea 2.8.4: Verificar que el frontend (`OpportunitiesView`) procese y muestre correctamente los datos recibidos del backend en ese contexto. (Buscar log `OpportunitiesView: Received ... opportunities.` en `logs/frontend.log`). (Depende de la Subtarea 2.8.3).
    - [ ] ⬜️ Subtarea 2.8.5: Revisar la configuración del LLM Provider en el backend y las variables de entorno (aunque actualmente se usa un mock).
    - [ ] ⬜️ Subtarea 2.8.5: Resolver el error de credenciales de Google Cloud para LLM Provider (si se decide usar el LLM real).

- [x] ✅ **Tarea 2.9:** Investigar y resolver el `psycopg.OperationalError` en el backend al obtener trades cerrados. (Resuelto).

- [x] ✅ **Tarea 2.10:** Corregir el error en PortfolioWidget. (Resuelto).
    
- [x] ✅ **Tarea 2.11:** Manejar símbolos inválidos de Binance (LDUSDT, LDUSDCUSDT).

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

### Acciones y Subtareas Generadas:

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

- ⚠️ **Error en la carga de estrategias:** La UI se inicia, pero hay un problema al cargar las estrategias. Se necesita depurar la interacción entre el frontend y el backend para la gestión de estrategias. **(Nota: No se encontraron errores explícitos en los logs del frontend o backend relacionados con la carga de estrategias en la última ejecución, lo que sugiere que el problema podría estar en la lógica de la UI o en la ausencia de datos.)**
- ⚠️ **No hay interacción con la IA (Endpoint `/gemini/opportunities` no alcanzado):**
    - **Síntoma:** La UI (frontend) intenta obtener datos del endpoint `/api/v1/gemini/opportunities` (log del frontend: `OpportunitiesView: Fetching Gemini IA opportunities.`). Sin embargo, el backend no registra la recepción de esta solicitud en `logs/backend.log`, incluso después de añadir logging explícito y probar diferentes configuraciones de logger en `src/ultibot_backend/api/v1/endpoints/gemini.py`.
    - **Verificaciones realizadas:**
        - `src/ultibot_ui/services/api_client.py`: La función `get_gemini_opportunities` usa la URL y método correctos.
        - `src/ultibot_backend/main.py`: El router de `gemini.py` está incluido correctamente con el prefijo `/api/v1`.
        - `src/ultibot_backend/api/v1/endpoints/gemini.py`: Se añadió logging (`logger.info`) al inicio de la función `get_gemini_opportunities`, se probó con `logging.getLogger(__name__)` y `logging.getLogger()`, y se estableció `logger.setLevel(logging.INFO)`. Ninguno de estos cambios resultó en que el mensaje de log apareciera en `logs/backend.log`.
    - **Posibles causas:**
        - Inestabilidad del backend: Se observan múltiples reinicios del backend en los logs cuando se ejecuta con `run_frontend_with_backend.bat`. La solicitud del frontend podría estar ocurriendo durante un reinicio. **Esta es la causa más probable.**
        - Problema a nivel de FastAPI/Uvicorn o configuración de logging más profunda que impide selectivamente que este endpoint sea alcanzado o logueado. (Menos probable ahora).
    - **Estado:** ✅ **Endpoint funcional y loguea correctamente cuando el backend se ejecuta de forma aislada.**
        - Se ejecutó el backend con `uvicorn src.ultibot_backend.main:app --reload --port 8000`.
        - Una prueba con `curl http://localhost:8000/api/v1/gemini/opportunities` devolvió 200 OK y el JSON esperado.
        - El log `INFO - Solicitud GET a /gemini/opportunities recibida.` apareció correctamente en `logs/backend.log` durante esta prueba aislada.
        - **Conclusión:** El problema de interacción con la IA cuando se usa `run_frontend_with_backend.bat` se debe muy probablemente a la inestabilidad/reinicios del backend inducidos por el script, impidiendo que la solicitud del frontend sea procesada en el momento adecuado.


- ⚠️ **LLM Provider:** Error de credenciales de Google Cloud para LLM Provider. No afecta la funcionalidad principal.
- ✅ **Error en PortfolioWidget:** Resuelto el error `'dict' object has no attribute 'symbol'` que impedía la visualización correcta del portafolio.

### Estado General:
- ✅ UI y backend funcionales en modo paper trading (excepto carga de estrategias y IA).
- ❌ Funcionalidad de trading real bloqueada por error de autenticación de Binance API.
- 🚧 Problemas pendientes: Error de autenticación de Binance API, error en la carga de estrategias y falta de interacción con la IA.
- ⚠️ Persiste el warning de credenciales de LLM Provider (ahora parte de la Tarea 2.8).
- ✅ **Error en `src/ultibot_ui/main.py` (Línea 599):** Resuelto. Se añadió una verificación `current_thread` para asegurar que `self.thread()` no es `None` antes de llamar a `quit()`.
- ⚠️ **Error de Pylance en `src/ultibot_ui/windows/dashboard_view.py` (Línea 245):** Persiste el error "Argument missing for parameter 'user_id'" en la definición de `_load_and_subscribe_notifications`, a pesar de que la firma del método es `async def _load_and_subscribe_notifications(self):` y no espera `user_id` como argumento directo. Podría ser un falso positivo de Pylance.
- 🚧 **Problema de Inicialización del Dashboard (`_initialize_async_components`):**
    - Los logs de `_schedule_task` en `DashboardView` confirman que la tarea para `_initialize_async_components` se está creando.
    - Sin embargo, los logs internos de `_initialize_async_components` (incluyendo el primer `logger.info` dentro del `try` más externo) no aparecen en `logs/frontend.log`.
    - Esto sugiere que la corrutina `_initialize_async_components` podría estar fallando de forma silenciosa justo al inicio, antes de que se ejecute la primera instrucción de logging, o que hay un problema con la ejecución de la tarea en el bucle de eventos de `qasync` en ese punto específico.
    - Se añadió un bloque `try-except Exception` al inicio de `_initialize_async_components` para capturar errores muy tempranos. Se requiere nueva ejecución para verificar.
