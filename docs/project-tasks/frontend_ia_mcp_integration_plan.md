# Plan de Integración Frontend para IA Colaborativa y MCP en Estrategias

Este documento detalla las tareas necesarias para que el frontend de UltiBotInversiones contemple la integración explícita de la IA colaborativa (Gemini) y los servidores MCP (Model Context Protocol) en la gestión y operación de estrategias de trading. Cada tarea principal se desglosa en subtareas minuciosas para facilitar la planificación, asignación y mejora continua.

---

## 1. Análisis y Diseño de la Integración

### 1.1. Revisión de la arquitectura actual
- Analizar cómo el backend orquesta la colaboración IA/MCP y cómo expone los resultados al frontend.
- Identificar endpoints REST existentes y carencias para interacción directa con MCP/IA desde la UI.
- Documentar el flujo actual de oportunidades, análisis IA y estrategias.

### 1.2. Definición de requerimientos de usuario
- Recopilar casos de uso donde el usuario quiera interactuar explícitamente con la IA/MCP (ej: lanzar análisis, ver logs, configurar MCPs).
- Definir qué información y controles deben estar disponibles en la UI.

### 1.3. Diseño de endpoints y contratos API
- Proponer nuevos endpoints REST (o WebSocket) para:
  - Lanzar análisis IA/MCP bajo demanda.
  - Consultar estado/resultados de análisis colaborativos.
  - Configurar MCPs y perfiles IA desde la UI.
- Definir los esquemas de datos y validaciones necesarias.

---

## 2. Extensión del Cliente API (`UltiBotAPIClient`)

### 2.1. Implementar métodos para nuevos endpoints
- `run_collaborative_ai_analysis(opportunity_id, strategy_id, ...)`
- `get_mcp_tools_status()`
- `get_ai_analysis_logs(opportunity_id)`
- `update_mcp_server_preferences(prefs)`

### 2.2. Pruebas unitarias de los nuevos métodos
- Mockear respuestas del backend.
- Validar manejo de errores y formatos de datos.

---

## 3. Actualización de Vistas y Componentes UI

### 3.1. Panel de Estrategias
- Añadir controles para:
  - Seleccionar si una estrategia usa IA/MCP colaborativa.
  - Configurar el perfil de IA y MCPs asociados.
  - Lanzar análisis colaborativo manualmente sobre una oportunidad.
- Mostrar el estado/resultados del último análisis IA/MCP.

#### 3.1.1. Subtareas
- Rediseñar el formulario de edición de estrategia para incluir opciones IA/MCP.
- Añadir botón "Lanzar análisis IA/MCP" en cada oportunidad.
- Mostrar logs/resultados detallados en un modal o panel lateral.

### 3.2. Panel de Oportunidades
- Visualizar si una oportunidad fue analizada por IA/MCP y el resultado.
- Permitir reanalizar una oportunidad bajo demanda.

#### 3.2.1. Subtareas
- Añadir iconos/etiquetas para oportunidades con análisis IA/MCP.
- Implementar historial de análisis por oportunidad.

### 3.3. Panel de Configuración
- Permitir al usuario gestionar la lista de MCPs y credenciales asociadas.
- Configurar preferencias de IA colaborativa (modelos, prompts, herramientas disponibles).

#### 3.3.1. Subtareas
- Formulario para alta/baja/edición de MCPs.
- Validación de credenciales MCP desde la UI.
- Selección de herramientas IA/MCP disponibles por perfil.

---

## 4. Mejoras de Experiencia de Usuario y Feedback

### 4.1. Indicadores de estado y progreso
- Mostrar spinners, barras de progreso o notificaciones durante análisis IA/MCP.
- Feedback claro en caso de error o éxito.

### 4.2. Logs y trazabilidad
- Permitir al usuario ver el historial de análisis IA/MCP por oportunidad y estrategia.
- Exportar logs o resultados para auditoría.

---

## 5. Pruebas de Integración y QA

### 5.1. Pruebas end-to-end
- Simular flujos completos: configuración, lanzamiento de análisis, visualización de resultados.
- Validar integración con backend real y mocks.

### 5.2. Pruebas de usabilidad
- Recoger feedback de usuarios sobre la nueva funcionalidad.
- Ajustar la UI/UX según resultados.

---

## 6. Documentación y Formación

### 6.1. Actualizar documentación técnica
- Documentar nuevos endpoints, métodos de cliente y flujos UI.

### 6.2. Manual de usuario
- Crear o actualizar guías para usuarios sobre la IA colaborativa y MCPs.

---

## 7. Futuras Mejoras y Extensiones

### 7.1. Soporte para nuevos MCPs
- Añadir adaptadores y UI para nuevos tipos de MCPs (on-chain, sentiment, etc.).

### 7.2. Integración con WebSocket para análisis en tiempo real
- Permitir feedback en vivo de análisis IA/MCP.

### 7.3. Personalización avanzada de prompts y perfiles IA
- Permitir a usuarios avanzados editar plantillas de prompts y lógica de análisis.

---

> **Nota:** Cada tarea y subtarea debe ser registrada en el sistema de gestión de proyectos y desglosada en issues/tickets para su seguimiento y priorización.
