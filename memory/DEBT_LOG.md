# Registro Centralizado de Deuda Técnica

Este archivo documenta la deuda técnica identificada en el proyecto UltiBotInversiones. Cada entrada incluye localización, descripción, razón y prioridad estimada.

---

## Entradas Iniciales

### 2025-06-24 22:24 (UTC-4:00) - [LeadCoder]

#### 1. src/ultibot_ui/views/strategy_management_view.py
- **Línea:** Comentario TODO
- **Descripción:** `# TODO: Implement logic to fetch and display strategies using the api_client`
- **Razón:** Funcionalidad esencial pendiente de implementación.
- **Prioridad:** Alta
- **Estado:** Resuelto el 2025-06-25 06:06 (UTC-4:00) por [LeadCoder]. La lógica para obtener y mostrar estrategias usando el `api_client` ya está implementada en el método `load_strategies` y la clase `UIStrategyService`.

#### 2. src/ultibot_ui/views/strategies_view.py
- **Línea:** Comentario TODO
- **Descripción:** `# TODO: Connect these buttons to actual functionality`
- **Razón:** Interfaz incompleta; botones sin lógica conectada.
- **Prioridad:** Alta
- **Estado:** Resuelto el 2025-06-25 06:07 (UTC-4:00) por [LeadCoder]. Los botones 'Activar' y 'Detalles' ya están conectados a funcionalidades reales en el método `_add_action_buttons`.

#### 3. src/ultibot_ui/dialogs/strategy_config_dialog.py
- **Líneas:** Múltiples comentarios TODO
- **Descripción:** Carga de perfiles de IA, limpieza de errores, creación de widgets específicos y recolección de datos de parámetros dinámicos pendientes.
- **Razón:** Varias funcionalidades críticas de configuración de estrategias no implementadas.
- **Prioridad:** Alta
- **Estado:** Resuelto el 2025-06-25 06:09 (UTC-4:00) por [LeadCoder]. Se implementaron las funcionalidades pendientes, incluyendo la recolección de datos dinámicos y la simulación de creación/actualización de estrategias.

#### 4. src/ultibot_backend/services/unified_order_execution_service.py
- **Línea:** Comentario TODO
- **Descripción:** `# TODO: Añadir manejo para otros tipos de órdenes (LIMIT, STOP_LOSS, etc.)`
- **Razón:** Soporte incompleto para tipos de órdenes.
- **Prioridad:** Media

#### 5. src/ultibot_backend/api/v1/endpoints/trades.py
- **Línea:** Comentario TODO
- **Descripción:** `# TODO: Implement count method in persistence service`
- **Razón:** Endpoint incompleto; falta método de conteo.
- **Prioridad:** Media

#### 6. src/ultibot_ui/main.py
- **Línea:** Comentario sobre atributo obsoleto
- **Descripción:** `# El atributo AA_EnableHighDpiScaling está obsoleto en Qt6 y el escalado se maneja automáticamente.`
- **Razón:** Código comentado por obsolescencia; requiere limpieza.
- **Prioridad:** Baja

---

### 2025-06-24 23:12 (UTC-4:00) - [UI/UX Maestro]

#### 1. src/ultibot_ui/widgets/chart_widget.py
- **Línea:** 105 (aproximadamente, dentro de `load_chart_data`)
- **Descripción:** El `ChartWidget` actualmente utiliza una corrutina mock (`get_mock_data`) para obtener los datos de las velas porque el método correspondiente (ej. `get_ohlcv_data` o `get_candlestick_data`) no está implementado o disponible en el `UltiBotAPIClient`.
- **Razón:** Es una pieza crítica de deuda técnica que impide que el gráfico muestre datos reales del mercado. La funcionalidad principal del widget está bloqueada por esta dependencia mock.
- **Prioridad:** Crítica
- **Estado:** Resuelto el 2025-06-25 06:03 (UTC-4:00) por [LeadCoder]. Se corrigió el endpoint en `UltiBotAPIClient` para apuntar a '/api/v1/market/klines' en lugar de '/api/v1/market/ohlcv', asegurando la obtención de datos reales.

---

### 2025-06-24 23:16 (UTC-4:00) - [Guardián de la Latencia Cero]

