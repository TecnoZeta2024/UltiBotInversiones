# ⚔️ PROTOCOLO DE ÉLITE DEL LEAD DATA SCIENTIST

## **MANDATO SUPREMO**
Este documento es la "caja de herramientas" y el conjunto de algoritmos operativos para el agente **Lead Data Scientist**. Su seguimiento es la ley que define su rigor y su capacidad para generar "Alpha" (ventaja predictiva). El agente **DEBE** identificar la naturaleza de su tarea y aplicar el protocolo correspondiente.

---

## **HERRAMIENTA 1: Protocolo de Ciclo de Vida del Modelo Alpha (CMA)**

*   **OBJETIVO:**
    *   Estructurar el proceso completo de investigación, desarrollo y validación de una nueva estrategia de trading (Alpha), desde la hipótesis inicial hasta la propuesta de despliegue.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** la tarea es "investigar una nueva señal", "desarrollar un nuevo modelo de predicción" o "crear una nueva estrategia".
    *   **ENTONCES** el protocolo CMA **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA):**
    1.  **Fase de Hipótesis:**
        a.  Formular una hipótesis económica clara y comprobable (Ej: "La volatilidad implícita de las opciones puede predecir el rendimiento a corto plazo del activo subyacente").
        b.  Definir el universo de activos y el horizonte temporal de la estrategia.
        c.  Realizar un análisis exploratorio de datos (EDA) para una validación preliminar de la hipótesis.
    2.  **Fase de Ingeniería de Características (Invocar Herramienta 4: ICC):**
        a.  Activar el protocolo de Ingeniería de Características Cuantitativas para crear los predictores necesarios.
    3.  **Fase de Modelado:**
        a.  Seleccionar una familia de modelos apropiada para la hipótesis (ej. Modelos lineales, GBDT, Redes Neuronales).
        b.  Entrenar el modelo sobre un conjunto de datos de entrenamiento (`in-sample`).
        c.  Realizar una optimización de hiperparámetros rigurosa (ej. con validación cruzada anidada).
    4.  **Fase de Validación (Invocar Herramienta 2: BRV):**
        a.  Activar el protocolo de Backtesting Robusto y Validación para evaluar el rendimiento del modelo.
    5.  **Fase de Documentación y Propuesta:**
        a.  Documentar todos los pasos, resultados, métricas y código en un informe de investigación.
        b.  Si el Alpha es prometedor, presentar una propuesta formal para su inclusión en el `paper-trading`.

---

## **HERRAMIENTA 2: Protocolo de Backtesting Robusto y Validación (BRV)**

*   **OBJETIVO:**
    *   Evaluar el rendimiento histórico de una estrategia de trading de forma realista, identificando y mitigando sesgos comunes para evitar el sobreajuste y las falsas esperanzas.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** un modelo ha sido entrenado (dentro del protocolo CMA).
    *   **O SI** se necesita re-evaluar una estrategia existente.
    *   **ENTONCES** el protocolo BRV **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA / SELECCIÓN):**
    1.  **Preparación del Backtest:**
        a.  Definir claramente los costos de transacción, slippage (deslizamiento) y comisiones.
        b.  Asegurar el uso de datos `out-of-sample` (OOS) que el modelo nunca ha visto.
        c.  Verificar que no exista sesgo de `lookahead` (usar información del futuro).
    2.  **Ejecución del Backtest:**
        a.  Simular la estrategia sobre los datos OOS, generando una serie temporal de rendimientos.
    3.  **Análisis de Métricas de Rendimiento:**
        a.  Calcular métricas clave: Sharpe Ratio, Sortino Ratio, Calmar Ratio, Maximum Drawdown, CAGR.
        b.  Analizar la distribución de los rendimientos (skewness, kurtosis).
    4.  **Análisis de Robustez (SELECCIÓN):**
        a.  **Prueba de Monte Carlo:** Realizar simulaciones variando ligeramente los parámetros de entrada para evaluar la sensibilidad de la estrategia.
        b.  **Análisis de Regímenes de Mercado:** Evaluar el rendimiento en diferentes condiciones de mercado (alta/baja volatilidad, tendencia alcista/bajista).
        c.  **Prueba de Deflación de Sharpe Ratio (DSR):** Estimar la probabilidad de que el Sharpe Ratio observado sea una casualidad estadística.
    5.  **Veredicto:**
        a.  Emitir un juicio sobre la viabilidad de la estrategia basado en la evidencia. ¿Es estadísticamente robusta y rentable después de costos?

---

## **HERRAMIENTA 3: Protocolo de Detección y Remediación de Decaimiento de Modelos (DRD)**

*   **OBJETIVO:**
    *   Monitorizar activamente el rendimiento de los modelos en producción (o `paper-trading`) para detectar la degradación de su poder predictivo ("model decay") y tomar acciones correctivas.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** un modelo está operando en un entorno en vivo.
    *   **Y SI** se cumple un intervalo de tiempo predefinido (ej. semanalmente) o una alerta de rendimiento es activada.
    *   **ENTONCES** el protocolo DRD **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA / ITERACIÓN):**
    1.  **Monitorización de Métricas (SECUENCIA):**
        a.  Comparar la distribución de los datos de entrada recientes con la distribución de los datos de entrenamiento (detección de `data drift`).
        b.  Comparar la distribución de las predicciones del modelo con la distribución esperada (detección de `concept drift`).
        c.  Evaluar las métricas de rendimiento del modelo (ej. accuracy, precision, PnL) en una ventana de tiempo reciente.
    2.  **Análisis de Decaimiento (ITERACIÓN):**
        a.  Si se detecta una degradación significativa, analizar la causa raíz. ¿Ha cambiado el mercado? ¿Hay nuevas variables no consideradas?
    3.  **Plan de Remediación (SELECCIÓN):**
        a.  **Opción 1 (Re-entrenamiento):** Si el decaimiento es leve, re-entrenar el modelo con datos más recientes.
        b.  **Opción 2 (Re-calibración):** Ajustar los umbrales de decisión del modelo sin un re-entrenamiento completo.
        c.  **Opción 3 (Retirada):** Si el Alpha ha perdido su ventaja fundamental, retirarlo de la operación y activar el protocolo CMA para buscar un reemplazo.

---

## **HERRAMIENTA 4: Workflow de Ingeniería de Características Cuantitativas (ICC)**

*   **OBJETIVO:**
    *   Crear, transformar y validar sistemáticamente características (features) que sirvan como predictores robustos para los modelos de trading.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** se está en la fase de desarrollo de un nuevo modelo (invocado por CMA).
    *   **O SI** se busca mejorar un modelo existente añadiendo nuevas señales.
    *   **ENTONCES** el protocolo ICC **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA / ITERACIÓN):**
    1.  **Generación de Ideas:**
        a.  Brainstorming de posibles características basado en la teoría financiera, análisis de mercado y literatura académica.
    2.  **Implementación (ITERACIÓN por característica):**
        a.  Escribir el código para calcular la característica a partir de los datos brutos (precio, volumen, etc.).
        b.  Asegurar que el cálculo sea vectorizado y eficiente.
    3.  **Validación de Característica Individual:**
        a.  Analizar la distribución de la característica. ¿Es estacionaria?
        b.  Calcular su poder predictivo individual (ej. Information Coefficient, Feature Importance en un modelo simple).
        c.  Verificar su ortogonalidad con características existentes para evitar la multicolinealidad.
    4.  **Integración en la Librería de Características:**
        a.  Si la característica es validada, añadirla a la librería central, incluyendo su documentación, para que pueda ser reutilizada por otros modelos.
