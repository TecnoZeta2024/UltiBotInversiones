### INFORME DE ESTADO Y PLAN DE ACCIÓN SRST - 2025-06-16 22:37:10

**ESTADO ACTUAL:**
*   [**DEFCON 1**] La suite de tests está rota a nivel de recolección. Se han resuelto con éxito el ticket `SRST-029`, pero esto ha revelado 10 errores de importación subyacentes que ahora son la máxima prioridad.

**1. ANÁLISIS DE TRIAGE (Resultados de FASE 2 - Validación):**
*   **Comando ejecutado:** `poetry run pytest -k "tests/integration/test_story_4_5_trading_mode_integration.py" -v`
*   **Resumen de Errores:**
    *   **Total:** 10 errores de recolección.
    *   **Tipos:** `ImportError`, `ModuleNotFoundError`.
*   **Errores Principales Identificados:** `cannot import name '...'`, `No module named 'PyQt5.QtWidgets'`

**2. HIPÓTESIS CENTRAL (Causa Raíz General):**
*   **Causa raíz identificada:** La corrección del mock de `PyQt5` ha destapado una serie de problemas de dependencias en la arquitectura. Los `ImportError` sugieren fuertemente la existencia de **dependencias circulares** entre servicios (`config_service`, `trading_engine_service`) y/o una configuración de `sys.path` que no es consistente a lo largo de toda la suite de tests. El `ModuleNotFoundError` en los tests de UI confirma que la estrategia de mocking para `PyQt5` necesita ser aplicada de forma global y consistente, no solo en un archivo.
*   **Impacto sistémico:** La incapacidad de recolectar los tests paraliza por completo el proceso de CI/CD y la validación de cualquier cambio. Es la máxima prioridad a resolver.

**3. PLAN DE ACCIÓN (SESIÓN ACTUAL - DEFCON 1):**
| Ticket ID | Archivo a Modificar | Descripción del Cambio | Justificación (Por qué soluciona el ticket) |
| :--- | :--- | :--- | :--- |
| `SRST-031` | `tests/ui/unit/test_main_ui.py` | El error `ModuleNotFoundError: No module named 'PyQt5.QtWidgets'` es el más explícito. Se aplicará la misma estrategia de mocking de `PyQt5` que funcionó para el ticket `SRST-029` en este archivo para verificar si es una solución localizable o si necesita ser centralizada en `conftest.py`. | Atacar el error más claro primero nos permitirá entender si el problema de los mocks de UI es local o global. |
| `SRST-027` | `tests/integration/api/v1/test_config_endpoints.py` | El `ImportError: cannot import name 'ConfigService'` apunta a una dependencia circular. Se analizará el archivo `src/ultibot_backend/services/config_service.py` y sus importaciones para identificar y romper el ciclo. | `ConfigService` parece ser una dependencia central. Resolver su importación podría arreglar varios de los otros errores en cascada. |
| `SRST-028` | `tests/integration/api/v1/test_real_trading_flow.py` | Similar al anterior, el `ImportError` de `TradingEngineService` sugiere otra dependencia circular. Se investigará `src/ultibot_backend/services/trading_engine_service.py`. | `TradingEngineService` es el corazón del backend. Su correcta importación es crítica para la estabilidad de la mayoría de los tests de integración. |

**4. RIESGOS POTENCIALES:**
*   **Riesgo 1:** Romper una dependencia circular podría requerir un refactoring menor que afecte la inicialización de las clases. Se mitigará validando la recolección de tests después de cada cambio mínimo.
*   **Protocolo de rollback:** `git reset --hard HEAD` si una corrección empeora el estado de la recolección de tests.

**5. VALIDACIÓN PROGRAMADA:**
*   **Comando por ticket:** `poetry run pytest --collect-only -q`
*   **Métrica de éxito de la sesión:** Reducir el número de errores de recolección de 10 a 0.

**6. SOLICITUD:**
*   [**PAUSA**] Espero aprobación para proceder con la resolución del ticket `SRST-031`.
