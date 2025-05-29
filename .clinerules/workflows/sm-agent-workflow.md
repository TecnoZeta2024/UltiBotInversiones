# Workflow: SM Agent Task Creation

Este workflow guía a Cline para asumir el rol de Technical Scrum Master (IDE), iniciar la creación de una nueva historia y luego restaurar el prompt del Orchestrator.

## Pasos

1.  **Configurar Custom Instructions para SM Agent:**
    Utiliza las instrucciones personalizadas del SM Agent para asegurar que Cline opere bajo ese rol.
    `/custom-instructions bmad-agent/personas/sm.ide.md`

2.  **Indicar a Cline que cree la siguiente historia:**
    Notifica a Cline que debe proceder a ejecutar la tarea de creación de la siguiente historia.
    `/say Por favor, procede a ejecutar la tarea de creación de la siguiente historia usando bmad-agent/tasks/create-next-story-task.md.`
    