# Evaluación y Propuesta de Mejoras para la UI (UI v2)

## 1. Resumen Ejecutivo

El objetivo de esta evaluación es alinear las capacidades de la interfaz de usuario (UI) con la robusta funcionalidad del backend de `UltiBotInversiones`. El análisis revela una **brecha significativa** entre los servicios disponibles en el backend y su representación visual en la UI actual, que está construida con PySide6.

La UI actual es funcional pero rudimentaria. Carece de vistas para servicios críticos como el análisis de rendimiento, la reportería, la configuración y el monitoreo del sistema. Las vistas existentes, como la del portafolio y las estrategias, ofrecen una funcionalidad mínima.

**Decisión:** Siguiendo la directriz del usuario, se procederá con la **Ruta A: Evolución de la UI de Escritorio (PySide6)**, enfocándose en mejoras incrementales y de alto valor para la aplicación existente. El objetivo es lograr una "producción perfecta" a corto plazo, transformando la aplicación en un verdadero centro de control de inversiones.

---

## 2. Análisis del Estado Actual

### 2.1. Brecha Funcional: Backend vs. UI

| Servicio Backend | Vista UI Correspondiente | Estado / Brecha |
| :--- | :--- | :--- |
| `portfolio_service.py` | `portfolio_view.py` | ✅ **Cubierto (Básico)**. Muestra activos y distribución. |
| `strategy_service.py` | `strategies_view.py` | ⚠️ **Cubierto (Muy Básico)**. Solo lista nombres. |
| `market_data_service.py` | `opportunities_view.py` | ✅ **Cubierto (Parcial)**. |
| `performance_service.py` | **NINGUNA** | ❌ **BRECHA CRÍTICA**. No hay visualización de P&L histórico, drawdown, etc. |
| `trading_report_service.py` | **NINGUNA** | ❌ **BRECHA CRÍTICA**. No se pueden generar ni ver informes. |
| `order_execution_service.py` | **NINGUNA** | ❌ **BRECHA ALTA**. No hay historial de órdenes ni detalles de ejecución. |
| `config_service.py` | **NINGUNA** | ❌ **BRECHA ALTA**. La configuración no es gestionable desde la UI. |
| `credential_service.py` | **NINGUNA** | ❌ **BRECHA ALTA**. Las credenciales no son gestionables desde la UI. |
| `notification_service.py` | **NINGUNA** | ❌ **BRECHA MEDIA**. No hay un centro de notificaciones. |
| `trading_engine_service.py` | **NINGUNA** | ❌ **BRECHA MEDIA**. No hay monitoreo del estado del motor. |
| `ai_orchestrator_service.py` | **NINGUNA** | ❌ **BRECHA MEDIA**. No hay interfaz para la orquestación de IA. |

### 2.2. Crítica de Vistas Actuales

*   **`portfolio_view.py`**: Funcional, pero visualmente simple. El gráfico de tarta es estándar. Carece de gráficos de evolución histórica del valor del portafolio.
*   **`strategies_view.py`**: Extremadamente simple. Es solo una lista de texto sin formato. No muestra el rendimiento, el estado (activo/inactivo), los parámetros, ni permite ninguna acción sobre las estrategias.

---

## 3. Plan de Acción Detallado y Extendido (Ruta A)

**Objetivo:** Implementar mejoras incrementales, rápidas y de alto valor en la UI de escritorio existente para cubrir las brechas funcionales más críticas y mejorar drásticamente la productividad del usuario.

**Fases de Implementación (Priorizadas por Impacto y Velocidad):**

##### **Fase 1: Mejora Crítica de `StrategiesView` (Alto Impacto, Esfuerzo Moderado)**
*   **Objetivo:** Transformar la lista de estrategias actual, que es solo informativa, en un panel de control interactivo y funcional.
*   **Acciones Concretas:**
    1.  **Reemplazar `QListWidget` por `QTableWidget`:** Esto permitirá una visualización estructurada.
    2.  **Añadir Columnas de Datos Clave:**
        *   `Nombre de Estrategia`
        *   `Estado` (ej. "Activa", "Inactiva", "Error") con indicadores de color.
        *   `P&L Total` (obtenido de `performance_service`).
        *   `Nº de Operaciones`.
    3.  **Añadir Botones de Acción por Fila:**
        *   Un botón para `Activar / Desactivar` la estrategia.
        *   Un botón para `Ver Detalles` que podría abrir un modal con logs o parámetros.
*   **Resultado Esperado:** El usuario podrá monitorear el rendimiento de cada estrategia de un vistazo y realizar acciones básicas de gestión directamente desde la UI.

