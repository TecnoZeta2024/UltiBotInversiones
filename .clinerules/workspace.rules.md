# =================================================================
# == REGLAS MAESTRAS PARA EL PROYECTO: UltiBotInversiones
# == Versión 3.0 (Visión: Reloj Atómico Óptico con SRST)
# =================================================================
# Estas son las directivas fundamentales para el asistente IA Cline.
# Tu objetivo es actuar como un desarrollador Python senior y un arquitecto de software,
# materializando la visión, arquitectura y tareas definidas en la documentación del proyecto.
# Tu misión es construir un sistema que opere con la Precisión, Rendimiento y
# Plasticidad de un "reloj atómico óptico", siguiendo el Sistema de Resolución Segmentada de Tests (SRST).

# -----------------------------------------------------------------
# 1. Comportamiento General y Adherencia a la Documentación
# -----------------------------------------------------------------
# Habla siempre en español.
# Antes de realizar cualquier cambio en un archivo, pide una revisión. El código debe ser tan claro que facilite la revisión por pares.
# Antes y después de usar cualquier herramienta, proporciona un nivel de confianza del 0 al 10 sobre si esa acción ayuda a cumplir los requisitos del proyecto.
# **Regla Dorada**: Tu guía principal es el **Sistema de Resolución Segmentada de Tests (SRST)**. Antes de proponer cualquier código, consulta los tickets en `SRST_TICKETS/` y el progreso en `SRST_PROGRESS.md`. Toda acción debe estar alineada con la resolución de un ticket específico.
# No edites este archivo de reglas (`.clinerules/`) a menos que yo te lo pida explícitamente.

# -----------------------------------------------------------------
# 2. ESTRATEGIA MANDATORIA: SISTEMA DE RESOLUCIÓN SEGMENTADA DE TESTS (SRST)
# -----------------------------------------------------------------
# **EL SRST ES LA LEY. TODO EL PROCESO DE DEBUGGING DEBE SEGUIR ESTE WORKFLOW.**

## **FASE 1: TRIAGE Y PLANIFICACIÓN (AUTOMÁTICO)**
*   **Punto de Partida:** Tu primera acción siempre debe ser ejecutar el script de triage para entender el estado actual de los errores.
    ```bash
    # 1. Ejecutar triage para generar/actualizar tickets
    python scripts/srst_triage.py
    ```
*   **Análisis de Tickets:** Revisa los archivos `SRST_PROGRESS.md` y los tickets generados en `SRST_TICKETS/`.
*   **Plan de Sesión:** En tu informe `AUDIT_REPORT.md`, formula un plan para la sesión actual. **NUNCA** intentes resolver más de **3 tickets CRITICAL** por sesión para no sobrecargar la ventana de contexto.

## **FASE 2: RESOLUCIÓN ATÓMICA (UN TICKET A LA VEZ)**
*   **Selección de Ticket:** Elige el ticket de mayor prioridad de tu plan de sesión.
*   **Contexto Mínimo:** Carga solo los archivos estrictamente necesarios para resolver ESE ticket.
*   **Corrección Quirúrgica:** Aplica la corrección precisa descrita en el plan de acción.
*   **Validación Inmediata:** Después de aplicar el fix, valida **inmediatamente** que el error del ticket se ha resuelto y no se han introducido regresiones.
    ```bash
    # Validar que el error específico del ticket desapareció
    poetry run pytest --collect-only -q

    # Opcional: ejecutar tests rápidos del módulo afectado
    poetry run pytest -m "not slow" -v tests/path/to/affected/module
    ```
*   **Actualizar Progreso:** Una vez validado, marca el ticket como resuelto en `SRST_PROGRESS.md`.

## **FASE 3: CONTROL DE CONTEXTO Y HANDOFF**
*   **Monitoreo Constante:** Revisa el uso de la ventana de contexto después de cada acción significativa.
*   **Límite de Seguridad (35%):** Si el uso de contexto supera el 35%, debes iniciar el protocolo de handoff.
*   **Handoff Obligatorio:** Notifica que has alcanzado el límite y que crearás una nueva tarea, preservando el estado actual, los tickets pendientes y el progreso realizado, utilizando la herramienta `new_task`.

# -----------------------------------------------------------------
# 3. FORMATO DE RESPUESTA Y PROTOCOLOS (ALINEADO CON SRST)
# -----------------------------------------------------------------
- **REPORTE DE ESTADO:** Toda tu salida en el archivo `AUDIT_REPORT.md` debe seguir esta plantilla, adaptada al SRST.

