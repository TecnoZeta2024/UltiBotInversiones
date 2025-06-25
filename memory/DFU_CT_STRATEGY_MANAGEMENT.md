# Protocolo de Diseño de Flujo de Usuario Centrado en Tareas (DFU-CT)
## Integración del Servicio AI Orchestrator en la UI

### 1. Análisis del Servicio `AIOrchestrator` (`src/ultibot_backend/services/ai_orchestrator_service.py`)

**Modelos de Datos Clave para la UI:**
*   **`TradeParameters`**: Define los parámetros de trading sugeridos por la IA (precio de entrada, stop-loss, take-profit, tamaño de posición). La UI debe mostrar estos campos de forma clara, posiblemente en una tabla o lista.
*   **`DataVerification`**: Indica el estado de verificación de datos (ej. `price_check`, `volume_check`). La UI debe mostrar estos estados, quizás con iconos de verificación o advertencia.
*   **`AIResponse`**: Estructura de salida principal de la IA, incluyendo `confidence`, `action`, `reasoning`, `trade_params`, `warnings`, y `data_verification`. Todos estos campos son cruciales para la visualización en la UI.
*   **`AIAnalysisResult`**: Clase que encapsula el resultado del análisis de la IA, incluyendo `analysis_id`, `calculated_confidence`, `suggested_action`, `reasoning_ai`, `recommended_trade_params`, `data_verification`, `processing_time_ms`, `ai_warnings`, y `model_used`. Esta es la información que la UI consumirá directamente.
*   **`OpportunityData`**: Estructura de entrada para la IA, conteniendo `opportunity_id`, `symbol`, `initial_signal`, `source_type`, `source_name`, `detected_at`. La UI debe ser capaz de presentar o capturar estos detalles para iniciar un análisis.
*   **`TradingStrategyConfig`**: Configuración de la estrategia de trading. La UI debe permitir la selección o configuración de estas estrategias.
*   **`AIStrategyConfiguration`**: Configuración específica de la IA (ej. `gemini_prompt_template`, `tools_available_to_gemini`, `confidence_thresholds`). La UI debe tener una sección para gestionar estas configuraciones.

**Funcionalidades Clave del Backend Relevantes para la UI:**
*   **`analyze_opportunity_with_strategy_context_async`**: Método principal que orquesta el análisis de la IA. La UI invocará este proceso y esperará un `AIAnalysisResult`.
*   **Métodos de Formateo (`_format_historical_data`, `_format_strategy_parameters`, `_format_opportunity_details`, `_format_tools_description`)**: Aunque internos, revelan el tipo y formato de los datos que se manejan, lo que es esencial para la consistencia en la UI.

### 2. Actores y Objetivos (DFU-CT)

**Actor Principal:** Usuario de UltiBot

**Objetivo del Actor:**
*   Configurar y gestionar estrategias de trading con integración de IA.
*   Analizar oportunidades de mercado utilizando el motor de IA.
*   Visualizar los resultados detallados del análisis de la IA para tomar decisiones de trading informadas (ej. ejecutar una operación, ajustar una estrategia).
*   Monitorear el estado y el rendimiento de los análisis de IA.

### 3. Escenarios de Uso Clave (DFU-CT)

**Escenario:** Análisis de Oportunidad de Trading con IA

**Descripción:** El usuario desea obtener un análisis detallado de una oportunidad de trading específica utilizando el modelo de IA configurado.

**Pasos del Flujo:**
1.  **Detección/Selección de Oportunidad:**
    *   El sistema detecta automáticamente una oportunidad (ej. a través de un escáner de mercado o una alerta externa).
    *   Alternativamente, el usuario puede seleccionar manualmente una oportunidad de una lista o tabla en la UI.
2.  **Inicio del Análisis de IA:**
    *   El usuario hace clic en un botón "Analizar con IA" asociado a la oportunidad.
    *   La UI envía la `OpportunityData`, la `TradingStrategyConfig` seleccionada, la `AIStrategyConfiguration` activa y el `user_id` al endpoint del backend que invoca `AIOrchestrator.analyze_opportunity_with_strategy_context_async`.
3.  **Procesamiento del Análisis (Backend):**
    *   El backend invoca el `AIOrchestrator` para realizar el análisis.
    *   Durante este proceso, la UI puede mostrar un indicador de carga o estado "Analizando...".
4.  **Recepción y Visualización de Resultados:**
    *   Una vez completado el análisis, el backend devuelve un `AIAnalysisResult`.
    *   La UI recibe este resultado y lo presenta al usuario en un formato comprensible.

