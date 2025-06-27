# Roadmap de Evolución 2.0: UltiBotInversiones - Planificación de Tareas

Este documento detalla la planificación estratégica, holística, secuencial y algorítmica de las tareas para la evolución de UltiBotInversiones, desglosadas en 3 niveles con sus respectivos checkpoints para un seguimiento efectivo.

## Visión General

Transformar UltiBotInversiones en un sistema de trading de alto rendimiento con una experiencia de usuario web moderna, visualmente impactante y altamente funcional, eliminando las complejidades del despliegue de escritorio actual y solidificando la confianza a través de una robusta estrategia de pruebas.

---

## Fase 0: Fundación del Backend (Pre requisitos Innegociables)

*   **Objetivo:** Eliminar la deuda técnica crítica del backend para construir sobre una base estable y confiable. Estas tareas son heredadas de la auditoría original y son esenciales antes de cualquier desarrollo de UI.
*   **Duración Estimada:** 1-2 semanas.

### Tareas:

*   **[ ] 1. Implementar Pruebas Unitarias de Modelos de Dominio (`src/ultibot_backend/core/domain_models`)**
    *   [ ] 1.1. Crear archivos de prueba para cada modelo Pydantic y ORM.
    *   [ ] 1.2. Validar la creación, serialización/deserialización y lógica de negocio de cada modelo.
    *   [ ] 1.3. **Checkpoint:** Cobertura de pruebas > 90% para este directorio.

*   **[ ] 2. Implementar Pruebas Unitarias de Estrategias de Trading (`src/ultibot_backend/strategies`)**
    *   [ ] 2.1. Desarrollar pruebas unitarias para cada estrategia, simulando diversos escenarios de mercado.
    *   [ ] 2.2. Validar la lógica de entrada, salida, y gestión de riesgo de forma aislada.
    *   [ ] 2.3. **Checkpoint:** Cobertura de pruebas > 90% para los archivos de estrategias.

*   **[ ] 3. Expandir Pruebas de Integración de API**
    *   [ ] 3.1. Ampliar la cobertura de `tests/integration/api/v1/endpoints` para todos los endpoints.
    *   [ ] 3.2. Priorizar endpoints de `trading`, `market_data`, `opportunities`, y `portfolio`.
    *   [ ] 3.3. **Checkpoint:** Todos los endpoints principales de la API tienen al menos una prueba de integración que valida su funcionalidad básica (happy path y error handling).

---

## Fase 1: Transición a una UI Web (Decisión Arquitectónica)

*   **Objetivo:** Seleccionar la tecnología para la nueva interfaz de usuario, diseñar su arquitectura y crear un prototipo funcional que valide la comunicación con el backend.
*   **Duración Estimada:** 1 semana.

### Tareas:

*   **[X] 1. Selección de Framework Frontend**
    *   [X] 1.1. Análisis comparativo realizado, considerando el flujo de usuario de trading de alta complejidad.
    *   [X] 1.2. **Decisión:** React.
        *   **Justificación:** React ofrece un ecosistema inigualable para aplicaciones financieras, destacando la disponibilidad de wrappers para librerías de gráficos estándar de la industria como TradingView y Highcharts. Su robustez en la gestión de estados complejos (con herramientas como Zustand o Redux) es crucial para manejar la lógica de las 10 estrategias de trading, los datos de mercado en tiempo real y las interacciones con el LLM. Además, el ecosistema de componentes de Magic UI permitirá un desarrollo rápido de una interfaz visualmente atractiva y funcional, con elementos como `bento-grid`, `terminal` y `animated-circular-progress-bar` que se alinean perfectamente con las necesidades del dashboard de trading.

*   **[ ] 2. Diseño de Arquitectura Frontend**
    *   [ ] 2.1. **Estructura de Directorios:** El proyecto en `src/ultibot_frontend/` (creado con Vite) seguirá una arquitectura modular y escalable:
        *   `components/`: Contendrá componentes de UI atómicos (botones, inputs) y complejos (`OrderMonitor`, `StrategyCard`).
        *   `views/`: Albergará las vistas principales que componen la aplicación (`DashboardView`, `StrategiesView`, `OpportunityDetailView`).
        *   `store/`: Gestionará el estado global con Zustand. Se definirán "slices" para responsabilidades claras: `marketDataSlice`, `ordersSlice`, `opportunitiesSlice`, `userInterfaceSlice`.
        *   `lib/`: Centralizará la lógica de servicios, incluyendo un `apiClient.js` (wrapper de Axios para la comunicación con el backend) y `charting.js` (configuraciones y wrappers para TradingView y Highcharts).
        *   `hooks/`: Definirá hooks de React personalizados para encapsular lógica de negocio compleja (ej. `useOrderExecution`, `useLlmAnalysisSubscription`).
    *   [ ] 2.2. **Flujo de Datos en Tiempo Real:** La arquitectura se centrará en la reactividad. La UI establecerá una conexión persistente (idealmente WebSockets, con fallback a sondeo de alta frecuencia) con el backend para recibir actualizaciones en tiempo real de:
        *   Datos de mercado de Binance.
        *   Nuevas oportunidades generadas por el LLM.
        *   Cambios de estado en las órdenes activas (creación, OCO, Trailing Stop, cierre).
    *   [ ] 2.3. **Gestión de Estado con Zustand:** El estado recibido a través de la conexión en tiempo real actualizará los slices correspondientes en Zustand. Los componentes de React se suscribirán a estos slices, asegurando que la UI se re-renderice de manera eficiente y automática solo cuando los datos relevantes cambien.

