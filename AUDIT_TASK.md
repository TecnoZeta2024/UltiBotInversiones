# Plan de Acción: Auditoría y Transición a Producción de UltiBotInversiones

## Objetivo:
Transformar UltiBotInversiones de un MVP a un producto de producción robusto, seguro y funcional, abordando los problemas identificados en el `AUDIT_REPORT.md` y asegurando una interacción perfecta entre todos los componentes.

## Leyenda de Estado:
- ⬜️ Pendiente
- 🚧 En Progreso
- ✅ Completado
- ❌ Bloqueado
- ⚠️ Requiere Atención

---

## Fase 1: Resolución de Problemas Críticos Fundamentales

Esta fase se enfoca en corregir las deficiencias arquitectónicas y de seguridad más graves que impiden que el sistema sea apto para producción.

-   ⬜️ **Tarea 1.1: Refactorización de la UI para ser un Cliente Puro**
    *   **Descripción:** Eliminar toda inicialización de servicios de backend, conexiones a bases de datos y manejo de credenciales sensibles de la aplicación de UI. La UI debe interactuar con el backend exclusivamente a través de `APIClient` y servicios UI-específicos.
    *   **Impacto:** Seguridad, desacoplamiento, escalabilidad.
    *   **Ubicación:** `src/ultibot_ui/main.py`, `src/ultibot_ui/widgets/*`, `src/ultibot_ui/windows/*`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 1.1.1: Eliminar `PersistenceService`, `CredentialService`, `MarketDataService`, `ConfigService` y otras inicializaciones de backend de `src/ultibot_ui/main.py`.
        *   ⬜️ Subtarea 1.1.2: Eliminar conexiones directas a la base de datos y manejo de credenciales (ej. `CREDENTIAL_ENCRYPTION_KEY`, claves de Binance) de `src/ultibot_ui/main.py`.
        *   ⬜️ Subtarea 1.1.3: Modificar `ChartWidget`, `NotificationWidget`, `PortfolioWidget`, `DashboardView`, `MainWindow` y cualquier otro componente de UI para que no instancien ni reciban directamente instancias de servicios de backend.
        *   ⬜️ Subtarea 1.1.4: Asegurar que todos los datos requeridos por la UI se obtengan a través de `src/ultibot_ui/services/api_client.py` o servicios UI-específicos que lo utilicen.

-   ⬜️ **Tarea 1.2: Implementación Completa de `StrategyService` en el Backend**
    *   **Descripción:** Desarrollar la lógica de backend para la creación, gestión, recuperación y aplicación de estrategias de trading.
    *   **Impacto:** Habilita la funcionalidad central de estrategias.
    *   **Ubicación:** `src/ultibot_backend/services/strategy_service.py`, `src/ultibot_backend/adapters/persistence_service.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 1.2.1: Implementar métodos CRUD (Crear, Leer, Actualizar, Eliminar) para `TradingStrategyConfig` en `src/ultibot_backend/services/strategy_service.py`.
        *   ⬜️ Subtarea 1.2.2: Definir el esquema de almacenamiento para las estrategias (tabla dedicada o extensión de `UserConfiguration` con JSONB) y actualizar `PersistenceService` en consecuencia.
        *   ⬜️ Subtarea 1.2.3: Integrar `StrategyService` con `AIOrchestratorService` para proporcionar contexto de estrategia al LLM.

-   ⬜️ **Tarea 1.3: Completar Métodos Faltantes en `APIClient` de la UI**
    *   **Descripción:** Añadir los métodos necesarios en `src/ultibot_ui/services/api_client.py` para que la UI pueda obtener todos los datos requeridos del backend.
    *   **Impacto:** Habilita la funcionalidad de visualización de datos en la UI.
    *   **Ubicación:** `src/ultibot_ui/services/api_client.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 1.3.1: Implementar `get_market_historical_data` para obtener datos de velas (klines).
        *   ⬜️ Subtarea 1.3.2: Implementar `get_tickers_data` para obtener datos de tickers actuales.
        *   ⬜️ Subtarea 1.3.3: Implementar `get_portfolio_summary` para obtener un resumen del portafolio.
        *   ⬜️ Subtarea 1.3.4: Implementar `get_notification_history` para obtener el historial de notificaciones.
        *   ⬜️ Subtarea 1.3.5: Asegurar que los endpoints correspondientes existan y sean funcionales en el backend.

