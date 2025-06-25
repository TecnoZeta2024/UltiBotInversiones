# Self-Improving Cline Reflection

## Objective: Offer opportunities to continuously improve .clinerules based on user interactions and feedback.

## Trigger: Before using the attempt_completion tool for any task that involved user feedback provided at any point during the conversation, or involved multiple non-trivial steps (e.g., multiple file edits, complex logic generation).

## Process:
- Offer Reflection: Ask the user: "Before I complete the task, would you like me to reflect on our interaction and suggest potential improvements to the active .clinerules?"
- Await User Confirmation: Proceed to attempt_completion immediately if the user declines or doesn't respond affirmatively.
- If User Confirms: 
    1. Review Interaction: Synthesize all feedback provided by the user throughout the entire conversation history for the task. Analyze how this feedback relates to the active .clinerules and identify areas where modified instructions could have improved the outcome or better aligned with user preferences. 
    2. Identify Active Rules: List the specific global and workspace .clinerules files active during the task. 
    3. Formulate & Propose Improvements: Generate specific, actionable suggestions for improving the content of the relevant active rule files. Prioritize suggestions directly addressing user feedback. Use replace_in_file diff blocks when practical, otherwise describe changes clearly. 
    4. Await User Action on Suggestions: Ask the user if they agree with the proposed improvements and if they'd like me to apply them now using the appropriate tool (replace_in_file or write_to_file). Apply changes if approved, then proceed to attempt_completion.

# Constraint: Do not offer reflection if:
- No .clinerules were active.
- The task was very simple and involved no feedback.

---

## Suggested Improvements from Interactions

### 1. Reforzar la verificación de la aplicación de cambios en entornos con recarga automática:
Si un error persiste después de aplicar un cambio a un archivo y el servidor se reinicia automáticamente (ej. Uvicorn con `--reload`), y los logs del servidor no muestran un error de carga, considere un reinicio manual del proceso del servidor (ej. `taskkill /F /IM <nombre_proceso>.exe` en Windows o `killall <nombre_proceso>` en Linux/macOS) **y la eliminación de artefactos persistentes como bases de datos locales (`ultibot_local.db`)** antes de reintentar la operación. Esto asegura que la última versión del código esté en uso y que los esquemas de datos estén sincronizados.

### 2. Mejorar la guía para la depuración de errores de validación de Pydantic en scripts de prueba:
Cuando un endpoint de API devuelve un error 400 (Bad Request) o 422 (Unprocessable Entity) debido a problemas de validación de Pydantic, o cuando hay **inconsistencias en el formato de datos (ej. símbolos de trading, fechas) entre el frontend, el backend y las APIs externas**, examine cuidadosamente el campo `detail` de la respuesta JSON. Preste especial atención a los campos `loc` (ubicación del error en el payload) y `msg` (mensaje de error específico). Ajuste el payload de su script de prueba o solicitud de API de forma incremental, asegurándose de que los datos enviados coincidan con el esquema Pydantic esperado por el backend. Si es necesario, consulte directamente el modelo Pydantic relevante en el código fuente del backend (ej. `src/ultibot_backend/core/domain_models/trading_strategy_models.py` para estrategias) para entender los campos requeridos y sus tipos. **Considere también la implementación de tests de integración específicos para la consistencia del formato de datos.**