##### **Fase 2: Creación de `PerformanceView` (Alto Impacto, Esfuerzo Alto)**
*   **Objetivo:** Crear un dashboard dedicado para el análisis del rendimiento global del portafolio, abordando una de las brechas más críticas.
*   **Acciones Concretas:**
    1.  Crear el nuevo archivo `src/ultibot_ui/views/performance_view.py`.
    2.  Integrar `QtCharts` para visualizar:
        *   **Gráfico de Línea:** Evolución del valor total del portafolio a lo largo del tiempo.
        *   **Gráfico de Barras:** P&L desglosado por día, semana o mes.
    3.  Añadir `QLabels` para mostrar métricas clave calculadas por el `performance_service`:
        *   `Sharpe Ratio`
        *   `Máximo Drawdown`
        *   `Tasa de Acierto (Win Rate)`
*   **Resultado Esperado:** El usuario obtendrá una visión cuantitativa y clara del rendimiento histórico de sus inversiones, permitiendo una toma de decisiones informada.

##### **Fase 3: Creación de `OrdersView` (Impacto Medio, Esfuerzo Moderado)**
*   **Objetivo:** Proporcionar un historial de órdenes completo y transparente para auditoría y seguimiento.
*   **Acciones Concretas:**
    1.  Crear el nuevo archivo `src/ultibot_ui/views/orders_view.py`.
    2.  Implementar una `QTableWidget` con capacidad de filtrado (por fecha, símbolo, etc.).
    3.  Columnas a mostrar: `Fecha/Hora`, `Símbolo`, `Tipo (Compra/Venta)`, `Cantidad`, `Precio de Ejecución`, `Estado`.
*   **Resultado Esperado:** El usuario podrá auditar cada operación ejecutada por el bot, aumentando la confianza y la transparencia.

---
#### **Plan Extendido (Visión de Usuario para Productividad Máxima)**
Para transformar la aplicación en un verdadero centro de control de inversiones, se proponen las siguientes fases adicionales que se enfocan en la productividad y el control del usuario:

##### **Fase 4: Creación del "Terminal de Trading" (Impacto Muy Alto)**
*   **Objetivo:** Otorgar al usuario control manual y rápido para intervenir en el mercado, mejorando drásticamente la capacidad de respuesta.
*   **Herramientas Clave:**
    *   **Panel de Órdenes Rápidas:** Formularios optimizados para enviar órdenes de `COMPRA`/`VENTA` (Mercado, Límite) con un solo clic.
    *   **Botones de Emergencia:** Un botón de "Pánico" para `Liquidar Todas las Posiciones` o `Pausar Todas las Estrategias` instantáneamente.
    *   **Vista de Posiciones Abiertas:** Un resumen en tiempo real de las posiciones actuales, separado de los activos a largo plazo del portafolio.

##### **Fase 5: Implementación del "Laboratorio de Estrategias" (Impacto Estratégico)**
*   **Objetivo:** Permitir al usuario probar, validar y optimizar estrategias contra datos históricos (`backtesting`) antes de arriesgar capital.
*   **Herramientas Clave:**
    *   **Interfaz de Backtesting:** Un formulario intuitivo para seleccionar una estrategia, un rango de fechas, un símbolo y parámetros específicos.
    *   **Visualizador de Resultados de Backtest:** Gráficos interactivos que superpongan las operaciones sobre el gráfico de precios, acompañados de un informe detallado con métricas de rendimiento (P&L, Drawdown, Win Rate, etc.).

##### **Fase 6: Desarrollo del "Centro de Mando IA" (Impacto Futuro)**
*   **Objetivo:** Crear una interfaz para interactuar, supervisar y colaborar con el `ai_orchestrator_service`.
*   **Herramientas Clave:**
    *   **Feed de Señales IA:** Una lista en tiempo real de las recomendaciones o análisis generados por la IA.
    *   **Panel de Aprobación de Operaciones:** Permitir que la IA sugiera operaciones que el usuario pueda aprobar o rechazar con un solo clic ("Human-in-the-loop").
    *   **Visualizador de Confianza IA:** Un medidor o gráfico que muestre el nivel de confianza de la IA en sus predicciones, ayudando al usuario a ponderar las sugerencias.

---

## 4. Conclusión y Próximos Pasos

Siguiendo la decisión del usuario, el proyecto se enfocará en la **Ruta A: Evolución de la UI de Escritorio (PySide6)**. El plan de acción detallado y por fases permitirá entregar valor de forma rápida e incremental, abordando las brechas funcionales más críticas para lograr una versión de producción robusta y funcional a corto plazo. El siguiente paso es iniciar la implementación de la **Fase 1**, comenzando por la mejora de `StrategiesView`.