-   ⬜️ **Tarea 1.4: Implementación de la Funcionalidad de Visualización de Estrategias en la UI**
    *   **Descripción:** Reemplazar el placeholder de la sección "Strategies" en la UI con componentes funcionales para listar y mostrar detalles de las estrategias de trading.
    *   **Impacto:** Permite a los usuarios ver e interactuar con sus estrategias.
    *   **Ubicación:** `src/ultibot_ui/windows/main_window.py`, nuevos archivos de vista/widgets.
    *   **Subtareas:**
        *   ⬜️ Subtarea 1.4.1: Diseñar e implementar una nueva vista (ej. `StrategiesView`) y widgets asociados para mostrar configuraciones de estrategias.
        *   ⬜️ Subtarea 1.4.2: La nueva vista debe usar `UIConfigService` (o un nuevo `UIStrategyService`) para obtener datos de estrategias a través de `APIClient.get_user_configuration()` o un nuevo método dedicado.
        *   ⬜️ Subtarea 1.4.3: Actualizar `MainWindow` para usar la nueva `StrategiesView`.

-   ⬜️ **Tarea 1.5: Eliminación de `FIXED_USER_ID` y Implementación de Autenticación de Usuario**
    *   **Descripción:** Eliminar el `FIXED_USER_ID` hardcodeado y establecer un sistema de autenticación y autorización robusto para soportar múltiples usuarios.
    *   **Impacto:** Seguridad, multi-usuario, escalabilidad.
    *   **Ubicación:** Múltiples archivos de backend (`main.py`, `app_config.py`, routers, servicios), `src/ultibot_backend/services/trading_engine_service.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 1.5.1: Implementar un sistema de autenticación y autorización (ej. basado en JWT) en el backend.
        *   ⬜️ Subtarea 1.5.2: Eliminar todas las instancias de `FIXED_USER_ID` hardcodeado.
        *   ⬜️ Subtarea 1.5.3: Modificar todos los servicios y endpoints de API para operar en el contexto del usuario autenticado, pasando el `user_id` a través del sistema.

-   ⬜️ **Tarea 1.6: Corrección de la Inicialización de Dependencias en `CredentialService`**
    *   **Descripción:** Modificar `CredentialService` para que reciba sus dependencias (`BinanceAdapter`, `SupabasePersistenceService`) a través de su constructor, en lugar de inicializarlas internamente.
    *   **Impacto:** Consistencia, gestión de recursos compartidos.
    *   **Ubicación:** `src/ultibot_backend/services/credential_service.py`, `src/ultibot_backend/main.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 1.6.1: Actualizar el constructor de `CredentialService` para aceptar instancias de `BinanceAdapter` y `SupabasePersistenceService`.
        *   ⬜️ Subtarea 1.6.2: Modificar `main.py` y cualquier otro punto de instanciación de `CredentialService` para inyectar estas dependencias.

-   ⬜️ **Tarea 1.7: Mejora de la Lógica de Salida de Operaciones Reales (OCO Fallido)**
    *   **Descripción:** Mejorar la lógica de `TradingEngineService` para asegurar que las posiciones de trading real se cierren automáticamente si una orden OCO falla y los niveles de Stop Loss/Take Profit son alcanzados.
    *   **Impacto:** Prevención de pérdidas no gestionadas en trading real.
    *   **Ubicación:** `src/ultibot_backend/services/trading_engine_service.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 1.7.1: Mejorar `monitor_and_manage_real_trade_exit` para ejecutar órdenes de mercado (venta/compra) a través de `OrderExecutionService` si un trade real no gestionado por OCO alcanza su TSL o TP.
        *   ⬜️ Subtarea 1.7.2: Implementar reportes de errores robustos y alertas si la colocación de OCO falla.

-   ⬜️ **Tarea 1.8: Registro del Router `trading.py` en el Backend**
    *   **Descripción:** Registrar el router de API definido en `src/ultibot_backend/api/v1/endpoints/trading.py` en `src/ultibot_backend/main.py`.
    *   **Impacto:** Habilita el endpoint crucial para confirmar e iniciar trades reales.
    *   **Ubicación:** `src/ultibot_backend/main.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 1.8.1: Añadir `app.include_router(trading.router, prefix="/api/v1", tags=["trading"])` a `src/ultibot_backend/main.py`.

