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
* **Pérdida de lógica de negocio**: Migitado por preservar toda la lógica matemática existente
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
* **`tests/unit/strategies/test_supertrend_volatility_filter.py`:** El fixture `default_params` ya establece `min_volatility_percentile=0.0` y `max_volatility_percentile=100.0`, lo cual es correcto para hacer que el filtro de volatilidad sea trivialmente verdadero en los tests de señal.

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

### INFORME DE ESTADO Y PLAN DE ACCIÓN - 6/12/2025 12:09 PM

**ESTADO ACTUAL:**
* Iniciando FASE 1: ANÁLISIS SISTÉMICO - PROBLEMA PYTHONPATH CRÍTICO IDENTIFICADO

**REFERENCIA A INFORMES PREVIOS:**
* Los informes anteriores se centraron en estrategias y dependencias, pero el problema central es más fundamental.
* El error FastAPI mencionado en `AUDIT_TASK.md` no es visible debido a problemas de importación más básicos.

**1. OBSERVACIONES (Resultados de FASE 1):**

### PROBLEMA CRÍTICO IDENTIFICADO: SISTEMA DE IMPORTS COMPLETAMENTE ROTO

**Test Collection Results:**
* ❌ **28 ERRORES de importación + 0 correcciones exitosas**
* **Error Principal**: `ModuleNotFoundError: No module named 'src'` 
* **Afecta**: 100% de tests de integración y unidad que importan el código principal
* **Solo 15 tests se recolectan** (únicamente los que no importan `src`)

**Archivos Afectados por Import Errors:**
```
- tests/integration/api/v1/endpoints/test_performance_endpoints.py
- tests/integration/test_ai_orchestrator_integration.py  
- tests/unit/adapters/test_binance_adapter.py
- tests/unit/services/test_ai_orchestrator_service.py
- tests/unit/strategies/test_bollinger_squeeze_breakout.py
- tests/unit/strategies/test_macd_rsi_trend_rider.py
- tests/unit/strategies/test_triangular_arbitrage.py
- [+ 21 archivos más con el mismo problema]
```

**Dependencias Adicionales Faltantes:**
* `psycopg` (PostgreSQL adapter)
* `asgi_correlation_id`
* `injector` 
* `PySide6`
* `langchain_google_genai`

**Depreciaciones Identificadas:**
* Pydantic V1 `@validator` → debe migrar a `@field_validator`
* `datetime.utcnow()` → debe usar `datetime.now(datetime.UTC)`

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**

**El proyecto tiene un problema de configuración de PYTHONPATH y entorno de desarrollo**:
1. **PYTHONPATH Incorrecto**: Los tests no pueden importar `src` porque no está en el path
2. **Entorno Incompleto**: Dependencias críticas no están instaladas en el entorno actual  
3. **FastAPI Error Enmascarado**: El error original de `gemini.py` no es visible hasta resolver imports

**Esto explica por qué:**
- `AUDIT_TASK.md` reportaba "un error restante" cuando hay 28+ errores de imports
- La validación de tests es imposible hasta resolver PYTHONPATH
- El proyecto parece completo pero no es ejecutable

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**

### OPERACIÓN: "ESTABILIZACIÓN DE ENTORNO DE DESARROLLO"

| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| **FASE 3A: CORRECCIÓN DE PYTHONPATH** |
| `pytest.ini` | Agregar configuración `pythonpath = .` para incluir el directorio raíz en PYTHONPATH | Permite que pytest encuentre el módulo `src` y todos los imports funcionen |
| **FASE 3B: INSTALACIÓN DE DEPENDENCIAS** |
| Entorno Python | Ejecutar `poetry install` para instalar todas las dependencias especificadas en `pyproject.toml` | Resuelve todos los `ModuleNotFoundError` para librerías de terceros |
| **FASE 3C: VALIDACIÓN DE IMPORTS** |
| N/A | Ejecutar `pytest --collect-only -q` para verificar que todos los tests se pueden importar sin errores | Confirma que el sistema de imports está completamente funcional |
| **FASE 3D: VERIFICACIÓN FASTAPI** |
| `src/ultibot_backend/api/v1/endpoints/gemini.py` | Verificar si el error FastAPI original persiste después de resolver imports | Identifica el problema real mencionado en `AUDIT_TASK.md` |

