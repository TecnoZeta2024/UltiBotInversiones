### INFORME POST-MORTEM - 12/06/2025 15:58

**REFERENCIA A INTENTOS PREVIOS:**
* Este post-mortem se genera tras el fallo catastrófico de la suite de tests (`poetry run pytest`) después de la refactorización de `src/ultibot_backend/core/domain_models/prompt_models.py` a Pydantic V2.
* El fallo reintroduce los errores `SystemError: AST constructor recursion depth mismatch` y `RuntimeError: Event loop is closed`, que se creían resueltos según `AUDIT_REPORT.md`.

**Resultado Esperado:**
* La ejecución de `poetry run pytest` debía validar la migración de Pydantic V2, resultando en una suite de tests limpia, sin errores ni advertencias.

**Resultado Real:**
* Fallo masivo de la suite de tests con 67 fallos y 13 errores.
* Reaparición de `SystemError: AST constructor recursion depth mismatch`.
* Reaparición de `RuntimeError: Event loop is closed` y errores de `asyncio` relacionados con `psycopg_pool`.

**Análisis de Falla:**
* La hipótesis de que solo era necesaria una migración de sintaxis de Pydantic fue incorrecta.
* La modificación en `prompt_models.py`, aunque sintácticamente correcta, expuso una fragilidad subyacente en la configuración del entorno de pruebas.
* La causa raíz no está en los modelos de dominio, sino en una configuración defectuosa en `tests/conftest.py` que no gestiona de forma robusta el ciclo de vida del `event loop` de `asyncio` y el `pool` de conexiones a la base de datos a lo largo de toda la suite de tests. El error `AST` es un síntoma de esta inestabilidad.

**Lección Aprendida y Nueva Hipótesis:**
* **Lección Aprendida:** No se debe asumir que un problema está resuelto permanentemente solo porque un informe anterior lo indica. Las modificaciones, incluso las pequeñas, pueden revelar problemas latentes. Es necesario validar el estado del sistema de forma más integral.
* **Nueva Hipótesis Central:** La inestabilidad de la suite de tests se origina en `tests/conftest.py`. La gestión del `event_loop` y del `db_session` es inadecuada para una ejecución completa de pytest, causando fugas de recursos y fallos en cascada. La solución requiere una refactorización del fixture de base de datos para garantizar que las conexiones y el bucle de eventos se creen y destruyan correctamente una sola vez por sesión de prueba.

---

### INFORME POST-MORTEM - 12/06/2025 16:46

**REFERENCIA A INTENTOS PREVIOS:**
* Este informe sigue a la ejecución de la "OPERACIÓN: ESTABILIZACIÓN DEL CICLO DE VIDA ASÍNCRONO DE TESTS", que refactorizó `tests/conftest.py`.

**Resultado Esperado:**
* La ejecución de `poetry run pytest` debía resultar en una suite de pruebas estable, libre de errores de `RuntimeError` y `SystemError`, aunque se esperaban fallos de lógica de negocio.

**Resultado Real:**
* La suite de pruebas ha fallado masivamente con 97 fallos y 139 errores.
* Los errores de ciclo de vida de `asyncio` (`Event loop is closed`) han sido eliminados, validando la Fase 3A.
* Sin embargo, ha surgido una nueva clase de errores sistémicos:
    1.  **`TypeError` en la inicialización de servicios:** Múltiples `fixtures` intentan instanciar clases de servicio (`TradingEngine`, `BinanceAdapter`, `AIOrchestratorService`, etc.) sin proporcionar los argumentos requeridos en sus constructores (`__init__`).
    2.  **`ValidationError` de Pydantic:** Múltiples pruebas intentan crear instancias de modelos de Pydantic (`Trade`, `KlineData`, `Order`, etc.) con datos incorrectos o campos faltantes.
    3.  **`AttributeError` en `async_generator`:** Las pruebas de API intentan usar el `client` de `TestClient` como un objeto directo en lugar de un generador asíncrono, causando errores como `AttributeError: 'async_generator' object has no attribute 'get'`.
    4.  **`PoolTimeout` en `test_persistence_service.py`:** A pesar de la nueva `fixture`, el `SupabasePersistenceService` sigue intentando usar su propio pool de conexiones interno en lugar de la sesión transaccional proporcionada por la `fixture`, lo que lleva a timeouts.

**Análisis de Falla:**
* La hipótesis de que solo el ciclo de vida de `asyncio` estaba roto fue incompleta. La corrección de ese problema ha destapado una erosión masiva de la integridad de las pruebas unitarias y de integración.
* Las `fixtures` de prueba no han sido mantenidas y están desincronizadas con las firmas de los constructores de las clases que instancian.
* Los datos de prueba (mocks y datos para modelos Pydantic) son inválidos y no cumplen con los esquemas actuales de los modelos.
* La interacción con el `TestClient` de FastAPI en las pruebas de API es incorrecta.

**Lección Aprendida y Nueva Hipótesis:**
* **Lección Aprendida:** Una suite de pruebas que no se mantiene activamente se convierte en deuda técnica. Los cambios en el código de la aplicación deben ser reflejados inmediatamente en las pruebas correspondientes. La estabilidad de la suite es un indicador clave de la salud del proyecto.
* **Nueva Hipótesis Central:** La causa raíz de la falla actual es una **desintegración sistémica de la suite de pruebas**. Las pruebas no reflejan el estado actual del código fuente. La solución no es un único arreglo, sino una campaña de refactorización de pruebas dividida en fases, enfocada en restaurar la coherencia entre las pruebas y el código de la aplicación. Se debe comenzar por el problema más fundamental: la instanciación incorrecta de objetos en las `fixtures`.