-   ⬜️ **Tarea 1.9: Implementación de Almacenamiento Persistente para Datos de Mercado**
    *   **Descripción:** Implementar el almacenamiento persistente de datos de mercado granulares (klines, tickers, datos de stream de WebSocket) para permitir backtesting y entrenamiento de modelos de IA.
    *   **Impacto:** Habilita capacidades analíticas avanzadas y mejora la eficiencia.
    *   **Ubicación:** `src/ultibot_backend/adapters/persistence_service.py`, nuevos esquemas de base de datos.
    *   **Subtareas:**
        *   ⬜️ Subtarea 1.9.1: Diseñar un esquema de base de datos para almacenar datos de klines y tickers.
        *   ⬜️ Subtarea 1.9.2: Implementar métodos en `PersistenceService` para guardar y recuperar estos datos.
        *   ⬜️ Subtarea 1.9.3: Integrar la lógica de guardado en `MarketDataService` para persistir los datos recibidos.

---

## Fase 2: Optimización y Mejora de la Robustez

Esta fase se centra en mejorar la eficiencia, la claridad del código y la resiliencia del sistema.

-   ⬜️ **Tarea 2.1: Corrección de la Inicialización de Dependencias en Routers de API**
    *   **Descripción:** Refactorizar los routers de API (`binance_status.py`, `notifications.py`) para usar las instancias de servicio inicializadas globalmente en `main.py` a través de `FastAPI's Depends`.
    *   **Impacto:** Eficiencia, consistencia de estado.
    *   **Ubicación:** `src/ultibot_backend/api/v1/endpoints/binance_status.py`, `src/ultibot_backend/api/v1/endpoints/notifications.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 2.1.1: Modificar `binance_status.py` para inyectar `MarketDataService` y `CredentialService` usando `Depends`.
        *   ⬜️ Subtarea 2.1.2: Modificar `notifications.py` para inyectar `NotificationService` usando `Depends`.

-   ⬜️ **Tarea 2.2: Refactorización de Lógica de Negocio en el Router de Oportunidades**
    *   **Descripción:** Mover la lógica de negocio significativa del endpoint `get_real_trading_candidates` en `src/ultibot_backend/api/v1/endpoints/opportunities.py` a un servicio relevante (ej. `TradingEngineService` o `AIOrchestratorService`).
    *   **Impacto:** Mejora la modularidad, testabilidad y mantenibilidad.
    *   **Ubicación:** `src/ultibot_backend/api/v1/endpoints/opportunities.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 2.2.1: Identificar y extraer la lógica de negocio del router.
        *   ⬜️ Subtarea 2.2.2: Crear o extender un método en `TradingEngineService` o `AIOrchestratorService` para contener esta lógica.
        *   ⬜️ Subtarea 2.2.3: Modificar el router para delegar la ejecución a este nuevo método de servicio.

-   ⬜️ **Tarea 2.3: Persistencia de Activos de Paper Trading**
    *   **Descripción:** Implementar un mecanismo para guardar y cargar las tenencias de activos de paper trading (`PortfolioService.paper_trading_assets`) en la base de datos.
    *   **Impacto:** Permite simulaciones de paper trading a largo plazo y análisis.
    *   **Ubicación:** `src/ultibot_backend/services/portfolio_service.py`, `src/ultibot_backend/services/order_execution_service.py`, `src/ultibot_backend/adapters/persistence_service.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 2.3.1: Diseñar un esquema para almacenar las tenencias de activos de paper trading (nueva tabla o extensión de `UserConfiguration`).
        *   ⬜️ Subtarea 2.3.2: Actualizar `PortfolioService` para cargar y guardar estas tenencias a través de `PersistenceService`.

-   ⬜️ **Tarea 2.4: Automatización del Mapeo de Datos en `PersistenceService`**
    *   **Descripción:** Utilizar las características de aliasing de Pydantic o una función de utilidad para manejar automáticamente la conversión de nombres de columnas snake_case de la base de datos a nombres de campos camelCase/PascalCase de los modelos Pydantic.
    *   **Impacto:** Reduce errores, verbosidad y mejora la mantenibilidad.
    *   **Ubicación:** `src/ultibot_backend/adapters/persistence_service.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 2.4.1: Investigar y aplicar la configuración de Pydantic (`AliasGenerator` o `model_config = {"populate_by_name": True}`) para el mapeo automático.
        *   ⬜️ Subtarea 2.4.2: Eliminar el mapeo manual de campos en los métodos de `SupabasePersistenceService`.

