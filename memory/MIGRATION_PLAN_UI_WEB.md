# Plan Maestro de Migración: Evolución 2.0 a UI Web

**ID de Misión:** EVO-2.0-UI-WEB
**Agente Responsable:** Lead Coder
**Visión:** Transformar UltiBotInversiones en un sistema de trading de alto rendimiento con una experiencia de usuario web moderna, eliminando las complejidades del despliegue de escritorio y solidificando la confianza a través de una robusta estrategia de pruebas y desarrollo desacoplado.
**Documentos de Referencia Clave:** `roadmap_evolucion_2.0.md`, `auditoria_ultibot_inversiones_20250627.md`, `API_CONTRACT_MAP.md`.

---

## Principios Rectores de la Migración

1.  **Desarrollo Desacoplado (Mock-First):** La nueva UI se desarrollará y probará de forma aislada contra un servidor de API simulado (mock server) antes de cualquier integración con el backend real.
2.  **Inmutabilidad del Legado:** El código existente en `src/ultibot_ui/` no será modificado. Permanecerá intacto hasta la fase final de "Tierra Quemada".
3.  **Enfoque Iterativo y por Fases:** La migración se ejecutará en fases secuenciales. Cada fase tiene criterios de éxito claros y debe completarse antes de iniciar la siguiente.
4.  **Calidad por Diseño:** Las pruebas (unitarias, de componentes y E2E) son una parte integral del desarrollo, no una ocurrencia tardía.

---

## Fase 0: Fortificación del Backend (Pre-requisito Innegociable)

*   **Objetivo:** Asegurar que el backend sea una base estable y confiable antes de construir la nueva UI sobre él. Esta fase aborda la deuda técnica crítica identificada en la auditoría.
*   **Estado:** `COMPLETADO`

### Tareas:

- [x] **1. Implementar Pruebas Unitarias de Modelos de Dominio (`src/ultibot_backend/core/domain_models`)**
    - [x] 1.1. Crear archivos de prueba para cada modelo Pydantic y ORM.
    - [x] 1.2. Validar la creación, serialización/deserialización y lógica de negocio de cada modelo.
    - [x] **Criterio de Éxito:** Cobertura de pruebas > 90% para este directorio.

- [x] **2. Implementar Pruebas Unitarias de Estrategias de Trading (`src/ultibot_backend/strategies`)**
    - [x] 2.1. Desarrollar pruebas unitarias para cada estrategia, simulando diversos escenarios de mercado.
    - [x] 2.2. Validar la lógica de entrada, salida y gestión de riesgo de forma aislada.
    - [x] **Criterio de Éxito:** Cobertura de pruebas > 90% para los archivos de estrategias.

- [x] **3. Expandir Pruebas de Integración de API**
    - [x] 3.1. Ampliar la cobertura de `tests/integration/api/v1/endpoints` para todos los endpoints definidos en `API_CONTRACT_MAP.md`.
    - [x] 3.2. Priorizar endpoints de `trading`, `market_data`, `opportunities`, y `portfolio`.
    - [x] 3.3. **(Completado)** Crear y validar pruebas para los endpoints de `config` (`test_config_endpoints.py`).
    - [x] **Criterio de Éxito:** Todos los endpoints principales de la API tienen al menos una prueba de integración que valida su funcionalidad básica (happy path y error handling).

---

## Fase 1: Andamiaje Frontend y Desarrollo Guiado por Mocks

*   **Objetivo:** Crear un prototipo funcional y aislado de la nueva UI, validando las tecnologías seleccionadas y estableciendo un entorno de desarrollo robusto basado en un backend simulado.
*   **Estado:** `EN PROGRESO`

### Tareas:

- [x] **1. Configuración del Proyecto Frontend**
    - [x] 1.1. Crear una nueva aplicación **React** con **Vite** en `src/ultibot_frontend/`.
    - [x] 1.2. Definir y crear la estructura de directorios: `components/`, `views/`, `lib/`.
    - [x] 1.3. Instalar dependencias clave: `react`, `vite`, `axios`, `highcharts`, `highcharts-react`, `lucide-react` y componentes de `magicui`.

- [ ] **2. Implementación del Servidor de API Simulado (Mock Server) - `SALTADO`**
    - **Justificación de Desviación:** Se priorizó la velocidad de desarrollo, conectando directamente con el backend. Esto introduce un riesgo de acoplamiento que debe ser mitigado con pruebas de integración robustas en la Fase 3.

- [ ] **3. Desarrollo de Servicios y Estado Global - `SALTADO`**
    - **Justificación de Desviación:** No se implementó un store global con Zustand. La gestión de estado es local a los componentes o a través de React Context, lo que puede requerir refactorización si la complejidad aumenta.