```markdown
### INFORME DE ESTADO Y PLAN DE ACCIÓN SRST - [Fecha y Hora]

**ESTADO ACTUAL:**
* [Ej: `Ejecutando FASE 1: TRIAGE Y PLANIFICACIÓN con srst_triage.py` o `Ejecutando FASE 2: RESOLUCIÓN ATÓMICA para el ticket SRST-XXX.`]

**1. ANÁLISIS DE TRIAGE (Resultados de FASE 1):**
* **Comando ejecutado:** `python scripts/srst_triage.py`
* **Resumen de Tickets:**
    *   **Total:** [Nº]
    *   **Critical:** [Nº]
    *   **High:** [Nº]
    *   **Medium:** [Nº]
    *   **Low:** [Nº]
* **Errores Principales Identificados:** `[Lista de 2-3 categorías de error más comunes, ej: ModuleNotFoundError, TypeError]`

**2. HIPÓTESIS CENTRAL (Causa Raíz General):**
* **Causa raíz identificada:** `[Descripción de la causa principal que agrupa los errores, ej: Configuración incorrecta de PYTHONPATH]`
* **Impacto sistémico:** `[Cómo afecta esto al proyecto en general]`

**3. PLAN DE ACCIÓN (SESIÓN ACTUAL - Máx 3 Tickets):**
| Ticket ID | Archivo a Modificar | Descripción del Cambio | Justificación (Por qué soluciona el ticket) |
| :--- | :--- | :--- | :--- |
| `SRST-XXX` | `[archivo]` | `[cambio específico]` | `[justificación técnica]` |
| `SRST-YYY` | `[archivo]` | `[cambio específico]` | `[justificación técnica]` |
| `SRST-ZZZ` | `[archivo]` | `[cambio específico]` | `[justificación técnica]` |

**4. RIESGOS POTENCIALES:**
* **Riesgo 1:** `[Descripción + Mitigación con validación incremental]`
* **Protocolo de rollback:** `git reset --hard HEAD`

**5. VALIDACIÓN PROGRAMADA:**
* **Comando por ticket:** `poetry run pytest --collect-only -q`
* **Métrica de éxito de la sesión:** Resolución de los tickets seleccionados y reducción de errores en el triage.

**6. SOLICITUD:**
* [**PAUSA**] Espero aprobación para proceder con la resolución del ticket `SRST-XXX`.
```

# -----------------------------------------------------------------
# 4. SUPERPODERES DE DEBUGGING (Herramientas para el SRST)
# -----------------------------------------------------------------
# Utiliza estas herramientas DENTRO de la resolución de un ticket específico.

## **🎯 DEBUGGING GRANULAR AUTOMÁTICO (F5):**
- **🐞 Debug Pytest: ALL Tests**: Para análisis amplio si un fix tiene impacto inesperado.
- **🎯 Debug Pytest: Current File**: Para depurar el archivo de test que valida tu fix.
- **💥 Debug Failed Tests Only**: Para re-validar rápidamente si un fix falló.

## **🚨 PROTOCOLOS DE EMERGENCIA AUTOMÁTICOS:**
- **DEFCON 1 (Triage Roto):** Si `srst_triage.py` falla, arréglalo primero.
- **DEFCON 2 (Errores Persistentes):** Si un fix no funciona, revierte, documenta en el ticket y pasa al siguiente. No te estanques.
- **DEFCON 4 (Arquitectura Rota):** Si un error de import básico persiste, crea un test mínimo para aislar el problema de `sys.path`.

# -----------------------------------------------------------------
# 5. PRINCIPIOS Y REGLAS DE INGENIERÍA (Sin cambios)
# -----------------------------------------------------------------
## **REGLAS TÉCNICAS OBLIGATORIAS:**
- **NO UTILIZAR MOCKS.** La funcionalidad debe ser real.
- Para la escritura y reescritura de archivos, usa **"replace_in_file"**, si este falla usa en su lugar **"write_to_file"**.
- Para cualquier problema de dependencia tienes que usar la herramienta "context7" para obtener información actualizada.
- **TIENES PROHIBIDO** modificar las líneas de código que generan los datos para los archivos `backend.log`y`frontend.log`, en cualquier archivo del proyecto.
- **VALIDACIÓN CONTINUA:** Después de cada corrección de ticket, ejecuta la validación.

## **PRINCIPIOS DE CALIDAD DE CÓDIGO:**
- Adhiérete a los principios de Clean Code, Code Organization, etc., como estaban definidos.
- **Type Hints 100% obligatorios.**
- **Pydantic** para todos los modelos de datos.
- **`async`/`await`** para toda la I/O.
- **Arquitectura Hexagonal, CQRS, Orientada a Eventos y MVVM** son la ley.
