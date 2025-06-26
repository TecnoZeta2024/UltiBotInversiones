# Tarea: [TASK-BACKEND-REFACTOR-001] - Refactorización y Sincronización Holística del Backend

## Misión:
Alinear completamente la lógica, los modelos de datos y los endpoints del backend con la nueva arquitectura asíncrona y los flujos de datos del frontend refactorizado. El objetivo es lograr un sistema unificado, estable y sin errores de comunicación.

---

### **Fase 1: Análisis y Mapeo de Interacciones (Blueprint)**
*   [x] **1.1. Análisis de Código Frontend:** Escanear sistemáticamente `src/ultibot_ui/` (vistas, widgets, servicios) para identificar todas las llamadas a la API realizadas a través de `api_client.py`.
*   [x] **1.2. Creación del Mapa de Contratos:** Generar un artefacto en `memory/BACKEND_REFACTOR_MAP.md` que documente cada interacción. La tabla debe contener: `UI Component | Frontend Method | HTTP Method | Backend Endpoint | Request Payload Schema | Expected Response Schema`.

---

### **Fase 2: Auditoría y Detección de Desviaciones (Measure)**
*   [x] **2.1. Auditoría de Modelos Pydantic:** Para cada endpoint en el mapa, auditar los modelos Pydantic correspondientes en `src/ultibot_backend/core/domain_models/` y `src/ultibot_backend/api/v1/` contra los esquemas de payload y respuesta definidos.
*   [x] **2.2. Auditoría de la Capa de Servicios:** Revisar la lógica en `src/ultibot_backend/services/` para asegurar que el procesamiento de datos se alinea con los contratos del mapa.
*   [x] **2.3. Registro de Discrepancias:** Documentar cada desviación (campos faltantes, tipos incorrectos, lógica de negocio desactualizada) en una sección "Discrepancy Log" dentro de `memory/BACKEND_REFACTOR_MAP.md`.

---

### **Fase 3: Refactorización y Pruebas de Integración (Assemble)**
*   [ ] **3.1. Refactorización de Modelos y Servicios:** Corregir todas las discrepancias documentadas, trabajando de manera modular (un servicio o endpoint a la vez).
*   [ ] **3.2. Desarrollo Guiado por Pruebas (TDD):** Para cada corrección, crear o actualizar un test de integración en `tests/integration/api/`. Estos tests deben simular las llamadas del frontend con los nuevos payloads y validar las respuestas del backend.
*   [ ] **3.3. Estandarización de Formatos:** Asegurar la consistencia en formatos de datos críticos (ej. `BTC/USDT` vs `BTCUSDT`, formatos de fecha) a través de toda la capa de servicio del backend.

---

### **Fase 4: Validación del Sistema Completo (Decide)**
*   [ ] **4.1. Preparación del Entorno:** Eliminar la base de datos local (`ultibot_local.db`) para forzar la recreación del esquema.
*   [ ] **4.2. Ejecución de la Suite de Pruebas Completa:** Correr `pytest` y asegurar que el 100% de los tests (unitarios y de integración) pasen.
*   [ ] **4.3. Pruebas End-to-End (E2E) Manuales:**
    *   [ ] Iniciar el servidor backend (`poetry run start_backend`).
    *   [ ] Iniciar la interfaz de usuario (`run_ui_local.bat`).
    *   [ ] Ejecutar un checklist de pruebas funcionales cubriendo todas las vistas y acciones de la UI, monitoreando `logs/frontend.log` y `logs/backend.log` en busca de errores.

---

### **Fase 5: Cierre y Documentación (Record)**
*   [ ] **5.1. Limpieza de Artefactos:** Archivar o eliminar `memory/BACKEND_REFACTOR_MAP.md`.
*   [ ] **5.2. Registro Final:** Actualizar `memory/PROJECT_LOG.md` con una entrada que resuma el resultado de la refactorización.
*   [ ] **5.3. Reflexión de Auto-Mejora:** Ofrecer reflexionar sobre las `.clinerules` según el protocolo.
*   [ ] **5.4. Entrega Final:** Presentar el sistema completamente funcional y sincronizado usando `attempt_completion`.