### ENFOQUE CRÍTICO:
1. **Resolver PYTHONPATH** como prerequisito absoluto
2. **Instalar dependencias** completas del proyecto
3. **Validar imports** antes de proceder con correcciones de código
4. **Identificar problemas reales** una vez que el entorno esté estable

**4. RIESGOS POTENCIALES:**
* **Poetry install falla**: Mitigado por revisar `pyproject.toml` y resolver conflictos de dependencias
* **PYTHONPATH no resuelve imports**: Mitigado usando rutas absolutas si es necesario
* **Problemas de entorno virtual**: Controlado verificando activación del entorno correcto

**5. SOLICITUD:**
* [**PAUSA**] Espero aprobación para proceder con la ejecución del plan de ESTABILIZACIÓN DE ENTORNO DE DESARROLLO.

---

### INFORME DE ESTADO Y PLAN DE ACCIÓN - 6/12/2025 14:02

**ESTADO ACTUAL:**
* FASE 1: ANÁLISIS SISTÉMICO COMPLETADO. Listo para formular hipótesis y plan de acción unificado.

**REFERENCIA A INFORMES PREVIOS:**
* Se preserva el historial completo de auditoría en este archivo. Se confirma que los problemas de arquitectura, dependencias y entorno ya han sido identificados y documentados en profundidad.

**1. OBSERVACIONES (Resultados de FASE 1):**
* **logs/frontend.log**: Solo muestra cierre limpio de MainWindow, sin errores ni advertencias.
* **logs/frontend1.log**: Cierre limpio, pero termina con "Unhandled Python exception" sin stacktrace. Indica excepción no capturada en el frontend, probablemente relacionada con dependencias PySide6 o integración UI.
* **logs/backend.log**: Solo muestra petición HTTP 200 exitosa al endpoint de notificaciones. No hay errores ni advertencias en backend FastAPI.
* **logs/pyqt_test.log**: Vacío o sin información relevante. No se registran errores de pruebas PyQt6, o las pruebas no se ejecutaron por problemas de entorno.
* **No se detectan errores críticos de ejecución en backend ni frontend fuera de los ya identificados en los informes previos.**
* **Persisten síntomas de entorno incompleto y dependencias faltantes, especialmente PySide6, injector, psycopg, asgi_correlation_id, langchain_google_genai.**
* **No hay evidencia de fallos de integración entre servicios en los logs, pero la excepción no capturada en frontend refuerza la hipótesis de entorno roto.**

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**
* El sistema está funcional a nivel de arquitectura y backend, pero la excepción no capturada en el frontend y la ausencia de logs de error detallados sugieren que el entorno de desarrollo sigue incompleto, especialmente en lo referente a dependencias de UI (PySide6) y posibles problemas de integración de pruebas.
* La causa raíz sigue siendo la instalación incompleta/corrupta de dependencias y posibles inconsistencias en el entorno virtual, lo que impide la ejecución estable y la validación completa del sistema.

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**

| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| N/A | Ejecutar `poetry install` para reinstalar todas las dependencias y reconstruir el entorno virtual | Garantiza que todas las librerías requeridas (incluyendo PySide6, injector, psycopg, asgi_correlation_id, langchain_google_genai) estén presentes y funcionales |
| N/A | Ejecutar `pytest --collect-only -q` para validar que todos los tests pueden importarse sin errores | Permite identificar si persisten problemas de imports o dependencias tras la reinstalación |
| N/A | Ejecutar pruebas de frontend/manuales para detectar y capturar el stacktrace de la excepción no manejada en frontend1.log | Permite aislar y corregir el fallo de integración UI que actualmente no tiene diagnóstico detallado |
| N/A | Documentar cualquier error nuevo o persistente en AUDIT_REPORT.md y, si corresponde, iniciar protocolo de post-mortem en AUDIT_MORTEN.md | Mantiene trazabilidad y contexto de auditoría |

**4. RIESGOS POTENCIALES:**
* Si `poetry install` falla, puede deberse a conflictos en `pyproject.toml` o problemas de red/repositorios.
* Si persisten los errores de importación o dependencias, podría ser necesario recrear el entorno virtual desde cero.
* La excepción no capturada en frontend podría requerir instrumentación adicional para obtener stacktrace.

**5. SOLICITUD:**
* [**PAUSA**] Espero aprobación para proceder con la ejecución del plan de REINSTALACIÓN DE DEPENDENCIAS Y VALIDACIÓN DE ENTORNO.

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