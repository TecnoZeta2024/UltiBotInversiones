# Plan de Acción Estratégico: Evolución 2.0 - Migración a UI Web

**Visión:** Transformar UltiBotInversiones en un sistema de trading de alto rendimiento con una experiencia de usuario web moderna, eliminando las complejidades del despliegue de escritorio y solidificando la confianza a través de una robusta estrategia de pruebas.

**Documento de Origen:** `memory/roadmap_evolucion_2.0.md`
**Protocolo Activo:** Lead Coder, Ciclo B-MAD-R

---

## Fase 0: Fundación del Backend (Pre-requisitos Innegociables)

*   **Objetivo:** Eliminar la deuda técnica crítica del backend para construir sobre una base estable y confiable.
*   **Estado:** `PENDIENTE`

### Tareas:

- [ ] **1. Implementar Pruebas Unitarias de Modelos de Dominio (`src/ultibot_backend/core/domain_models`)**
    - [ ] **1.1.** Crear archivos de prueba para cada modelo Pydantic y ORM.
    - [ ] **1.2.** Validar la creación, serialización/deserialización y lógica de negocio de cada modelo.
    - [ ] **1.3.** **Criterio de Éxito:** Cobertura de pruebas > 90% para este directorio.

- [ ] **2. Implementar Pruebas Unitarias de Estrategias de Trading (`src/ultibot_backend/strategies`)**
    - [ ] **2.1.** Desarrollar pruebas unitarias para cada estrategia, simulando diversos escenarios de mercado.
    - [ ] **2.2.** Validar la lógica de entrada, salida, y gestión de riesgo de forma aislada.
    - [ ] **2.3.** **Criterio de Éxito:** Cobertura de pruebas > 90% para los archivos de estrategias.

- [ ] **3. Expandir Pruebas de Integración de API**
    - [ ] **3.1.** Ampliar la cobertura de `tests/integration/api/v1/endpoints` para todos los endpoints.
    - [ ] **3.2.** Priorizar endpoints de `trading`, `market_data`, `opportunities`, y `portfolio`.
    - [ ] **3.3.** **Criterio de Éxito:** Todos los endpoints principales de la API tienen al menos una prueba de integración que valida su funcionalidad básica (happy path y error handling).

---

## Fase 1: Transición a una UI Web (Decisión Arquitectónica)

*   **Objetivo:** Seleccionar la tecnología para la nueva interfaz de usuario, diseñar su arquitectura y crear un prototipo funcional que valide la comunicación con el backend.
*   **Estado:** `EN PROGRESO`

### Tareas:

- [x] **1. Selección de Framework Frontend**
    - [x] **1.1.** Análisis comparativo realizado.
    - [x] **1.2.** **Decisión: React.**
        - **Justificación:** Ecosistema robusto (TradingView, Highcharts, Magic UI, Zustand) ideal para la complejidad de la aplicación.

- [ ] **2. Diseño de Arquitectura Frontend**
    - [ ] **2.1.** **Estructura de Directorios:** Definir y crear la estructura de directorios en `src/ultibot_frontend/` (components, views, store, lib, hooks).
    - [ ] **2.2.** **Flujo de Datos en Tiempo Real:** Diseñar el mecanismo de conexión (WebSockets con fallback a sondeo) para la recepción de datos del mercado, oportunidades y órdenes.
    - [ ] **2.3.** **Gestión de Estado con Zustand:** Definir los "slices" iniciales (`marketDataSlice`, `ordersSlice`, `opportunitiesSlice`, `userInterfaceSlice`) en `src/ultibot_frontend/store/`.

