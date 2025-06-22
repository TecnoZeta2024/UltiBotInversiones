# Plan de Tareas para la Evolución de la UI (UI v2)

## 1. Resumen Ejecutivo
**Misión:** Transformar la aplicación de escritorio PySide6 en un "Centro de Control de Inversiones" completo, cerrando las brechas funcionales entre el backend y la UI. Este plan de tareas es la hoja de ruta para ejecutar la visión descrita en `UI_v2.md`.

---

## 2. Fases de Implementación

### **Fase 1: Mejora Crítica de `StrategiesView` (Alto Impacto)**
**Objetivo:** Convertir la lista de estrategias en un panel de control interactivo.

| ID de Tarea | Tarea / Subtarea | Estado | Prioridad | Archivos Afectados | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UI-F1-T1` | Reemplazar `QListWidget` por `QTableWidget` en `strategies_view.py`. | `[x] Completado` | Crítica | `src/ultibot_ui/views/strategies_view.py` | Base para la nueva vista. |
| `UI-F1-T2` | Añadir columnas: Nombre, Estado, P&L Total, Nº de Operaciones. | `[x] Completado` | Crítica | `src/ultibot_ui/views/strategies_view.py` | Columnas añadidas. La conexión de datos se hará en `UI-F1-T3`. |
| `UI-F1-T3` | Implementar worker para obtener datos de estrategias de forma asíncrona. | `[x] Completado` | Crítica | `src/ultibot_ui/workers.py` | Creado `StrategiesWorker` con datos mock. La conexión a la vista es el siguiente paso. |
| `UI-F1-T4` | Añadir botones de acción por fila: `Activar/Desactivar` y `Ver Detalles`. | `[x] Completado` | Alta | `src/ultibot_ui/views/strategies_view.py` | La funcionalidad de los botones se implementará después. |

### **Fase 2: Creación de `PerformanceView` (Alto Impacto)**
**Objetivo:** Crear un dashboard para el análisis de rendimiento global.

| ID de Tarea | Tarea / Subtarea | Estado | Prioridad | Archivos Afectados | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UI-F2-T1` | Crear el nuevo archivo `src/ultibot_ui/views/performance_view.py`. | `[x] Completado` | Alta | `src/ultibot_ui/views/performance_view.py` | Esqueleto inicial del widget. |
| `UI-F2-T2` | Integrar `QtCharts` para gráfico de evolución del portafolio. | `[x] Completado` | Alta | `src/ultibot_ui/views/performance_view.py` | Usar `QChartView` y `QLineSeries`. |
| `UI-F2-T3` | Integrar `QtCharts` para gráfico de P&L por período. | `[x] Completado` | Alta | `src/ultibot_ui/views/performance_view.py` | Usar `QBarSeries`. |
| `UI-F2-T4` | Añadir `QLabels` para métricas clave (Sharpe, Drawdown, Win Rate). | `[x] Completado` | Media | `src/ultibot_ui/views/performance_view.py` | - |
| `UI-F2-T5` | Implementar worker para obtener datos de rendimiento. | `[x] Completado` | Alta | `src/ultibot_ui/workers.py` | Creado `PerformanceWorker` y conectado a la vista. |

### **Fase 3: Creación de `OrdersView` (Impacto Medio)**
**Objetivo:** Proporcionar un historial de órdenes completo y transparente.

| ID de Tarea | Tarea / Subtarea | Estado | Prioridad | Archivos Afectados | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UI-F3-T1` | Crear el nuevo archivo `src/ultibot_ui/views/orders_view.py`. | `[x] Completado` | Media | `src/ultibot_ui/views/orders_view.py` | - |
| `UI-F3-T2` | Implementar `QTableWidget` con columnas: Fecha, Símbolo, Tipo, etc. | `[x] Completado` | Media | `src/ultibot_ui/views/orders_view.py` | - |
| `UI-F3-T3` | Añadir capacidad de filtrado a la tabla de órdenes. | `[x] Completado` | Baja | `src/ultibot_ui/views/orders_view.py` | Añadido filtro por símbolo y lado (compra/venta). |
| `UI-F3-T4` | Implementar worker para obtener el historial de órdenes. | `[x] Completado` | Media | `src/ultibot_ui/workers.py`, `src/ultibot_ui/views/orders_view.py` | `OrdersWorker` creado y conectado a la vista. Carga datos mock de forma asíncrona. |

---

## 3. Visión Extendida (Fases Futuras)

### **Fase 4: Creación del "Terminal de Trading" (Próxima Fase)**
**Objetivo:** Permitir la ejecución de órdenes manuales y la visualización de datos de mercado en tiempo real.

| ID de Tarea | Tarea / Subtarea | Estado | Prioridad | Archivos Afectados | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UI-F4-T1` | Crear el nuevo archivo `src/ultibot_ui/views/trading_terminal_view.py`. | `[x] Completado` | Alta | `src/ultibot_ui/views/trading_terminal_view.py` | Esqueleto inicial de la vista del terminal. |
| `UI-F4-T2` | Diseñar layout con widgets para selección de símbolo, tipo de orden, etc. | `[x] Completado` | Alta | `src/ultibot_ui/views/trading_terminal_view.py` | Incluir `QComboBox` para símbolo y tipo, `QLineEdit` para cantidad/precio. |
| `UI-F4-T3` | Añadir un gráfico en tiempo real para el precio del activo. | `[x] Completado` | Alta | `src/ultibot_ui/views/trading_terminal_view.py` | Usar `QtCharts` para mostrar la fluctuación del precio. |
| `UI-F4-T4` | Implementar `TradingTerminalWorker` para datos de mercado. | `[x] Completado` | Alta | `src/ultibot_ui/workers.py` | Worker para obtener precio y datos del libro de órdenes. |
| `UI-F4-T5` | Implementar lógica para enviar órdenes manuales. | `[x] Completado` | Crítica | `src/ultibot_ui/views/trading_terminal_view.py`, `src/ultibot_ui/services/api_client.py` | Conectar la UI con el servicio de API para ejecutar trades. |
| `UI-F4-T6` | Integrar la nueva vista en la `MainWindow`. | `[x] Completado` | Media | `src/ultibot_ui/main.py`, `src/ultibot_ui/windows/main_window.py`, `src/ultibot_ui/widgets/sidebar_navigation_widget.py` | Añadido el terminal como una nueva pestaña principal. |