-   ⬜️ **Tarea 2.5: Clarificación y Simplificación de la Lógica de `MobulaAdapter`**
    *   **Descripción:** Clarificar los endpoints exactos de la API de Mobula y las estructuras de respuesta esperadas para simplificar la lógica de obtención y parsing de datos de mercado.
    *   **Impacto:** Mejora la robustez y reduce la fragilidad.
    *   **Ubicación:** `src/ultibot_backend/adapters/mobula_adapter.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 2.5.1: Documentar los endpoints de Mobula y las estructuras de respuesta.
        *   ⬜️ Subtarea 2.5.2: Simplificar la lógica de `get_market_data` basándose en el comportamiento documentado de la API.

-   ⬜️ **Tarea 2.6: Mejora de la Robustez del Parsing de Salida del LLM**
    *   **Descripción:** Reforzar el parsing de la salida del LLM para asegurar un formato estructurado (JSON) y reducir la dependencia de expresiones regulares frágiles.
    *   **Impacto:** Mejora la fiabilidad del análisis de oportunidades.
    *   **Ubicación:** `src/ultibot_backend/services/ai_orchestrator_service.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 2.6.1: Refinar el prompt del LLM para forzar una salida JSON estructurada.
        *   ⬜️ Subtarea 2.6.2: Utilizar los parsers de salida estructurados de LangChain si es posible.
        *   ⬜️ Subtarea 2.6.3: Mejorar el manejo de errores si no se puede obtener una salida estructurada.

---

## Fase 3: Ajustes Finales y Preparación para Producción

Esta fase aborda problemas relevantes que, aunque no son críticos, son importantes para la calidad, seguridad y mantenibilidad a largo plazo del proyecto.

-   ⬜️ **Tarea 3.1: Estandarización de Rutas de Endpoint API**
    *   **Descripción:** Asegurar que el router de oportunidades (`opportunities.router`) se registre consistentemente en `main.py` con el prefijo `/api/v1`, o ajustar `APIClient` en la UI si la ruta raíz es intencional.
    *   **Impacto:** Resuelve errores 404 en llamadas API.
    *   **Ubicación:** `src/ultibot_backend/main.py`, `src/ultibot_ui/services/api_client.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 3.1.1: Modificar `src/ultibot_backend/main.py` para incluir `opportunities.router` con `prefix="/api/v1"`.
        *   ⬜️ Subtarea 3.1.2: Verificar que `APIClient` en la UI utiliza la ruta correcta.

-   ⬜️ **Tarea 3.2: Implementación de Autorización Granular para Endpoints API**
    *   **Descripción:** Una vez implementada la autenticación de usuario (Tarea 1.5), añadir mecanismos de autorización para asegurar que los usuarios solo puedan acceder o modificar sus propios recursos.
    *   **Impacto:** Seguridad.
    *   **Ubicación:** Diseño general de la API de backend, endpoints y servicios.
    *   **Subtareas:**
        *   ⬜️ Subtarea 3.2.1: Implementar verificaciones de autorización basadas en recursos en los endpoints de API y servicios.
        *   ⬜️ Subtarea 3.2.2: Asegurar que el `user_id` del contexto de autenticación se utilice para filtrar las consultas a la base de datos.

-   ⬜️ **Tarea 3.3: Separación de Métodos de Ayuda de Prueba en `PersistenceService`**
    *   **Descripción:** Mover los métodos de ayuda de prueba (`execute_test_...`, `fetchrow_test_...`) de `SupabasePersistenceService` a un módulo de utilidad de prueba separado o a una subclase específica para pruebas.
    *   **Impacto:** Limpia el código de producción y mejora la organización.
    *   **Ubicación:** `src/ultibot_backend/adapters/persistence_service.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 3.3.1: Identificar todos los métodos de prueba en `PersistenceService`.
        *   ⬜️ Subtarea 3.3.2: Crear un nuevo módulo (ej. `tests/utils/persistence_test_helpers.py`) y mover los métodos allí.
        *   ⬜️ Subtarea 3.3.3: Actualizar las pruebas para importar los métodos desde la nueva ubicación.