*   **[ ] 3. Prueba de Concepto (PoC) - Validación de Pilares Tecnológicos**
    *   [ ] 3.1. **Bootstrap:** Crear una aplicación React básica en `src/ultibot_frontend/` usando Vite.
    *   [ ] 3.2. **Layout y Conectividad:**
        *   Implementar una vista principal utilizando el componente `bento-grid` de Magic UI como layout principal.
        *   **Panel 1 (Conexión Backend):** En un panel del grid, usar Axios para conectar con el endpoint `/health` del backend y mostrar el estado ("Online" / "Offline").
    *   [ ] 3.3. **Visualización de Datos:**
        *   **Panel 2 (Gráficos Avanzados):** En otro panel, integrar un gráfico de Highcharts (`highcharts-react`) con datos estáticos para validar la correcta renderización y configuración de la librería.
    *   [ ] 3.4. **Componentes de UI Especializados:**
        *   **Panel 3 (Simulación de Logs):** Integrar el componente `terminal` de Magic UI para mostrar un flujo simulado de logs de actividad del bot, validando su estética y funcionalidad.
        *   **Panel 4 (Visualización de Confianza):** Usar el componente `animated-circular-progress-bar` de Magic UI para mostrar un valor de confianza de oportunidad (ej. 95%) de forma visualmente atractiva.
    *   [ ] 3.5. **Checkpoint:** El PoC se considera exitoso cuando la aplicación se renderiza sin errores y demuestra:
        *   Comunicación exitosa con la API del backend.
        *   Integración y renderización correcta de componentes de Magic UI (`bento-grid`, `terminal`, `animated-circular-progress-bar`).
        *   Renderización funcional de una librería de gráficos avanzada (`highcharts-react`).
        *   Esto valida los pilares tecnológicos fundamentales antes de proceder con la implementación a gran escala.

---

## Fase 2: Implementación y Migración de Vistas

*   **Objetivo:** Reconstruir sistemáticamente todas las funcionalidades de la antigua UI de PySide6 en la nueva plataforma web, mejorando el diseño y la experiencia de usuario en el proceso.
*   **Duración Estimada:** 2-4 semanas.

### Tareas:

*   **[ ] 1. Diseño de Componentes Reutilizables (Sistema de Diseño Atómico)**
    *   [ ] 1.1. **Componentes Base (Atómicos):** Crear un catálogo de componentes de UI fundamentales en `src/ultibot_frontend/components/base/`. Incluirá: `Button` (con variantes), `Input`, `Modal`, `Spinner`, `Tooltip`, `Card`.
    *   [ ] 1.2. **Componentes Complejos (Organismos):** Desarrollar componentes de negocio reutilizables en `src/ultibot_frontend/components/shared/`. Incluirá:
        *   `ChartWrapper`: Encapsulará `TradingView` y `Highcharts` para una fácil integración.
        *   `DataTable`: Tabla de datos avanzada con ordenamiento, filtrado y paginación (usando `TanStack Table`).
        *   `OpportunityCard`: Tarjeta para mostrar resúmenes de oportunidades de trading.
        *   `OrderForm`: Formulario dedicado para la creación y modificación de órdenes.
        *   `NotificationHandler`: Componente para gestionar y mostrar las notificaciones de Telegram.

*   **[ ] 2. Migración de Vistas (Ensamblaje de Componentes)**
    *   [ ] 2.1. **Dashboard Principal (`views/DashboardView.js`):**
        *   Layout principal con `bento-grid`.
        *   Integrará `ChartWrapper` para el gráfico principal, `DataTable` para órdenes activas, una lista de `OpportunityCard` y el `terminal` para logs.
    *   [ ] 2.2. **Vista de Gestión de Estrategias (`views/StrategiesView.js`):**
        *   Utilizará un componente `FileTree` para navegar entre las 10 estrategias.
        *   Integrará un editor de código (ej. `Monaco Editor`) para visualizar y modificar la configuración de cada estrategia.
    *   [ ] 2.3. **Vista de Análisis de Oportunidades (`views/OpportunityDetailView.js`):**
        *   Vista detallada que se carga al seleccionar una `OpportunityCard`.
        *   Mostrará un `ChartWrapper` específico del activo, datos de análisis del LLM y los botones de acción (Aprobar/Rechazar) del `NotificationHandler`.
    *   [ ] 2.4. **Vista de Portfolio y Rendimiento (`views/PortfolioView.js`):**
        *   Usará `DataTable` para el historial de operaciones y `ChartWrapper` con `Highcharts` para los gráficos de rendimiento.
    *   [ ] 2.5. **Diálogos de Configuración:**
        *   Se implementarán como `Modal`s reutilizables para la gestión de credenciales de API y otras configuraciones.

