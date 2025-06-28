# =================================================================
# == TASK LIST - UltiBotInversiones (Misión: EVO-2.0-UI-WEB)
# =================================================================
# Este archivo refleja el plan de trabajo actual basado en MIGRATION_PLAN_UI_WEB.md.
# -----------------------------------------------------------------

## Fase 0: Fortificación del Backend (Pre-requisito Innegociable)
*   **Estado:** `EN PROGRESO`

- [x] **1. Implementar Pruebas Unitarias de Modelos de Dominio**
- [x] **2. Implementar Pruebas Unitarias de Estrategias de Trading**
- [ ] **3. Expandir Pruebas de Integración de API**
    - [ ] 3.1. Ampliar la cobertura de `tests/integration/api/v1/endpoints` para todos los endpoints definidos en `API_CONTRACT_MAP.md`.
    - [ ] 3.2. Priorizar endpoints de `trading`, `market_data`, `opportunities`, y `portfolio`.
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
*   **Estado:** `COMPLETADO`
*   **Deuda Técnica Identificada:**
    - [ ] **(Pendiente)** Escribir pruebas unitarias y de componentes para hooks y componentes con lógica de negocio.
    - **Acción Requerida:** Priorizar la creación de tests para los flujos críticos (crear orden, aprobar oportunidad).

---

## Fase 3: Integración con el Backend Real
*   **Estado:** `PENDIENTE`

- [ ] **1. El "Interruptor" (The Switch)**
- [ ] **2. Pruebas de Integración Manual y Depuración**

---

## Fase 4: Pruebas E2E, Despliegue y Limpieza
*   **Estado:** `PENDIENTE`

- [ ] **1. Pruebas de Extremo a Extremo (E2E) con Playwright**
- [ ] **2. Estrategia de Despliegue Simplificada (Local-First)**
- [ ] **3. Tierra Quemada (Scorched Earth)**