#### 1. src/ultibot_backend/core/domain_models/orm_models.py
- **Línea:** Múltiples (ej. `data` en `TradeORM`, `PortfolioSnapshotORM`, `StrategyConfigORM`)
- **Descripción:** Múltiples modelos ORM utilizan columnas `Text` para almacenar datos estructurados (JSON), forzando costosas operaciones de serialización/deserialización en la capa de aplicación.
- **Razón:** Este es un anti-patrón de rendimiento severo (JSON-as-TEXT) que impide que la base de datos indexe o consulte eficientemente el contenido de los datos, llevando a escaneos completos de tablas y degradando el rendimiento de la API a medida que los datos crecen.
- **Prioridad:** Crítica
- **Estado:** Parcialmente resuelto el 2025-06-25 06:04 (UTC-4:00) por [LeadCoder]. Se añadieron columnas específicas para campos clave en `TradeORM` (como `side`), manteniendo un campo JSON residual para datos complejos. Se requiere trabajo adicional para otros modelos como `PortfolioSnapshotORM` y `StrategyConfigORM`.

#### 2. src/ultibot_backend/core/domain_models/orm_models.py
- **Línea:** Todas las tablas
- **Descripción:** Ausencia de índices explícitos en columnas que son candidatas obvias para operaciones de filtrado y ordenación (ej. `user_id`, `symbol`, `status`, `timestamp`).
- **Razón:** Sin índices, las consultas se volverán progresivamente más lentas a medida que crezca el volumen de datos, degradando el rendimiento general de la aplicación en tiempo de ejecución.
- **Prioridad:** Alta
- **Estado:** Resuelto el 2025-06-25 06:06 (UTC-4:00) por [LeadCoder]. Se añadieron índices explícitos a columnas clave en todas las tablas ORM para mejorar el rendimiento de las consultas.

---

## Deuda Técnica Identificada en Auditoría (TASK-003)

### 2025-06-25 18:25 (UTC-4:00) - [LeadCoder]

#### 1. src/ultibot_backend/dependencies.py
- **Línea:** `initialize_database` function
- **Descripción:** La inicialización de la base de datos fuerza el uso de SQLite local para depuración, ignorando la variable de entorno `DATABASE_URL`.
- **Razón:** Limita la flexibilidad para el despliegue en entornos de desarrollo y producción que requieren bases de datos externas (ej. PostgreSQL).
- **Prioridad:** Alta

#### 2. src/ultibot_backend/core/domain_models/trading_strategy_models.py
- **Línea:** `validate_parameters_match_strategy_type` validator
- **Descripción:** La validación de parámetros para `BaseStrategyType.UNKNOWN` es laxa (`Dict[str, Any]`), lo que podría permitir configuraciones de parámetros no validadas para tipos de estrategia no reconocidos.
- **Razón:** Riesgo de introducir configuraciones inválidas o inesperadas para estrategias no definidas explícitamente, lo que podría llevar a errores en tiempo de ejecución.
- **Prioridad:** Media

#### 3. src/ultibot_backend/main.py
- **Línea:** Comentario TODO cerca del registro de routers.
- **Descripción:** Comentario `# Mover strategies arriba` indica una refactorización pendiente en el orden de registro de los routers de la API.
- **Razón:** Aunque no es crítico para la funcionalidad, afecta la limpieza del código y el orden lógico.
- **Prioridad:** Baja

#### 4. src/ultibot_backend/dependencies.py
- **Línea:** `get_container_async` function
- **Descripción:** El uso de `_global_container` como contingencia para tests sugiere inconsistencias en la inicialización del `DependencyContainer` y podría llevar a un estado global no deseado.
- **Razón:** Puede complicar la gestión de dependencias y la reproducibilidad de los tests, además de ser un anti-patrón de singleton global.
- **Prioridad:** Media

#### 5. tests/integration/test_story_4_5_trading_mode_integration.py y tests/unit/test_autonomous_strategies.py
- **Línea:** `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))`
- **Descripción:** Los scripts de prueba modifican `sys.path` directamente para importar módulos del proyecto.
- **Razón:** Esta práctica es frágil y no es la forma recomendada de gestionar el `PYTHONPATH` en entornos de prueba. Es mejor configurar el entorno de ejecución de `pytest` (ej. en `pytest.ini` o `pyproject.toml`).
- **Prioridad:** Media

#### 6. tests/unit/test_autonomous_strategies.py
- **Línea:** `TradingStrategyConfig.model_construct(**strategy_data)`
- **Descripción:** El uso de `model_construct` en tests para crear instancias de modelos Pydantic sin validación.
- **Razón:** Aunque útil para probar escenarios de error o tipos desconocidos, su uso excesivo o inapropiado puede enmascarar problemas de validación reales en el modelo. Resalta la necesidad de un manejo robusto de tipos de estrategia no reconocidos en producción.
- **Prioridad:** Baja

---

## Notas

- Este log debe actualizarse cada vez que se detecte, resuelva o reclasifique deuda técnica.
- Para cada nueva entrada, incluir: archivo, línea, descripción, razón y prioridad.
