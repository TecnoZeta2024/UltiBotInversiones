# Workflow: Dev Agent Task Execution

Este workflow guía a Cline para asumir el rol de Dev Agent, procesar una historia pendiente y luego restaurar el prompt del Orchestrator.

## Pasos

1.  **Configurar Custom Instructions para Dev Agent:**
    Utiliza las instrucciones personalizadas del Dev Agent para asegurar que Cline opere bajo ese rol.
    `/custom-instructions bmad-agent/personas/dev.ide.md`

2.  **Indicar a Cline que siga la historia pendiente:**
    Notifica a Cline que debe continuar con la historia pendiente en el directorio `docs/stories`.
    `/say Por favor, sigue el archivo de historia pendiente en docs/stories.`

3.  **Restaurar Custom Instructions del Orchestrator:**
    Una vez que las tareas del Dev Agent hayan terminado, restaura las instrucciones personalizadas al prompt del Orchestrator.
    `/custom-instructions bmad-agent/ide-bmad-orchestrator.md`