### 4. Puntos de Decisión y Estados del Sistema (DFU-CT)

**Puntos de Decisión:**
*   **Confianza de la IA:** ¿La `calculated_confidence` de la IA supera los `confidence_thresholds` (para trading en papel o real)? Esto puede influir en la acción sugerida y en la prominencia visual de la recomendación.
*   **Advertencias:** ¿Existen `ai_warnings`? Si es así, deben ser destacados.
*   **Verificación de Datos:** ¿El `data_verification` indica alguna discrepancia?

**Estados del Sistema (para la UI):**
*   **Oportunidad Pendiente de Análisis:** Oportunidad detectada pero aún no analizada por la IA.
*   **Análisis en Curso:** La IA está procesando la oportunidad.
*   **Análisis Completado (Éxito):** El `AIAnalysisResult` ha sido recibido y es válido.
*   **Análisis Completado (Con Advertencias):** El análisis fue exitoso pero incluye `ai_warnings`.
*   **Análisis Fallido:** El backend devolvió un error (ej. `HTTPException`). La UI debe mostrar un mensaje de error claro.
*   **Acción Sugerida:** El resultado del análisis incluye una `suggested_action` (ej. 'strong_buy', 'hold_neutral', 'sell').
*   **Parámetros de Trading Disponibles:** `recommended_trade_params` están presentes.

### 5. Diseño de la Interfaz de Usuario (DFU-CT)

**Componentes de UI Propuestos:**

1.  **Vista de Oportunidades (`OpportunitiesView`):**
    *   **Tabla/Lista de Oportunidades:**
        *   Columnas: `Symbol`, `Source Type`, `Source Name`, `Detected At`.
        *   Columna de Acción: Botón "Analizar con IA" para cada fila.
        *   Indicador de Estado: Un pequeño icono o texto que muestre si la oportunidad ya fue analizada, si el análisis está en curso, o si falló.
    *   **Filtros/Búsqueda:** Para gestionar grandes volúmenes de oportunidades.

2.  **Diálogo/Panel de Análisis de IA (`AIAnalysisDialog` o `AIAnalysisPanel`):**
    *   Se abre al hacer clic en "Analizar con IA" o al seleccionar una oportunidad analizada.
    *   **Sección de Resumen:**
        *   **Confianza:** Barra de progreso visual (ej. `QProgressBar`) o indicador numérico (`QLabel`) con color (`QPalette` o CSS) que refleje el nivel de confianza (`calculated_confidence`). Verde para alta, amarillo para media, rojo para baja.
        *   **Acción Sugerida:** Texto grande (`QLabel`) con icono (`QIcon`) y color (`QPalette` o CSS) que represente la acción (ej. flecha verde hacia arriba para 'strong_buy', círculo gris para 'hold_neutral', flecha roja hacia abajo para 'sell').
        *   **Modelo Utilizado:** `QLabel` mostrando `model_used`.
        *   **Tiempo de Procesamiento:** `QLabel` mostrando `processing_time_ms`.
    *   **Sección de Razonamiento:**
        *   Área de texto (`QTextEdit` o `QLabel` con `wordWrap`) para `reasoning_ai`.
    *   **Sección de Parámetros de Trading:**
        *   Tabla (`QTableWidget`) para `recommended_trade_params` (columnas: Parámetro, Valor).
    *   **Sección de Advertencias:**
        *   Lista (`QListWidget` o `QVBoxLayout` con `QLabel`s) para `ai_warnings`. Cada advertencia con un icono de alerta (`QIcon`).
    *   **Sección de Verificación de Datos:**
        *   Tabla (`QTableWidget`) o lista (`QListWidget`) para `data_verification` (columnas: Verificación, Estado). Iconos de verificación/error.
    *   **Botones de Acción:**
        *   "Cerrar": Para cerrar el diálogo/panel.
        *   "Ejecutar Trade" (condicional): Habilitado si la confianza es alta y no hay advertencias críticas, y si `recommended_trade_params` están presentes.
        *   "Re-analizar": Para volver a ejecutar el análisis de IA.

**Consideraciones Adicionales:**
*   **Manejo de Errores:** Mostrar `QMessageBox.critical` o un `QLabel` de error prominente si el análisis falla.
*   **Actualizaciones en Tiempo Real:** Si el análisis es asíncrono y puede tardar, considerar mecanismos de actualización de UI (ej. `QTimer` o señales de backend) para reflejar el estado.
*   **Consistencia de Datos:** Asegurar que los tipos de datos (ej. `float` para precios, `str` para acciones) se manejen correctamente entre el backend y el frontend para evitar errores de validación.
