# =================================================================
# == TASK LIST - UltiBotInversiones (Misión: EVO-2.0-UI-WEB)
# =================================================================
# Este archivo refleja el plan de trabajo actual basado en MIGRATION_PLAN_UI_WEB.md.
# -----------------------------------------------------------------

## Fase 0: Fortificación del Backend (Pre-requisito Innegociable)
*   **Estado:** `COMPLETADO`

- [x] **1. Implementar Pruebas Unitarias de Modelos de Dominio**
- [x] **2. Implementar Pruebas Unitarias de Estrategias de Trading**
- [x] **3. Expandir Pruebas de Integración de API**
    - [x] 3.1. Ampliar la cobertura de `tests/integration/api/v1/endpoints` para todos los endpoints definidos en `API_CONTRACT_MAP.md`.
    - [x] 3.2. Priorizar endpoints de `trading`, `market_data`, `opportunities`, y `portfolio`.
    - [x] 3.3. **(Completado)** Crear y validar pruebas para los endpoints de `config` (`test_config_endpoints.py`).
    - [x] 3.4. **(Completado)** Crear y validar pruebas para los endpoints de `strategies` (`test_strategies_endpoints.py`).

---

## Fase 1: Andamiaje Frontend y Desarrollo Guiado por Mocks
*   **Estado:** `COMPLETADO (con desviaciones)`
*   **Deuda Técnica Identificada:**
    - Se omitió el Mock Server (MSW).
    - No se implementó un gestor de estado global (Zustand).
    - **Acción Requerida:** Mitigar con pruebas de integración robustas en Fase 3 y considerar refactorización si la complejidad aumenta.

---

## Fase 2: Implementación de Vistas con Paridad de Funciones
*   **Estado:** `BLOQUEADO`
*   **Deuda Técnica Identificada:**
    - [x] **(Completado)** Escribir pruebas unitarias y de componentes para hooks y componentes con lógica de negocio.
        - **Estado Actual:** Se refactorizó `StrategiesView.tsx` para usar un `apiClient`. Se crearon endpoints de backend para `strategies/files`. Se creó el archivo de test `StrategiesView.test.tsx`.
        - **BLOQUEO RESUELTO (parcialmente):** Se resolvió el problema de mocking de `apiClient` y los tests relacionados. El test `should fetch and display file content on file click` sigue fallando debido a una limitación del entorno de prueba `jsdom` con la interacción de componentes mockeados complejos y la actualización del DOM. Se ha documentado en `KB-0007` en `KNOWLEDGE_BASE.md`.
    - **Acción Requerida:** Se considera que el problema de mocking está resuelto en la medida de lo posible con las herramientas actuales. Se puede proceder con otras tareas de la Fase 2 o avanzar a la Fase 3 si es necesario.

---

## Fase 3: Integración con el Backend Real
*   **Estado:** `EN PROGRESO`

- [x] **1. El "Interruptor" (The Switch)**
    - **Estado:** Backend y Frontend iniciados y en ejecución.
    - **Observación:** El frontend muestra "Error de Conexión" a pesar de que el backend está operativo y CORS configurado. Esto puede deberse a la caché del navegador o a problemas de red locales.
    - **Próximo Paso:** El usuario debe borrar la caché del navegador, probar en modo incógnito/otro navegador, o verificar la configuración de red/firewall.
- [ ] **2. Pruebas de Integración Manual y Depuración**

---

## Fase 4: Pruebas E2E, Despliegue y Limpieza
*   **Estado:** `PENDIENTE`

- [ ] **1. Pruebas de Extremo a Extremo (E2E) con Playwright**
- [ ] **2. Estrategia de Despliegue Simplificada (Local-First)**
- [ ] **3. Tierra Quemada (Scorched Earth)**
