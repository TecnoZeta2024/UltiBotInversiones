# Workflow: Handoff y Continuidad de Tareas

Este workflow proporciona los pasos jerárquicos y específicos para detener el trabajo actual y continuar la resolución de errores en una nueva ventana de contexto, asegurando el registro de avances y el uso de `sequential-thinking`.

## Pasos para el Handoff y Continuidad

1.  **Detener el Trabajo Actual y Preparar Handoff:**
    *   Asegúrate de que `SRST_PROGRESS.md` y `AUDIT_REPORT.md` estén actualizados con el estado más reciente de los tickets (completados, en progreso, pendientes).

2.  **Crear Nueva Tarea con Contexto Preservado:**
    *   Ejecuta el comando `/newtask` y rellena la plantilla de contexto de forma exhaustiva, incluyendo:
        *   **Trabajo Completado:** Lista detallada de ítems, archivos modificados/creados, decisiones importantes.
        *   **Estado Actual:** Descripción del proyecto, procesos en ejecución, estado de archivos clave.
        *   **Próximos Pasos:** Tareas restantes, detalles de implementación, desafíos conocidos.
        *   **Información de Referencia:** Documentación, snippets de código, preferencias del usuario.
        *   **Instrucción de Continuidad:** Una instrucción clara sobre cómo debe continuar la nueva sesión.

3.  **En la Nueva Ventana de Contexto (Primera Acción Obligatoria):**
    *   **SI** el contexto de la nueva tarea indica que hay tareas completadas de la sesión anterior, la **primera acción** debe ser registrar este avance en los archivos de seguimiento (`SRST_PROGRESS.md`, `AUDIT_REPORT.md`).
        *   Esto se logra leyendo el contenido actual de estos archivos y añadiendo la nueva entrada de progreso utilizando `replace_in_file` o `write_to_file`.

4.  **Análisis, Reflexión y Planificación con `sequential-thinking`:**
    *   Utiliza la herramienta `sequential-thinking` para analizar el problema, reflexionar sobre posibles soluciones y planificar los pasos detallados para la resolución de los errores pendientes.
    *   Ejemplo de uso:
        ```xml
        <use_mcp_tool>
        <server_name>sequential-thinking</server_name>
        <tool_name>sequentialthinking</tool_name>
        <arguments>
        {
          "thought": "Analizando el ticket SRST-XXX: [Descripción del error]. Mi hipótesis inicial es [Hipótesis]. Necesito [Acción de análisis].",
          "nextThoughtNeeded": true,
          "thoughtNumber": 1,
          "totalThoughts": 3
        }
        </arguments>
        </use_mcp_tool>
        ```

5.  **Solución de Errores (SRST - Fase 2):**
    *   Una vez que el plan esté claro, procede con la resolución atómica de los tickets, siguiendo estrictamente la `FASE 2: RESOLUCIÓN ATÓMICA` del SRST (selección de ticket, contexto mínimo, fix quirúrgico, validación inmediata).