-   ⬜️ **Tarea 3.4: Sincronización del Modo de Trading UI-Backend**
    *   **Descripción:** Clarificar y asegurar que el `TradingModeService` de la UI sincronice su estado con el flag `UserConfiguration.paperTradingActive` del backend.
    *   **Impacto:** Consistencia en el comportamiento de trading.
    *   **Ubicación:** `src/ultibot_ui/services/trading_mode_service.py`, `src/ultibot_backend/shared/data_types.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 3.4.1: Asegurar que `TradingModeService` llame a `APIClient` para actualizar `UserConfiguration.paperTradingActive` en el backend cuando el modo se cambia en la UI.

-   ⬜️ **Tarea 3.5: Eliminación de Credenciales por Defecto de Supabase en `app_config.py`**
    *   **Descripción:** Eliminar los valores de marcador de posición predeterminados para las credenciales sensibles de Supabase en `src/ultibot_backend/app_config.py`. En su lugar, generar un error de configuración si no se encuentran en el entorno.
    *   **Impacto:** Seguridad, configuración robusta.
    *   **Ubicación:** `src/ultibot_backend/app_config.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 3.5.1: Eliminar los valores predeterminados para `SUPABASE_URL`, `SUPABASE_ANON_KEY`, etc.
        *   ⬜️ Subtarea 3.5.2: Implementar una verificación de inicio que genere un error si estas variables de entorno no están configuradas.

-   ⬜️ **Tarea 3.6: Estandarización de la Carga de `CREDENTIAL_ENCRYPTION_KEY`**
    *   **Descripción:** Asegurar que `pydantic-settings` cargue de forma fiable `CREDENTIAL_ENCRYPTION_KEY` y eliminar la lógica de carga manual en `src/ultibot_backend/main.py` si es posible.
    *   **Impacto:** Consistencia, fiabilidad de la configuración.
    *   **Ubicación:** `src/ultibot_backend/main.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 3.6.1: Verificar la configuración de `pydantic-settings` para `CREDENTIAL_ENCRYPTION_KEY`.
        *   ⬜️ Subtarea 3.6.2: Eliminar la carga manual si `pydantic-settings` puede manejarla. Documentar la razón si no es posible.

-   ⬜️ **Tarea 3.7: Mejora del Manejo de Errores de WebSocket en `BinanceAdapter`**
    *   **Descripción:** Implementar un mecanismo más robusto de manejo de errores y verificación de salud para las conexiones WebSocket en `BinanceAdapter`, permitiendo que los servicios de nivel superior reaccionen a fallos persistentes.
    *   **Impacto:** Resiliencia del sistema a fallos de WebSocket, datos en tiempo real fiables.
    *   **Ubicación:** `src/ultibot_backend/adapters/binance_adapter.py`.
    *   **Subtareas:**
        *   ⬜️ Subtarea 3.7.1: Implementar un mecanismo para notificar a `MarketDataService` (o consumidores) sobre fallos persistentes de WebSocket.
        *   ⬜️ Subtarea 3.7.2: Permitir que los servicios de nivel superior intenten volver a suscribirse o informen al usuario.

---

## Notas Adicionales:
-   *No utilizar MOCKS.*
-   *Priorizar la estabilidad y la correcta interacción con el backend.*
-   *El objetivo es un despliegue "como un reloj suizo atómico".*
-   *Cada tarea debe ser verificada con pruebas unitarias, de integración y/o manuales según corresponda.*