### **Fase 5: Implementación del "Laboratorio de Estrategias" (Impacto Estratégico)**
**Objetivo:** Permitir al usuario probar, validar y optimizar estrategias contra datos históricos (`backtesting`).

| ID de Tarea | Tarea / Subtarea | Estado | Prioridad | Archivos Afectados | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UI-F5-T1` | Crear el nuevo archivo `src/ultibot_ui/views/strategy_lab_view.py`. | `[ ] Pendiente` | Alta | `src/ultibot_ui/views/strategy_lab_view.py` | Vista principal para el backtesting. |
| `UI-F5-T2` | Diseñar formulario de configuración de backtest. | `[ ] Pendiente` | Alta | `src/ultibot_ui/views/strategy_lab_view.py` | Incluir selección de estrategia, rango de fechas, símbolo y parámetros. |
| `UI-F5-T3` | Implementar visualizador de resultados con `QtCharts`. | `[ ] Pendiente` | Alta | `src/ultibot_ui/views/strategy_lab_view.py` | Gráfico de P&L y superposición de trades en el precio. |
| `UI-F5-T4` | Añadir tabla/vista de métricas de rendimiento del backtest. | `[ ] Pendiente` | Media | `src/ultibot_ui/views/strategy_lab_view.py` | P&L Total, Max Drawdown, Win Rate, etc. |
| `UI-F5-T5` | Implementar `BacktestingWorker` para ejecutar análisis en segundo plano. | `[ ] Pendiente` | Crítica | `src/ultibot_ui/workers.py` | Para no bloquear la UI durante el backtesting. |
| `UI-F5-T6` | Conectar worker al servicio de backtesting del backend. | `[ ] Pendiente` | Crítica | `src/ultibot_ui/workers.py` | La lógica de backtesting reside en el backend. |
| `UI-F5-T7` | Integrar la nueva vista en la `MainWindow`. | `[ ] Pendiente` | Media | `src/ultibot_ui/windows/main_window.py`, `src/ultibot_ui/widgets/sidebar_navigation_widget.py` | Añadir el laboratorio como una nueva pestaña/vista principal. |

### **Fase 6: Desarrollo del "Centro de Mando IA" (Impacto Futuro)**
**Objetivo:** Crear una interfaz para interactuar, supervisar y colaborar con el `ai_orchestrator_service`.

| ID de Tarea | Tarea / Subtarea | Estado | Prioridad | Archivos Afectados | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UI-F6-T1` | Crear el nuevo archivo `src/ultibot_ui/views/ai_command_center_view.py`. | `[ ] Pendiente` | Alta | `src/ultibot_ui/views/ai_command_center_view.py` | Vista principal para la interacción con la IA. |
| `UI-F6-T2` | Implementar widget "Feed de Señales IA" en tiempo real. | `[ ] Pendiente` | Alta | `src/ultibot_ui/views/ai_command_center_view.py` | Usar `QListWidget` o `QTableWidget` para mostrar señales. |
| `UI-F6-T3` | Implementar widget "Panel de Aprobación de Operaciones". | `[ ] Pendiente` | Crítica | `src/ultibot_ui/views/ai_command_center_view.py` | Debe tener botones claros para `Aprobar` / `Rechazar` operaciones sugeridas. |
| `UI-F6-T4` | Implementar widget "Visualizador de Confianza IA". | `[ ] Pendiente` | Media | `src/ultibot_ui/views/ai_command_center_view.py` | Puede ser un `QProgressBar` o un dial personalizado. |
| `UI-F6-T5` | Implementar `AICommandCenterWorker` para comunicación con `ai_orchestrator_service`. | `[ ] Pendiente` | Crítica | `src/ultibot_ui/workers.py` | Gestionará la recepción de señales y el envío de aprobaciones. |
| `UI-F6-T6` | Integrar la nueva vista en la `MainWindow`. | `[ ] Pendiente` | Media | `src/ultibot_ui/windows/main_window.py`, `src/ultibot_ui/widgets/sidebar_navigation_widget.py` | Añadir el centro de mando como una nueva pestaña/vista principal. |
