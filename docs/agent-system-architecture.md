# Arquitectura del Sistema de Agentes de IA para UltiBotInversiones

## 1. Propósito

Este documento describe la arquitectura del sistema de agentes de IA, diseñado para operar dentro del proyecto `UltiBotInversiones`. El sistema, basado en el concepto `bmad-agent`, proporciona una capa de orquestación para automatizar tareas complejas de desarrollo, análisis y gestión de productos mediante el uso de agentes especializados (Personas).

## 2. Componentes Principales

El sistema se compone de los siguientes módulos lógicos:

- **Orquestador (Orchestrator):** Es el núcleo del sistema. Gestiona el estado principal (si está en modo orquestador o si hay una persona activa), procesa los comandos del usuario y dirige el flujo de activación de personas y ejecución de tareas. Su comportamiento está definido en `bmad-agent/ide-bmad-orchestrator.md`.

- **Cargador de Configuración (Config Loader):** Su única responsabilidad es leer, parsear y validar el archivo `bmad-agent/ide-bmad-orchestrator.cfg.md`. Proporciona al Orquestador la lista de personas, tareas y las rutas base para todos los recursos del agente.

- **Cargador de Personas (Persona Loader):** Cuando el Orquestador recibe una solicitud para activar una persona, este componente construye la ruta al archivo de la persona, lo carga en memoria y lo instancia como el "Agente Activo".

- **Ejecutor de Tareas (Task Executor):** Una vez que un agente está activo y recibe una tarea, este componente se encarga de:
    1.  Localizar el archivo de la tarea (si no es una tarea interna).
    2.  Resolver las rutas a recursos dependientes como plantillas (`templates`) o checklists (`checklists`).
    3.  Ejecutar las instrucciones definidas en la tarea.

- **Interfaz del Espacio de Trabajo (Workspace Interface):** Es la capa de abstracción que conecta al sistema de agentes con el entorno del proyecto. Proporciona las herramientas fundamentales que los agentes utilizan para interactuar con el proyecto, tales como:
    - `readFile(path)`
    - `writeFile(path)`
    - `replaceInFile(path, diff)`
    - `listFiles(path)`
    - `executeCommand(command)`

- **Sistema de Archivos del Proyecto (Project Filesystem):** Representa la estructura de directorios y archivos existente de `UltiBotInversiones`, con la que interactúa la `Workspace Interface`.

## 3. Diagrama de Arquitectura

El siguiente diagrama ilustra el flujo de interacción entre los componentes:

```mermaid
graph TD
    subgraph "Usuario"
        User[👤 Usuario]
    end

    subgraph "Sistema de Agentes de IA"
        Orchestrator[🚀 Orquestador]
        ConfigLoader[⚙️ Cargador de Configuración]
        PersonaLoader[🎭 Cargador de Personas]
        TaskExecutor[🛠️ Ejecutor de Tareas]
        WorkspaceInterface[🔌 Interfaz del Espacio de Trabajo]
    end

    subgraph "Recursos del Agente (bmad-agent/)"
        ConfigFile[📄 ide-bmad-orchestrator.cfg.md]
        PersonaFiles[🧑‍💻 Personas (e.g., po.md)]
        TaskFiles[📝 Tareas (e.g., create-prd.md)]
    end

    subgraph "Artefactos del Proyecto"
        ProjectFilesystem[📂 Sistema de Archivos (src/, docs/, etc.)]
    end

    User -- "1. Inicia y selecciona Agente/Tarea" --> Orchestrator
    Orchestrator -- "2. Carga configuración" --> ConfigLoader
    ConfigLoader -- "3. Lee" --> ConfigFile
    ConfigFile -- "4. Provee datos de configuración" --> Orchestrator

    Orchestrator -- "5. Activa Persona" --> PersonaLoader
    PersonaLoader -- "6. Carga definición" --> PersonaFiles
    PersonaLoader -- "7. Crea Instancia de Agente Activo" --> TaskExecutor

    TaskExecutor -- "8. Ejecuta Tarea" --> TaskFiles
    TaskExecutor -- "9. Usa herramientas" --> WorkspaceInterface
    WorkspaceInterface -- "10. Interactúa con archivos" --> ProjectFilesystem

```

## 4. Flujo de Operación

1.  El **Usuario** inicia una interacción.
2.  El **Orquestador** se inicializa, utilizando el **Cargador de Configuración** para leer el `ConfigFile`.
3.  El **Orquestador**, ya configurado, presenta las opciones al usuario o procesa una solicitud directa.
4.  A petición del usuario, el **Orquestador** utiliza el **Cargador de Personas** para instanciar un agente específico a partir de los `PersonaFiles`.
5.  El agente activo, a través del **Ejecutor de Tareas**, procesa una solicitud de tarea.
6.  El **Ejecutor de Tareas** lee la definición de la tarea desde los `TaskFiles` y utiliza la **Interfaz del Espacio de Trabajo** para realizar acciones concretas.
7.  La **Interfaz del Espacio de Trabajo** modifica o lee información del **Sistema de Archivos del Proyecto**, completando así la tarea.