- [x] **4. Prueba de Concepto (PoC) con Datos Reales/Estáticos**
    - [x] 4.1. Implementar un layout `bento-grid` (Magic UI) en la vista principal (`views/DashboardView.js`).
    - [x] 4.2. **Panel 1 (Estado de Conexión):** Creado (`HealthCheckPanel.tsx`).
    - [x] 4.3. **Panel 2 (Gráfico):** Creado (`HighchartsPanel.tsx`).
    - [x] 4.4. **Panel 3 (Terminal):** Creado (`TerminalPanel.tsx`).
    - [x] **Criterio de Éxito:** La PoC se renderiza sin errores, demostrando la correcta integración de las tecnologías seleccionadas.

---

## Fase 2: Implementación de Vistas con Paridad de Funciones

*   **Objetivo:** Reconstruir sistemáticamente todas las funcionalidades de la antigua UI de PySide6 en la nueva plataforma web.
*   **Estado:** `COMPLETADO`

### Tareas:

- [x] **1. Sistema de Diseño Atómico (Componentes Reutilizables)**
    - [x] 1.1. Crear componentes base en `components/base/` y `components/ui/`.
    - [x] 1.2. Crear componentes complejos en `components/shared/`.

- [x] **2. Migración de Vistas (una por una)**
    - [x] 2.1. Implementar `views/DashboardView.tsx`.
    - [x] 2.2. Implementar `views/StrategiesView.tsx`.
    - [x] 2.3. Implementar `views/OpportunityDetailView.tsx`.
    - [x] 2.4. Implementar `views/PortfolioView.tsx`.

- [ ] **3. Pruebas Unitarias y de Componentes**
    - [x] 3.1. Configurar **Vitest** y **React Testing Library**.
    - [ ] 3.2. **(Pendiente)** Escribir pruebas para todos los hooks personalizados y componentes con lógica de negocio.
    - [ ] 3.3. **(Pendiente)** La ausencia de MSW requiere que las pruebas de componentes se hagan con datos estáticos o mocks manuales de las llamadas de API.
    - [ ] **Criterio de Éxito:** Los flujos de usuario críticos (ej. crear una orden, aprobar una oportunidad) están cubiertos por pruebas.
>>>>>>>

---

## Fase 3: Integración con el Backend Real

*   **Objetivo:** Desconectar el backend simulado y conectar la nueva UI completamente funcional al backend real, depurando las discrepancias.
*   **Estado:** `PENDIENTE`

### Tareas:

- [ ] **1. El "Interruptor" (The Switch)**
    - [ ] 1.1. Configurar una variable de entorno (`VITE_API_MOCKING`) para habilitar o deshabilitar MSW.
    - [ ] 1.2. Deshabilitar MSW para apuntar al backend real (`http://localhost:8000` o la URL correspondiente).

- [ ] **2. Pruebas de Integración Manual y Depuración**
    - [ ] 2.1. Ejecutar el backend y el nuevo frontend simultáneamente.
    - [ ] 2.2. Probar sistemáticamente cada vista y cada interacción del usuario.
    - [ ] 2.3. Identificar y corregir cualquier discrepancia entre el contrato de API simulado y la implementación real (ej. formatos de fecha, casing de claves, etc.).

- [ ] **Criterio de Éxito:** La aplicación web funciona de extremo a extremo con el backend real, replicando toda la funcionalidad probada en la Fase 2.

---

## Fase 4: Pruebas E2E, Despliegue y Limpieza

*   **Objetivo:** Validar el sistema integrado de forma automatizada, definir la nueva estrategia de despliegue y eliminar todo el código obsoleto.
*   **Estado:** `PENDIENTE`

### Tareas:

- [ ] **1. Pruebas de Extremo a Extremo (E2E)**
    - [ ] 1.1. Configurar **Playwright** para ejecutar pruebas contra la aplicación integrada.
    - [ ] 1.2. Crear un script de prueba para el "Golden Path": iniciar sesión (si aplica), activar una estrategia, aprobar una oportunidad, verificar la creación de la orden.
    - [ ] **Criterio de Éxito:** El test E2E se ejecuta de forma fiable con un solo comando.

- [ ] **2. Estrategia de Despliegue Simplificada (Local-First)**
    - [ ] 2.1. Configurar FastAPI para servir los archivos estáticos de producción de la build de React.
    - [ ] 2.2. Crear un nuevo `docker-compose.yml` que solo contenga `ultibot_backend` y la base de datos.
    - [ ] 2.3. Actualizar el `README.md` con las nuevas y sencillas instrucciones de despliegue: `docker-compose up --build`.

- [ ] **3. Tierra Quemada (Scorched Earth)**
    - [ ] 3.1. **Eliminar** el directorio completo `src/ultibot_ui/`.
    - [ ] 3.2. **Eliminar** todos los tests asociados a la antigua UI (`tests/ui/`, etc.).
    - [ ] 3.3. **Eliminar** `Dockerfile.frontend` y cualquier configuración relacionada con VNC/XFCE.
    - [ ] **Criterio de Éxito:** El codebase está 100% libre de los artefactos de la UI de PySide6. El proyecto es ahora una aplicación web pura.