- [ ] **3. Prueba de Concepto (PoC) - Validación de Pilares Tecnológicos**
    - [ ] **3.1.** **Bootstrap:** Crear una aplicación React básica en `src/ultibot_frontend/` usando Vite.
    - [ ] **3.2.** **Layout y Conectividad:**
        - [ ] Implementar `bento-grid` de Magic UI como layout principal.
        - [ ] Conectar con el endpoint `/health` del backend y mostrar el estado.
    - [ ] **3.3.** **Visualización de Datos:**
        - [ ] Integrar un gráfico de `highcharts-react` con datos estáticos.
    - [ ] **3.4.** **Componentes de UI Especializados:**
        - [ ] Integrar el componente `terminal` de Magic UI para logs simulados.
        - [ ] Integrar `animated-circular-progress-bar` de Magic UI para un valor de confianza.
    - [ ] **3.5.** **Criterio de Éxito:** La aplicación PoC se renderiza sin errores, demostrando la integración exitosa de Backend, Magic UI y Highcharts.

---

## Fase 2: Implementación y Migración de Vistas

*   **Objetivo:** Reconstruir sistemáticamente todas las funcionalidades de la antigua UI de PySide6 en la nueva plataforma web.
*   **Estado:** `PENDIENTE`

### Tareas:

- [ ] **1. Diseño de Componentes Reutilizables (Sistema de Diseño Atómico)**
    - [ ] **1.1.** **Componentes Base (Atómicos):** Crear catálogo en `src/ultibot_frontend/components/base/` (Button, Input, Modal, etc.).
    - [ ] **1.2.** **Componentes Complejos (Organismos):** Desarrollar en `src/ultibot_frontend/components/shared/` (ChartWrapper, DataTable, OpportunityCard, etc.).

- [ ] **2. Migración de Vistas (Ensamblaje de Componentes)**
    - [ ] **2.1.** Implementar `views/DashboardView.js`.
    - [ ] **2.2.** Implementar `views/StrategiesView.js`.
    - [ ] **2.3.** Implementar `views/OpportunityDetailView.js`.
    - [ ] **2.4.** Implementar `views/PortfolioView.js`.
    - [ ] **2.5.** Implementar diálogos de configuración como `Modal`s.

- [ ] **3. Implementación de Pruebas Unitarias para la UI**
    - [ ] **3.1.** Configurar el stack de pruebas: Vitest, React Testing Library, MSW.
    - [ ] **3.2.** Desarrollar pruebas para hooks personalizados y componentes con estado.
    - [ ] **3.3.** **Criterio de Éxito:** Flujos de usuario críticos cubiertos por pruebas.

---

## Fase 3: Pruebas de Sistema y Nueva Estrategia de Despliegue

*   **Objetivo:** Validar el sistema completo (Backend + Frontend Web) y definir una estrategia de despliegue simplificada.
*   **Estado:** `PENDIENTE`

### Tareas:

- [ ] **1. Establecer un Marco de Pruebas de Extremo a Extremo (E2E)**
    - [ ] **1.1.** Implementar Playwright.
    - [ ] **1.2.** Crear el test E2E del "Golden Path" (inicio, activación de estrategia, aprobación de oportunidad, verificación de orden).
    - [ ] **1.3.** **Criterio de Éxito:** El test E2E se ejecuta de forma fiable con un solo comando.

- [ ] **2. Definir la Nueva Estrategia de Despliegue (Local-First)**
    - [ ] **2.1.** Configurar FastAPI para servir los archivos estáticos de React.
    - [ ] **2.2.** Crear un nuevo `docker-compose.yml` simplificado (`ultibot_backend`, `ultibot_db`).
    - [ ] **2.3.** Eliminar `Dockerfile.frontend` y la infraestructura VNC.

- [ ] **3. Documentación y Monitorización**
    - [ ] **3.1.** Re-escribir el `README.md` con las nuevas instrucciones de despliegue.
    - [ ] **3.2.** Incluir un indicador de estado de conexión en la UI.

- [ ] **4. Limpieza de Código Obsoleto (Tierra Quemada)**
    - [ ] **4.1.** Eliminar `src/ultibot_ui`.
    - [ ] **4.2.** Eliminar pruebas obsoletas (`tests/ui/`, etc.).
    - [ ] **4.3.** Buscar y eliminar restos de `PySide6`, `VNC`, `XFCE`.
    - [ ] **4.4.** **Criterio de Éxito:** El codebase está 100% libre de los artefactos de la UI antigua.
