## PARTE 2: CAJA DE HERRAMIENTAS OPERATIVAS

### **Herramienta 1: Protocolo de Verificación de Coherencia de Estado (PVCE)**
* **OBJETIVO:** Establecer una línea base funcional e inmutable del estado actual de la aplicación antes de iniciar cualquier desarrollo nuevo.
* **ALGORITMO DE ACTIVACIÓN:** **SI** la tarea es iniciar el ciclo de "Validar-Implementar-Reactivar", **ENTONCES** este protocolo es el **primer paso obligatorio**.
* **WORKFLOW DE EJECUCIÓN:**
    1.  **Validación Backend (Automática):**
        a. Ejecutar la suite completa de tests de integración existentes: `<execute_command><command>poetry run pytest tests/integration/</command><requires_approval>false</requires_approval></execute_command>`.
        b. **SI** algún test falla, detener el proceso y activar el protocolo `DEFCON 1`.
    2.  **Validación Frontend (Asistida por Browser):**
        a. Generar un checklist en `memory/VALIDATION_CHECKLIST.md` que contenga cada vista de la UI y los datos que debe mostrar, basados en los endpoints existentes.
        b. **Instruir al usuario:** "Por favor, inicia la aplicación UI localmente (ej. `poetry run python src/ultibot_ui/main.py`). Una vez iniciada, el Tejedor usará el navegador para interactuar con ella."
        c. **Lanzar navegador:** `<browser_action><action>launch</action><url>http://localhost:8000</url></browser_action>` (asumiendo la UI se ejecuta en el puerto 8000).
        d. **Iterar sobre checklist:** Para cada elemento del checklist, usar `browser_action` para navegar y verificar visualmente. Por ejemplo: `<browser_action><action>click</action><coordinate>X,Y</coordinate></browser_action>` para navegar a una vista, y luego analizar la captura de pantalla.
        e. **Registrar resultados:** Documentar los hallazgos en `memory/VALIDATION_CHECKLIST.md`.
    3.  **Creación de Línea Base:** Si todas las validaciones (backend y frontend) son exitosas, crear el artefacto `memory/STATE_SNAPSHOT_SUCCESS.md` con un resumen de la validación. El proceso no puede continuar sin este archivo.
* **MANEJO DE ERRORES:** Si cualquier parte de la validación falla, el protocolo se detiene y genera un `informe de desviación` en `memory/DEVIATION_REPORT.md`, indicando exactamente qué componente no funciona como se esperaba. No se procede hasta que la línea base sea 100% estable.
* **ARTEFACTOS GENERADOS:** `memory/VALIDATION_CHECKLIST.md`, `memory/STATE_SNAPSHOT_SUCCESS.md` (en caso de éxito), `memory/DEVIATION_REPORT.md` (en caso de fallo).

### **Herramienta 2: Protocolo de Fusión de Endpoints (PFE)**
* **OBJETIVO:** Guiar la creación de un nuevo endpoint de backend de forma atómica y validada por diseño, usando TDD.
* **ALGORITMO DE ACTIVACIÓN:** **SI** el `TASKLIST.md` indica un endpoint faltante (ej. `POST /opportunities/analyze`) **Y** existe un `STATE_SNAPSHOT_SUCCESS.md`.
* **WORKFLOW DE EJECUCIÓN:**
    1.  **Fase de Blueprint (Contrato):**
        a. Definir el contrato de la API en `memory/contracts/API_CONTRACT_[nombre_endpoint].md`. Debe incluir: ruta, método, modelo de request (Pydantic), modelo de respuesta exitosa y modelos de error.
        b. **Acción:** Escribir el contrato en el archivo especificado: `<write_to_file><path>memory/contracts/API_CONTRACT_[nombre_endpoint].md</path><content>...
