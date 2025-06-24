# Objetivo: Crear un sistema unificado de IA para UltiBotInversiones

- [x] **Fase 1: Síntesis y Unificación de Reglas**
    - [x] Sintetizar todos los documentos (`.clinerules`, `Systemprompt`, `Software_Ingeniering.md`) en un conjunto coherente de reglas maestras.
    - [x] Crear un archivo `workspace.rules.md` consolidado en `.clinerules` que sirva como el punto de entrada principal para las reglas del proyecto.

- [x] **Fase 2: Diseño de la Arquitectura del Sistema de Agentes**
    - [x] Diseñar una arquitectura que integre el concepto `bmad-agent` con la estructura de proyecto existente.
    - [x] Definir cómo los agentes (`Analyst`, `PO`, `Architect`, etc.) interactuarán con el código base y los artefactos del proyecto.
    - [x] Crear un diagrama de arquitectura para el nuevo sistema de agentes.

- [x] **Fase 3: Implementación del Orquestador de Agentes**
    - [x] Implementar la lógica del orquestador de agentes basada en `bmad-agent/ide-bmad-orchestrator.md`.
    - [x] Implementar el mecanismo de carga de configuración desde `ide-bmad-orchestrator.cfg.md`.
    - [x] Implementar la activación de `Personas` y la ejecución de `Tasks`.

- [ ] **Fase 4: Implementación de Mecanismos de Memoria y Seguimiento**
    - [x] Implementar el sistema de seguimiento de tareas (`TASKLIST.md`) como se define en el `Systemprompt.v5.0.md`.
    - [ ] Implementar el protocolo de handoff de contexto para preservar la memoria entre sesiones.

- [ ] **Fase 5: Implementación del Mecanismo de Autorreflexión**
    - [ ] Implementar el proceso de autorreflexión para la mejora continua de las `.clinerules` basado en `self-improving-cline.md`.

- [ ] **Fase 6: Integración con la Interfaz de Windows**
    - [ ] Investigar y definir el método para que el sistema de IA interactúe y ejecute la interfaz de Windows.
    - [ ] Implementar un prototipo de la ejecución de la interfaz de Windows.