*   **[ ] 3. Implementación de Pruebas Unitarias para la UI (Garantía de Calidad)**
    *   [ ] 3.1. **Stack de Pruebas:** Se utilizará Vitest como corredor de pruebas y React Testing Library para la renderización y simulación de interacciones. El mocking de la API se realizará con Mock Service Worker (MSW) para aislar la UI del backend.
    *   [ ] 3.2. **Estrategia de Pruebas:** Se priorizará la prueba de la lógica de negocio sobre la cobertura de código pura. El foco estará en:
        *   **Hooks Personalizados:** Probar toda la lógica en `src/ultibot_frontend/hooks/`.
        *   **Componentes con Estado:** Probar componentes con lógica interna compleja como `OrderForm`.
        *   **Flujos de Usuario:** Simular interacciones completas como "el usuario ve una oportunidad, la aprueba y la orden aparece en la tabla de órdenes activas".
    *   [ ] 3.3. **Checkpoint:** Los flujos de usuario más críticos están cubiertos por pruebas unitarias y de integración, asegurando que las refactorizaciones futuras no rompan la funcionalidad clave.

---

## Fase 3: Pruebas de Sistema y Nueva Estrategia de Despliegue

*   **Objetivo:** Validar el sistema completo (Backend + Frontend Web) de manera integral y definir una estrategia de despliegue simplificada y robusta.
*   **Duración Estimada:** 1-2 semanas.

### Tareas:

*   **[ ] 1. Establecer un Marco de Pruebas de Extremo a Extremo (E2E)**
    *   [ ] 1.1. **Selección de Framework:** Se implementará Playwright por su rendimiento superior y su robusto soporte para escenarios de aplicaciones web complejas.
    *   [ ] 1.2. **Escenario de Prueba Crítico (Golden Path):** Crear un test E2E que simule el flujo de usuario completo:
        *   Iniciar la aplicación y verificar que el dashboard carga datos de mercado.
        *   Navegar a la vista de estrategias y activar una.
        *   Esperar (con los `waits` apropiados de Playwright) a que aparezca una notificación de oportunidad en la UI.
        *   Hacer clic en "Aprobar" para la oportunidad.
        *   Navegar a la vista de portfolio y verificar que la nueva orden aparece con el estado 'activa'.
        *   Verificar que la orden se cierra correctamente tras un cambio de estado simulado.
    *   [ ] 1.3. **Checkpoint:** El flujo E2E se ejecuta de forma fiable y repetible con un solo comando, validando la integración completa del sistema.

*   **[ ] 2. Definir la Nueva Estrategia de Despliegue (Local-First)**
    *   [ ] 2.1. **Decisión de Arquitectura:** Se adoptará la **Opción A: FastAPI sirve los archivos estáticos de la UI**. Esto simplifica la arquitectura, reduce la sobrecarga y es ideal para una aplicación de escritorio autocontenida. El backend servirá la API en `/api/v1` y la UI de React en la ruta raíz (`/`).
    *   [ ] 2.2. **Orquestación Simplificada:** Crear un nuevo `docker-compose.yml` que contenga únicamente los servicios esenciales: `ultibot_backend` y `ultibot_db`.
    *   [ ] 2.3. **Eliminación de Complejidad:** El `Dockerfile.frontend` y toda la infraestructura relacionada con VNC/XFCE/Supervisord **serán eliminados por completo**.

*   **[ ] 3. Documentación y Monitorización**
    *   [ ] 3.1. **`README.md` Renovado:** Re-escribir el `README.md` del proyecto para que sea la única fuente de verdad para el arranque. Debe incluir:
        *   Prerrequisitos (Docker, Docker Compose).
        *   Instrucciones para configurar el archivo `.env`.
        *   El comando único para iniciar todo el sistema: `docker-compose up --build`.
        *   La URL de acceso a la aplicación: `http://localhost:8000`.
    *   [ ] 3.2. **Monitorización Básica:** La UI incluirá un indicador de estado de conexión en tiempo real (WebSocket/API) para una monitorización visual simple.

*   **[ ] 4. Limpieza de Código Obsoleto (Tierra Quemada)**
    *   [ ] 4.1. Eliminar el directorio completo `src/ultibot_ui`.
    *   [ ] 4.2. Eliminar todos los archivos de prueba relacionados: `tests/ui/`, `tests/integration/test_story_4_5_trading_mode_integration.py`, etc.
    *   [ ] 4.3. Realizar una búsqueda global en el proyecto de términos como `PySide6`, `VNC`, `XFCE` y eliminar cualquier configuración, script o comentario remanente.
    *   [ ] 4.4. **Checkpoint:** El codebase está completamente libre de los artefactos de la antigua UI, reflejando puramente la nueva arquitectura.
