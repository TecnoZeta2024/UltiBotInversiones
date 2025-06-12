### INFORME DE ESTADO Y PLAN DE ACCIÓN - 12/06/2025 14:16

**ESTADO ACTUAL:**
* Iniciando FASE 2: HIPÓTESIS Y PLAN DE ACCIÓN UNIFICADO. Persisten 10 errores de importación internos y error nativo de psycopg/libpq.

**REFERENCIA A INFORMES PREVIOS:**
* Ver informe previo de avance 6/12/2025 14:08 y plan granular en AUDIT_TASK.md. El entorno virtual, arquitectura y DI están estables. Los logs no muestran errores críticos de ejecución.

**1. OBSERVACIONES (Resultados de FASE 1):**
* Los errores actuales son:
  - `ModuleNotFoundError: No module named 'ultibot_backend.api.services'` y rutas similares.
  - `ImportError: no pq wrapper available. Attempts made: ... libpq library not found` (psycopg).
* El archivo `pytest.ini` ya incluye `pythonpath = .`, descartando problemas de PYTHONPATH.
* Todos los `__init__.py` requeridos parecen presentes, pero persisten errores de importación absoluta.
* No hay evidencia de fallos de entorno virtual ni de dependencias externas en los logs.

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**
* La causa raíz de los errores de importación es una combinación de:
  1. Imports absolutos incorrectos en algunos módulos (ej. `ultibot_backend.api.services` no existe como paquete, debería ser `ultibot_backend.services`).
  2. Posibles referencias a rutas de módulos que han cambiado tras la refactorización hexagonal.
  3. Falta de la librería nativa `libpq` en el sistema operativo Windows, impidiendo que psycopg funcione.

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**
| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| src/ultibot_backend/api/v1/router.py<br>src/ultibot_backend/api/v1/endpoints/*<br>src/ultibot_backend/adapters/persistence_service.py | Corregir imports absolutos: reemplazar `ultibot_backend.api.services` por `ultibot_backend.services` y ajustar cualquier import obsoleto tras la refactorización | Elimina los `ModuleNotFoundError` y alinea los imports con la estructura hexagonal actual |
| src/ultibot_backend/adapters/persistence_service.py | Validar que el import de psycopg sea correcto y no se intente cargar si falta la librería nativa | Previene fallos de importación y permite manejo de errores más claro |
| Sistema operativo (Windows) | Instalar la librería nativa de PostgreSQL (`libpq.dll`). Recomendado: instalar el cliente oficial de PostgreSQL y agregar la carpeta `bin` al PATH | Permite que psycopg encuentre y cargue la librería nativa, resolviendo el error `no pq wrapper available` |

**4. RIESGOS POTENCIALES:**
* Imports incorrectos pueden romper endpoints si no se ajustan todos los archivos afectados.
* Instalación de `libpq` puede requerir reinicio de terminal o ajustes de PATH.
* Si existen rutas de import obsoletas en tests, también deben corregirse.

**5. SOLICITUD:**
* [**PAUSA**] Espero aprobación para proceder con la ejecución del plan de corrección de imports internos y resolución de la dependencia nativa de PostgreSQL.

---
2. Patrones arquitectónicos obsoletos ❌ 
3. Incompatibilidad total con la BaseStrategy moderna ❌

**Esto explica por qué:**
- El contexto de traspaso las marcaba como "pendientes" (no eran utilizables)
- Los tests fallan sistemáticamente (incompatibilidad de modelos)
- No están integradas en el sistema de DI actual

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**

### OPERACIÓN: "MIGRACIÓN ARQUITECTÓNICA DE ESTRATEGIAS"

| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| **FASE 3A: REFACTORIZACIÓN DE MODELOS DE DOMINIO** |
| `src/ultibot_backend/core/domain_models/trading.py` | Extender `StrategyParameters` con campos específicos para cada tipo de estrategia usando Union types | Permite compatibilidad con BaseStrategy manteniendo flexibilidad de parámetros específicos |
| `src/ultibot_backend/strategies/base_strategy.py` | Actualizar firma de métodos y imports para alinearse con arquitectura hexagonal | Establece interfaz consistente que todas las estrategias deben seguir |
| **FASE 3B: MIGRACIÓN DE ESTRATEGIAS (1/7)** |
| `src/ultibot_backend/strategies/supertrend_volatility_filter.py` | Refactorizar para usar BaseStrategy + StrategyParameters estándar + imports correctos | Convierte estrategia funcional en compatible arquitectónicamente |
| **FASE 3C: CORRECCIÓN DE TESTS** |
| `tests/unit/strategies/test_supertrend_volatility_filter.py` | Crear/actualizar tests usando nuevos modelos compatibles + async support | Garantiza que la migración mantiene funcionalidad y calidad |
| **FASE 3D: VALIDACIÓN Y REPETICIÓN** |
| Repetir FASES 3B-3C para las 6 estrategias restantes | Migrar una por una: VWAP, Stochastic RSI, Statistical Arbitrage, Order Book, News Sentiment, OnChain Metrics | Proceso controlado que valida cada estrategia antes de continuar |

### ENFOQUE INCREMENTAL:
1. **Migrar 1 estrategia completa** (SuperTrend) como piloto
2. **Validar funcionamiento** con tests e integración
3. **Aplicar patrón** a las 6 restantes
4. **Integración final** con sistema de DI y endpoints

**4. RIESGOS POTENCIALES:**
* **Pérdida de lógica de negocio**: Mitigado por preservar toda la lógica matemática existente
* **Regresión en tests**: Controlado por validación incremental estrategia por estrategia  
* **Incompatibilidad con UI**: Manejado manteniendo contratos de API existentes

**5. SOLICITUD:**
* [**PAUSA**] Espero aprobación para proceder con la ejecución del plan de MIGRACIÓN ARQUITECTÓNICA DE ESTRATEGIAS.

---

### INFORME DE ESTADO Y PLAN DE ACCIÓN - 6/12/2025 10:00 AM

**ESTADO ACTUAL:**
* Iniciando FASE 4: CORRECCIÓN DE TESTS DE ESTRATEGIA (SuperTrendVolatilityFilter).

**REFERENCIA A INFORMES PREVIOS:**
* Se ha completado la FASE 3A (Refactorización de Modelos de Dominio) y FASE 3B (Migración de Estrategia Piloto - SuperTrendVolatilityFilter).
* Los tests para `supertrend_volatility_filter` están fallando (2 de 8).

**1. OBSERVACIONES (Resultados de FASE 1):**
* **`src/ultibot_backend/strategies/supertrend_volatility_filter.py`:** La implementación de `_apply_volatility_filter` utiliza `statistics.quantiles(..., n=100)` y luego intenta acceder a los índices `0` y `100` para `min_percentile=0.0` y `max_percentile=100.0`. Sin embargo, `statistics.quantiles(n=100)` devuelve una lista de 99 cuantiles (percentiles 1 al 99), lo que causa un `IndexError` cuando se intenta acceder al índice `100`. Esto provoca que el filtro de volatilidad falle inesperadamente en los tests de señal, donde se espera que pase.
* **`tests/unit/strategies/test_supertrend_volatility_filter.py`:** El fixture `default_params` ya establece `min_volatility_percentile=0.0` y `max_volatility_percentile=100.0`, lo cual es correcto para hacer que el filtro de volatilidad sea trivialmente verdadero en los tests de señal, permitiendo que pasen.

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**
La causa raíz de los tests fallidos (`test_analyze_generates_buy_signal` y `test_analyze_generates_sell_signal`) es un `IndexError` silencioso dentro de `_apply_volatility_filter` en `src/ultibot_backend/strategies/supertrend_volatility_filter.py` cuando se intenta acceder a los percentiles 0 y 100 usando `statistics.quantiles`. Esto hace que `volatility_filter_passed` sea `False` cuando debería ser `True`.

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**
| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| `src/ultibot_backend/strategies/supertrend_volatility_filter.py` | Modificar la función `_apply_volatility_filter` para manejar correctamente los casos de `min_percentile=0.0` y `max_percentile=100.0`. Si `min_percentile` es `0.0`, `min_threshold` debe ser el valor mínimo de `recent_atr`. Si `max_percentile` es `100.0`, `max_threshold` debe ser el valor máximo de `recent_atr`. Para otros percentiles, se seguirá usando `statistics.quantiles`. | Esto corregirá el `IndexError` y asegurará que el filtro de volatilidad se comporte como se espera en los tests de señal, permitiendo que pasen. |
| N/A | Ejecutar los tests para `test_supertrend_volatility_filter.py` hasta que los 8 tests pasen. | Validar que la corrección en `_apply_volatility_filter` resuelve los fallos de los tests de señal y no introduce regresiones. |

**4. RIESGOS POTENCIALES:**
*   **Introducción de nuevos errores lógicos**: Al modificar la lógica de los percentiles, existe un riesgo bajo de introducir un error en el cálculo del filtro de volatilidad para otros rangos de percentiles. Mitigado por la ejecución de todos los tests unitarios, incluyendo `test_analyze_volatility_filter_fails`.

**5. SOLICITUD:**
* [**PAUSA**] Espero aprobación para proceder con la ejecución del plan de CORRECCIÓN DE TESTS DE ESTRATEGIA.

---

### INFORME DE ESTADO Y PLAN DE ACCIÓN - 6/12/2025 10:09 AM

**ESTADO ACTUAL:**
* Completada la corrección de `ImportError: cannot import name 'StrategyParameters'`.

**REFERENCIA A INFORMES PREVIOS:**
* Se ha completado la FASE 3A (Refactorización de Modelos de Dominio) y FASE 3B (Migración de Estrategia Piloto - SuperTrendVolatilityFilter).
* Se han corregido los `ImportError` en `src/ultibot_backend/strategies/bollinger_squeeze_breakout.py`, `src/ultibot_backend/strategies/triangular_arbitrage.py`, `src/ultibot_backend/strategies/macd_rsi_trend_rider.py` y `src/ultibot_backend/core/domain_models/__init__.py`.

**1. OBSERVACIONES (Resultados de FASE 1):**
* Los `ImportError: cannot import name 'StrategyParameters'` han sido resueltos en los archivos identificados.
* Persisten los `ModuleNotFoundError: No module named 'asgi_correlation_id'`, `PySide6`, `injector`, `psycopg`, `langchain_google_genai`. Esto sugiere un problema con el entorno de Python o la instalación de dependencias.

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**
La causa raíz de los `ModuleNotFoundError` es una instalación incompleta o corrupta de las dependencias del proyecto. Esto podría deberse a un entorno virtual no activado correctamente, problemas con `pip` o `poetry`, o dependencias faltantes en `pyproject.toml`.

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**
| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| N/A | Ejecutar `poetry install` para asegurar que todas las dependencias del proyecto estén correctamente instaladas y el entorno virtual esté configurado. | Esto debería resolver los `ModuleNotFoundError` al instalar las librerías faltantes o corregir cualquier problema de instalación. |
| N/A | Ejecutar los tests para `test_supertrend_volatility_filter.py` y observar los resultados. | Verificar si las correcciones de importación y la reinstalación de dependencias han resuelto los errores y si los tests pasan. |

**4. RIESGOS POTENCIALES:**
*   **`poetry install` falla**: Podría haber problemas con la configuración de `poetry` o con las fuentes de los paquetes. Mitigado por la capacidad de depurar la salida de `poetry`.
*   **Los `ModuleNotFoundError` persisten**: Si `poetry install` no resuelve el problema, podría indicar un problema más profundo con el entorno de Python o con el `pyproject.toml`.

**5. SOLICITUD:**
* [**PAUSA**] Espero aprobación para proceder con la ejecución del plan de RE-EVALUACIÓN DE DEPENDENCIAS Y EJECUCIÓN DE TESTS.

---

### INFORME DE AVANCE - 6/12/2025 14:08

**FASE 3: REINSTALACIÓN DE DEPENDENCIAS Y VALIDACIÓN DE ENTORNO — AVANCE REGISTRADO**

**1. ACCIONES REALIZADAS:**
- Se revisó y sincronizó el archivo `pyproject.toml` para asegurar que todas las dependencias críticas (`asgi-correlation-id`, `langchain-google-genai`, `injector`, `psycopg`, `PySide6`) estuvieran correctamente declaradas.
- Se forzó la instalación de dependencias tanto con `poetry install`, `poetry sync` como con `pip install` y `poetry run pip install` dentro del entorno virtual de Poetry.
- Se validó que los paquetes requeridos están presentes en el entorno virtual de Poetry.
- Se ejecutó `poetry run pytest --collect-only -q` y se logró que la mayoría de los tests sean recolectados exitosamente.
- Persisten **10 errores de importación** (antes eran 18), pero **ya no son por dependencias externas** sino por:
  - Errores de import relativos/rutas: `ModuleNotFoundError: No module named 'ultibot_backend.api.services'`
  - Problemas con la carga de la librería nativa de `psycopg`: `ImportError: no pq wrapper available. Attempts made: ... libpq library not found`

**2. INTERPRETACIÓN:**
- El entorno virtual y las dependencias externas críticas están ahora correctamente instaladas y visibles para Poetry y pytest.
- Los errores actuales son de **estructura de imports internos** y de **dependencias nativas del sistema** (falta de la librería `libpq` para PostgreSQL en el sistema operativo).
- El avance es significativo: el sistema pasó de errores de entorno y dependencias a errores de integración interna y de entorno SO.

**3. SIGUIENTES PASOS RECOMENDADOS:**
- Corregir los imports relativos y rutas de módulos en los archivos afectados (`ultibot_backend.api.services`).
- Instalar la librería nativa de PostgreSQL (`libpq`/`libpq-dev` o equivalente para Windows) para que `psycopg` funcione correctamente.
- Documentar cualquier otro error nuevo que surja tras estas correcciones.

**4. ESTADO ACTUAL:**
- El entorno de desarrollo Python está **casi completamente funcional**.
- El siguiente cuello de botella es la integración de imports internos y la dependencia nativa de PostgreSQL.

---

### INFORME DE ESTADO Y PLAN DE ACCIÓN - 12/06/2025 14:16

**ESTADO ACTUAL:**
* Iniciando FASE 2: HIPÓTESIS Y PLAN DE ACCIÓN UNIFICADO. Persisten 10 errores de importación internos y error nativo de psycopg/libpq.

**REFERENCIA A INFORMES PREVIOS:**
* Ver informe previo de avance 6/12/2025 14:08 y plan granular en AUDIT_TASK.md. El entorno virtual, arquitectura y DI están estables. Los logs no muestran errores críticos de ejecución.

**1. OBSERVACIONES (Resultados de FASE 1):**
* Los errores actuales son:
  - `ModuleNotFoundError: No module named 'ultibot_backend.api.services'` y rutas similares.
  - `ImportError: no pq wrapper available. Attempts made: ... libpq library not found` (psycopg).
* El archivo `pytest.ini` ya incluye `pythonpath = .`, descartando problemas de PYTHONPATH.
* Todos los `__init__.py` requeridos parecen presentes, pero persisten errores de importación absoluta.
* No hay evidencia de fallos de entorno virtual ni de dependencias externas en los logs.

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**
* La causa raíz de los errores de importación es una combinación de:
  1. Imports absolutos incorrectos en algunos módulos (ej. `ultibot_backend.api.services` no existe como paquete, debería ser `ultibot_backend.services`).
  2. Posibles referencias a rutas de módulos que han cambiado tras la refactorización hexagonal.
  3. Falta de la librería nativa `libpq` en el sistema operativo Windows, impidiendo que psycopg funcione.

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**
| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| src/ultibot_backend/api/v1/router.py<br>src/ultibot_backend/api/v1/endpoints/*<br>src/ultibot_backend/adapters/persistence_service.py | Corregir imports absolutos: reemplazar `ultibot_backend.api.services` por `ultibot_backend.services` y ajustar cualquier import obsoleto tras la refactorización | Elimina los `ModuleNotFoundError` y alinea los imports con la estructura hexagonal actual |
| src/ultibot_backend/adapters/persistence_service.py | Validar que el import de psycopg sea correcto y no se intente cargar si falta la librería nativa | Previene fallos de importación y permite manejo de errores más claro |
| Sistema operativo (Windows) | Instalar la librería nativa de PostgreSQL (`libpq.dll`). Recomendado: instalar el cliente oficial de PostgreSQL y agregar la carpeta `bin` al PATH | Permite que psycopg encuentre y cargue la librería nativa, resolviendo el error `no pq wrapper available` |

**4. RIESGOS POTENCIALES:**
* Imports incorrectos pueden romper endpoints si no se ajustan todos los archivos afectados.
* Instalación de `libpq` puede requerir reinicio de terminal o ajustes de PATH.
* Si existen rutas de import obsoletas en tests, también deben corregirse.

**5. SOLICITUD:**
* [**PAUSA**] Espero aprobación para proceder con la ejecución del plan de corrección de imports internos y resolución de la dependencia nativa de PostgreSQL.

---
---

### INFORME DE ESTADO Y PLAN DE ACCIÓN - 12/06/2025 14:54

**ESTADO ACTUAL:**
* Dependencia nativa de `psycopg` resuelta. Plan de acción refinado y listo para aprobación.

**REFERENCIA A INFORMES PREVIOS:**
* El usuario ha confirmado la instalación de la librería `libpq.dll` y la verificación con `scripts/verify_psycopg.py` fue exitosa.
* El único bloqueo restante es la corrección de los imports internos.

**1. OBSERVACIONES (Resultados de FASE 1):**
* **Error Primario:** El único problema de software restante es el uso de rutas de importación obsoletas (`ultibot_backend.api.services` en lugar de `ultibot_backend.services`).
* **Alcance:** El error afecta a `router.py`, múltiples endpoints y `persistence_service.py`.

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**
* La causa raíz de la inoperabilidad del sistema es únicamente el desajuste de los imports internos tras la refactorización a la arquitectura hexagonal. Corregir estos imports debería estabilizar el sistema y permitir la ejecución de tests.

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**

### OPERACIÓN: "ALINEACIÓN ARQUITECTÓNICA DE IMPORTS"

| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| **FASE 3A: CORRECCIÓN DE IMPORTS** |
| `src/ultibot_backend/api/v1/router.py` | Corregir los imports de `ultibot_backend.api.services` a `ultibot_backend.services`. | Alinea el router con la arquitectura hexagonal. |
| `src/ultibot_backend/api/v1/endpoints/*.py` | Corregir las rutas de importación de servicios en todos los endpoints afectados. | Permite que los endpoints localicen los servicios del núcleo. |
| `src/ultibot_backend/adapters/persistence_service.py` | Corregir cualquier import de servicio incorrecto. | Asegura la correcta referenciación de los servicios. |
| **FASE 3B: VALIDACIÓN** |
| N/A | Ejecutar `poetry run pytest --collect-only -q`. | **Criterio de Éxito:** El comando debe ejecutarse sin errores de importación. |
| N/A | Ejecutar `poetry run pytest`. | **Criterio de Éxito:** Los tests deben ejecutarse, revelando cualquier error lógico subyacente. |

**4. RIESGOS POTENCIALES:**
* **Correcciones Incompletas:** Mitigado mediante una búsqueda exhaustiva de la ruta de import incorrecta en todo el proyecto.
* **Errores Lógicos Subyacentes:** Esperado. Este plan desbloqueará la capacidad de detectar y depurar dichos errores.

**5. SOLICITUD:**
* [**PAUSA**] Espero aprobación para proceder con la ejecución de la **FASE 3A: CORRECCIÓN DE IMPORTS**.

---

### INFORME DE ESTADO Y PLAN DE ACCIÓN - 12/06/2025 15:49

**ESTADO ACTUAL:**
* Completada la corrección de errores de importación de `MarketSnapshot` a `MarketData`.
* Se han resuelto todos los `ImportError` relacionados con `MarketSnapshot` en los archivos de estrategias y endpoints.
* La recolección de tests (`poetry run pytest --collect-only -q`) ahora se ejecuta sin errores de importación.

**REFERENCIA A INFORMES PREVIOS:**
* Este informe es una continuación de la "Task Continuation: Corrección Holística de Errores de Importación (Fase 2)".
* Se han corregido los archivos:
    - `src/ultibot_backend/strategies/vwap_cross_strategy.py`
    - `src/ultibot_backend/strategies/order_book_imbalance_scalper.py`
    - `src/ultibot_backend/strategies/news_sentiment_spike_trader.py`
    - `src/ultibot_backend/strategies/onchain_metrics_divergence.py`
* Se ha verificado que los imports de `MarketSnapshot` han sido reemplazados por `MarketData` y los type hints ajustados.

**1. OBSERVACIONES (Resultados de FASE 1):**
* La ejecución completa de los tests (`poetry run pytest`) ha revelado nuevos problemas:
    * **68 fallos y 13 errores.**
    * **Error Crítico:** `SystemError: AST constructor recursion depth mismatch` - Este es un error interno de Python/pytest, no un error de código del proyecto. Sugiere un problema con la complejidad del código o un límite de recursión en el intérprete de Python durante el análisis de AST por parte de pytest.
    * **Errores de `asyncio`:** Múltiples `RuntimeError: Event loop is closed` y `Task was destroyed but it is pending!` relacionados con `psycopg_pool` y `asyncio`. Esto indica problemas con la gestión del ciclo de vida de las conexiones asíncronas a la base de datos durante la ejecución de los tests.
    * **Advertencias de `PydanticDeprecatedSince20`:** Numerosas advertencias sobre el uso de `@validator` y `json_encoders` de Pydantic v1, que están obsoletas en Pydantic v2. Esto es deuda técnica y no un error que impida la ejecución, pero debe abordarse.
    * **Advertencia `PytestConfigWarning: Unknown config option: dotenv_files`:** Indica una configuración desconocida en `pytest.ini`.
    * **Advertencia `PendingDeprecationWarning: Please use `import python_multipart` instead.`:** Relacionada con `starlette/formparsers.py`.

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**
* La fase de corrección de errores de importación está completa. Los problemas actuales son de una naturaleza diferente:
    1.  **Problemas de entorno/configuración de Pytest:** El `SystemError` y las advertencias de configuración sugieren que Pytest no está configurado óptimamente o que hay un problema con el entorno de ejecución que excede los límites de recursión del analizador AST.
    2.  **Gestión de Conexiones Asíncronas:** Los errores de `asyncio` y `psycopg_pool` indican que los tests no están manejando correctamente el cierre de las conexiones a la base de datos o el ciclo de vida del bucle de eventos asíncrono, lo que lleva a la destrucción de tareas pendientes.
    3.  **Deuda Técnica de Pydantic:** Las advertencias de Pydantic v1 a v2 son un problema de deuda técnica que debe ser migrado para mantener la compatibilidad y el rendimiento.

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**

### OPERACIÓN: "DIAGNÓSTICO Y RESOLUCIÓN DE ERRORES DE EJECUCIÓN DE TESTS"

| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| **FASE 3A: DIAGNÓSTICO Y MITIGACIÓN DE ERRORES DE ENTORNO/PYTEST** |
| N/A | Investigar el `SystemError: AST constructor recursion depth mismatch`. Esto podría requerir ajustar la configuración de Python o Pytest, o identificar archivos de código excesivamente complejos que causen este problema. | Resolver un error crítico que impide la ejecución completa de los tests. |
| `pytest.ini` | Eliminar la opción `dotenv_files` si no es necesaria o corregirla si hay una alternativa para Pytest 8.4.0. | Limpiar advertencias de configuración y asegurar que Pytest se inicialice correctamente. |
| **FASE 3B: CORRECCIÓN DE GESTIÓN DE CONEXIONES ASÍNCRONAS** |
| `tests/conftest.py` y tests relevantes | Revisar y ajustar la configuración de los fixtures de `pytest-asyncio` y la gestión de la piscina de conexiones de `psycopg_pool` para asegurar un cierre limpio del bucle de eventos y las conexiones. | Eliminar los `RuntimeError: Event loop is closed` y `Task was destroyed but it is pending!` que indican fugas de recursos o cierres prematuros. |
| **FASE 3C: MIGRACIÓN DE Pydantic V1 a V2** |
| Archivos con advertencias `@validator` y `json_encoders` | Migrar el uso de `@validator` a `@field_validator` y `json_encoders` a `model_dump_json` o `json_schema_extra` según la guía de migración de Pydantic V2. | Reducir la deuda técnica, mejorar la compatibilidad y prepararse para futuras versiones de Pydantic. |
| **FASE 3D: VALIDACIÓN FINAL** |
| N/A | Ejecutar `poetry run pytest`. | **Criterio de Éxito:** Todos los tests deben ejecutarse sin errores ni fallos, y el número de advertencias debe reducirse significativamente. |

---

### INFORME DE ESTADO Y PLAN DE ACCIÓN - 12/06/2025 16:37

**ESTADO ACTUAL:**
* **FASE DE VALIDACIÓN FALLIDA.** La corrección masiva de importaciones fue exitosa para resolver los errores de recolección de `pytest`. Sin embargo, la ejecución de la suite de pruebas ahora falla catastróficamente con errores de `asyncio` y un `SystemError` fatal.

**REFERENCIA A INFORMES PREVIOS:**
* El plan del `12/06/2025 15:59` sobre la gestión de estado asíncrono es ahora la principal línea de investigación.

**1. OBSERVACIONES (Resultados de FASE 1):**
* **Éxito Parcial:** La estandarización de `from ultibot_backend...` ha eliminado todos los errores de `ModuleNotFoundError` y de recolección de `pytest`.
* **Nuevos Errores Críticos:** La ejecución de `pytest` ahora produce:
    * Múltiples errores `RuntimeError: Event loop is closed`.
    * Múltiples advertencias `Task was destroyed but it is pending!`.
    * Un `SystemError: AST constructor recursion depth mismatch` que aborta la sesión de tests.
* **Análisis de Causa:** Estos errores son sintomáticos de una gestión incorrecta del ciclo de vida de los recursos asíncronos, particularmente los pools de conexiones de `psycopg_pool` para Supabase, a lo largo de la suite de pruebas. Las `fixtures` actuales no garantizan que los `event loops` y las conexiones se creen y destruyan de forma limpia y ordenada.

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**
* La causa raíz de la inestabilidad actual de la suite de pruebas es una gestión deficiente y no centralizada del ciclo de vida de los recursos asíncronos. La corrección de los imports ha permitido que los tests se ejecuten, exponiendo este problema subyacente. La solución requiere refactorizar las `fixtures` en `tests/conftest.py` para manejar correctamente el `event loop` de `asyncio` y las conexiones a la base de datos con un `scope` adecuado.

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**

### OPERACIÓN: "ESTABILIZACIÓN DEL CICLO DE VIDA ASÍNCRONO DE TESTS"

| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| **FASE 3A: REFACTORIZACIÓN DE `conftest.py`** |
| `tests/conftest.py` | Reemplazar el contenido actual para introducir `fixtures` robustas: <br> 1. **`event_loop`**: Crear un `fixture` con `scope="session"` que provea un único `event loop` para toda la duración de la sesión de `pytest`. <br> 2. **`db_session`**: Crear un `fixture` asíncrono, también con `scope="session"`, que utilice el `event_loop` para establecer una única conexión a la base de datos, la ceda (`yield`) a los tests, y garantice su cierre limpio al finalizar todos los tests. <br> 3. **`sys.path`**: Mantener la lógica existente que añade `src` al `sys.path` para asegurar que los imports `from ultibot_backend` sigan funcionando. | Esta refactorización implementa un patrón estándar y robusto para tests asíncronos. Centraliza la gestión de recursos, previene fugas de conexiones y `event loops`, y elimina la causa raíz de los `RuntimeError` y el `SystemError`, creando un entorno de prueba estable. |
| **FASE 3B: VALIDACIÓN INICIAL** |
| `tests/unit/adapters/test_persistence_service.py` | Adaptar este archivo de test para que utilice la nueva `fixture` `db_session`. Esto servirá como prueba de concepto. | Permite validar el nuevo enfoque en un conjunto aislado de tests antes de aplicarlo a toda la suite, facilitando la depuración. |
| **FASE 3C: VALIDACIÓN COMPLETA** |
| N/A | Ejecutar `poetry run pytest`. | **Criterio de Éxito:** La suite de tests debe ejecutarse completamente sin errores de `RuntimeError` o `SystemError`. Los fallos lógicos (`F`) pueden persistir y serán abordados posteriormente, pero el entorno de ejecución debe ser estable. |

**4. RIESGOS POTENCIALES:**
* **Mínimos.** La implementación sigue las mejores prácticas de `pytest-asyncio`. El riesgo principal es que algunos tests requieran ajustes para consumir las nuevas `fixtures`, lo cual es parte del proceso de refactorización.

**5. SOLICITUD:**
* [**PAUSA**] Espero aprobación para proceder con la ejecución de la **FASE 3A: REFACTORIZACIÓN DE `conftest.py`**.

---

### INFORME DE ESTADO Y PLAN DE ACCIÓN - 12/06/2025 16:47

**ESTADO ACTUAL:**
* **FALLO CATASTRÓFICO DE LA SUITE DE PRUEBAS.** La estabilización del ciclo de vida asíncrono ha revelado una desintegración sistémica de las pruebas.

**REFERENCIA A INFORMES PREVIOS:**
* Ver `AUDIT_MORTEN.md` con fecha `12/06/2025 16:46` para un análisis detallado de la falla.

**1. OBSERVACIONES (Resultados de FASE 1):**
* La ejecución de `poetry run pytest` resultó en **97 fallos y 139 errores**.
* Los errores de ciclo de vida de `asyncio` fueron resueltos, pero esto expuso problemas más profundos.
* **Errores Sistémicos Identificados:**
    1.  **`TypeError` en `__init__`**: Las `fixtures` no proveen los argumentos correctos a los constructores de los servicios.
    2.  **`ValidationError` de Pydantic**: Los datos de prueba son inválidos para los modelos de Pydantic.
    3.  **`AttributeError` en `TestClient`**: Uso incorrecto del cliente de pruebas de FastAPI.
    4.  **`PoolTimeout`**: El servicio de persistencia no utiliza la `fixture` de sesión de base de datos inyectada.

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**
* La causa raíz es una **desintegración sistémica de la suite de pruebas**. Las pruebas no reflejan el estado actual del código fuente. La solución requiere una campaña de refactorización de pruebas por fases.

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 4):**

### OPERACIÓN: "RESTAURACIÓN DE INTEGRIDAD DE LA SUITE DE PRUEBAS"

| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| **FASE 4A: REFACTORIZACIÓN DE `SupabasePersistenceService`** |
| `src/ultibot_backend/adapters/persistence_service.py` | Modificar el constructor `__init__` para aceptar una `AsyncSession` opcional. Si se provee, el servicio usará esa sesión en lugar de su propio pool. | Resuelve el `PoolTimeout` al permitir la inyección de dependencias de la sesión de BD, desacoplando el servicio y haciéndolo testeable. |
| `tests/unit/adapters/test_persistence_service.py` | Actualizar la `fixture` `persistence_service` para inyectar la `db_session` en el constructor del servicio. | Alinea la prueba con el servicio refactorizado para una validación de integración real. |
| **FASE 4B: CORRECCIÓN DE `TypeError` EN FIXTURES** |
| `tests/unit/services/*.py`, `tests/integration/*.py` | Corregir todas las `fixtures` que instancian servicios para que provean los argumentos requeridos por los constructores. | Elimina los errores de `setup` y permite que los tests de servicio se ejecuten. |
| **FASE 4C: CORRECCIÓN DE `ValidationError` EN DATOS DE PRUEBA** |
| `tests/**/*.py` | Revisar y corregir todos los datos de prueba que causan `ValidationError` para que cumplan con los esquemas de los modelos Pydantic. | Asegura que los modelos de dominio se instancien correctamente, permitiendo probar la lógica de negocio. |
| **FASE 4D: CORRECCIÓN DE PRUEBAS DE API** |
| `tests/integration/api/v1/*.py` | Refactorizar las pruebas de API para manejar correctamente el `TestClient` como un generador de contexto asíncrono (`async with`). | Corrige el uso del cliente de prueba de FastAPI, permitiendo que los tests de endpoints se ejecuten. |
| **FASE 4E: VALIDACIÓN INCREMENTAL** |
| N/A | Ejecutar `poetry run pytest` después de cada fase. | Permite un enfoque controlado, asegurando que cada clase de error se resuelva antes de continuar. |

**4. RIESGOS POTENCIALES:**
* **Complejidad de la Refactorización:** La corrección de las `fixtures` puede ser compleja si las dependencias son profundas. Se mitigará abordando los errores de manera incremental.
* **Descubrimiento de Nuevos Errores:** Es probable que la corrección de una capa de errores revele otros problemas lógicos. Esto es esperado y es el objetivo de la operación.

**5. SOLICITUD:**
* [**PAUSA**] Espero aprobación para proceder con la **FASE 4A** del plan de **RESTAURACIÓN DE INTEGRIDAD DE LA SUITE DE PRUEBAS**.
