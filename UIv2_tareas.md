# Plan de Tareas para la Evolución de la UI (UI v2)

## 1. Resumen Ejecutivo
**Misión:** Transformar la aplicación de escritorio PySide6 en un "Centro de Control de Inversiones" completo, cerrando las brechas funcionales entre el backend y la UI. Este plan de tareas es la hoja de ruta para ejecutar la visión descrita en `UI_v2.md`.

---

## 2. Fases de Implementación

### **Fase 1: Mejora Crítica de `StrategiesView` (Alto Impacto)**
**Objetivo:** Convertir la lista de estrategias en un panel de control interactivo.

| ID de Tarea | Tarea / Subtarea | Estado | Prioridad | Archivos Afectados | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UI-F1-T1` | Reemplazar `QListWidget` por `QTableWidget` en `strategies_view.py`. | `[ ] Pendiente` | Crítica | `src/ultibot_ui/views/strategies_view.py` | Base para la nueva vista. |
| `UI-F1-T2` | Añadir columnas: Nombre, Estado, P&L Total, Nº de Operaciones. | `[ ] Pendiente` | Crítica | `src/ultibot_ui/views/strategies_view.py` | Requiere conectar con `performance_service`. |
| `UI-F1-T3` | Implementar worker para obtener datos de estrategias de forma asíncrona. | `[ ] Pendiente` | Crítica | `src/ultibot_ui/workers.py` | Evitará congelar la UI. |
| `UI-F1-T4` | Añadir botones de acción por fila: `Activar/Desactivar` y `Ver Detalles`. | `[ ] Pendiente` | Alta | `src/ultibot_ui/views/strategies_view.py` | La funcionalidad de los botones se implementará después. |

### **Fase 2: Creación de `PerformanceView` (Alto Impacto)**
**Objetivo:** Crear un dashboard para el análisis de rendimiento global.

| ID de Tarea | Tarea / Subtarea | Estado | Prioridad | Archivos Afectados | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UI-F2-T1` | Crear el nuevo archivo `src/ultibot_ui/views/performance_view.py`. | `[ ] Pendiente` | Alta | `src/ultibot_ui/views/performance_view.py` | Esqueleto inicial del widget. |
| `UI-F2-T2` | Integrar `QtCharts` para gráfico de evolución del portafolio. | `[ ] Pendiente` | Alta | `src/ultibot_ui/views/performance_view.py` | Usar `QChartView` y `QLineSeries`. |
| `UI-F2-T3` | Integrar `QtCharts` para gráfico de P&L por período. | `[ ] Pendiente` | Alta | `src/ultibot_ui/views/performance_view.py` | Usar `QBarSeries`. |
| `UI-F2-T4` | Añadir `QLabels` para métricas clave (Sharpe, Drawdown, Win Rate). | `[ ] Pendiente` | Media | `src/ultibot_ui/views/performance_view.py` | - |
| `UI-F2-T5` | Implementar worker para obtener datos de rendimiento. | `[ ] Pendiente` | Alta | `src/ultibot_ui/workers.py` | - |

### **Fase 3: Creación de `OrdersView` (Impacto Medio)**
**Objetivo:** Proporcionar un historial de órdenes completo y transparente.

| ID de Tarea | Tarea / Subtarea | Estado | Prioridad | Archivos Afectados | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `UI-F3-T1` | Crear el nuevo archivo `src/ultibot_ui/views/orders_view.py`. | `[ ] Pendiente` | Media | `src/ultibot_ui/views/orders_view.py` | - |
| `UI-F3-T2` | Implementar `QTableWidget` con columnas: Fecha, Símbolo, Tipo, etc. | `[ ] Pendiente` | Media | `src/ultibot_ui/views/orders_view.py` | - |
| `UI-F3-T3` | Añadir capacidad de filtrado a la tabla de órdenes. | `[ ] Pendiente` | Baja | `src/ultibot_ui/views/orders_view.py` | Se puede implementar en una iteración posterior. |
| `UI-F3-T4` | Implementar worker para obtener el historial de órdenes. | `[ ] Pendiente` | Media | `src/ultibot_ui/workers.py` | - |

---

## 3. Visión Extendida (Fases Futuras)

*   **Fase 4: Creación del "Terminal de Trading"**
*   **Fase 5: Implementación del "Laboratorio de Estrategias"**
*   **Fase 6: Desarrollo del "Centro de Mando IA"**

*(Estas fases se detallarán una vez completadas las fases 1-3).*
