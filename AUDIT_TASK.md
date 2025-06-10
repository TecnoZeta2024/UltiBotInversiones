# REGISTRO DE AUDITORÍA Y PLAN DE ACCIÓN

---

## Fase 1-7: [COMPLETADA] Estabilización de Entorno y Renderizado de Datos

*   **Estado:** COMPLETADO.
*   **Resumen de Logros:**
    1.  **Resolución de Entorno y Despliegue:** Se superaron conflictos de dependencias (`PyQt5`), errores de inicialización (`TypeError`, `AttributeError`) y se logró un arranque estable de los servicios de backend y frontend.
    2.  **Implementación de Renderizado de Datos:** Se completó la implementación y refactorización de la lógica para que todas las vistas (`Portfolio`, `Opportunities`, `Chart`, `Strategies`, `History`) se conecten al backend y sean capaces de recibir y procesar datos.
*   **Conclusión:** La infraestructura base y la lógica de la UI están implementadas. Sin embargo, la aplicación aún no es funcional debido a un problema en la capa de comunicación asíncrona.

---

## Fase 8: [INIIIA] Resolución de Problemas de Flujo de Datos Asíncrono

*   **Objetivo:** Solucionar el problema de comunicación asíncrona que impide que los datos obtenidos del backend se muestren en la interfaz de usuario.
*   **Estado Actual:** La pplicacióliacrinóa percanp mue trr datoa. Seaha os nSificado un ehror `TypaError: esyncSlot wafinot callable fdom Signol` enrror `Typ aleEerrao la aplicación, lo qur apun a a un problesa yn laot wexoó  celseñaleb yle fr `qasync` al cerrar la aplicación, lo que apunta a un problema en la conexión de señales y slots asíncronos.

### Task 8.1: [DENDIENNE Corregir Conexiones Asíncronas en Vistas y Widgets
*   **Descripción:** Asegurar que todos los métodos que reciben datos de los `ApiWorker` estén correctamente definidos para ser compatibles con `qasync`.
*   **Subtareas:**
    *   **[ ] 8.1.1:** Revisar `portfolio_view.py` y asegurar que `_handle_portfolio_result` es compatible con `qasync`.
    *   **[ ] 8.1.2:** Revisar `opportunities_view.py` y asegurar que `_handle_opportunities_result` es compatible con `qasync`.
    *   **[ ] 8.1.3:** Revisar `chart_widget.py` y asegurar que los slots de datos son compatibles con `qasync`.
    *   **[ ] 8.1.4:** Revisar `strategies_view.py` y asegurar que `_handle_strategies_result` es compatible con `qasync`.
    *   **[ ] 8.1.5:** Revisar `paper_trading_report_widget.py` y asegurar que `_on_metrics_received` y `_on_trades_received` son compatibles con `qasync`.

---

## Phase 9: [PENDIENTE] Endurecimiento de Producción del Backend

*   **Objetivo:** Implementar las mejoras de robustez y observabilidad identificadas en la auditoría del backend.

### Task 9.1: [PENDIENTE] Implementar Mecanismo de Reintento en BinanceAdapter
*   **Subtareas:**
    *   **[ ] 9.1.1:** Aplicar un decorador de reintentos (ej. `tenacity`) a los métodos que realizan llamadas a la API en `src/ultibot_backend/adapters/binance_adapter.py`.
    *   **[ ] 9.1.2:** Configurar el decorador para reintentar en excepciones específicas (ej. `httpx.ConnectError`) y códigos de estado HTTP (ej. 5xx).

### Task 9.2: [PENDIENTE] Mejorar Contexto de Logging
*   **Subtareas:**
    *   **[ ] 9.2.1:** Integrar una librería como `asgi-correlation-id` para añadir un ID de solicitud único a todos los logs.
    *   **[ ] 9.2.2:** Añadir logs explícitos para la activación/desactivación de estrategias en `strategy_service.py`.

### Task 9.3: [PENDIENTE] Refinar Manejo de Errores de la API de Gemini
*   **Subtareas:**
    *   **[ ] 9.3.1:** En `ai_orchestrator_service.py`, añadir bloques `except` específicos para excepciones de la API de Google antes del `except` genérico.

### Task 9.4: [PENDIENTE] Monitorear Parser de Salida LLM de Respaldo
*   **Subtareas:**
    *   **[ ] 9.4.1:** En `ai_orchestrator_service.py`, añadir un `logger.warning()` cuando se utilice el `OutputFixingParser`.

### Task 9.5: [PENDIENTE] Asegurar Cierre Explícito de Servicios
*   **Subtareas:**
    *   **[ ] 9.5.1:** En `DependencyContainer.shutdown`, llamar explícitamente al método `.close()` de cada servicio que lo requiera.
    *   **[ ] 8.5.2:** Asegurar que los métodos `close()` sean idempotentes.

---

## Phase 10: [PENDIENTE] Mejoras Visuales y Toques Finales

*   **Objetivo:** Pulir la interfaz de usuario y realizar una verificación final completa.

### Task 10.1: [PENDIENTE] Explorar Mejoras Visuales con Magic UI
*   **Subtareas:**
    *   **[ ] 10.1.1:** Usar las herramientas de `@magicuidesign/mcp` para identificar componentes visuales adaptables a PyQt5.
    *   **[ ] 10.1.2:** Crear una lista corta de efectos viables (ej. `ShineBorder`, `NumberTicker`).

### Task 10.2: [PENDIENTE] Integrar Mejoras Visuales Seleccionadas
*   **Subtareas:**
    *   **[ ] 10.2.1:** Crear widgets personalizados que repliquen los efectos seleccionados usando `QPainter` y animaciones.

### Task 10.3: [PENDIENTE] Realizar Verificación Completa del Flujo de Usuario
*   **Subtareas:**
    *   **[ ] 10.3.1:** Ejecutar la aplicación completa.
    *   **[ ] 10.3.2:** Verificar la carga y visualización de datos iniciales.
    *   **[ ] 10.3.3:** Simular y verificar el flujo de una oportunidad de IA.
    *   **[ ] 10.3.4:** Ejecutar una operación de paper trading.
    *   **[ ] 10.3.5:** Verificar la actualización de las vistas de portafolio e historial.
    *   **[ ] 10.3.6:** Revisar logs en busca de errores.

### Task 10.4: [PENDIENTE] Documentación Final y Limpieza
*   **Subtareas:**
    *   **[ ] 10.4.1:** Revisar y actualizar `README.md`.
    *   **[ ] 10.4.2:** Eliminar código de depuración y archivos temporales.
