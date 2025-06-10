# REGISTRO DE AUDITORÍA Y PLAN DE ACCIÓN

---

## Fase 1-7: [COMPLETADA] Estabilización de Entorno y Renderizado de Datos

*   **Estado:** COMPLETADO.
*   **Resumen de Logros:**
    1.  **Resolución de Entorno y Despliegue:** Se superaron conflictos de dependencias (`PyQt5`), errores de inicialización (`TypeError`, `AttributeError`) y se logró un arranque estable de los servicios de backend y frontend.
    2.  **Implementación de Renderizado de Datos:** Se completó la implementación y refactorización de la lógica para que todas las vistas (`Portfolio`, `Opportunities`, `Chart`, `Strategies`, `History`) se conecten al backend y sean capaces de recibir y procesar datos.
*   **Conclusión:** La infraestructura base y la lógica de la UI están implementadas funcionalmente.

---

## Fase 8-10: [COMPLETADA] Estabilización Final y Corrección de Flujos

*   **Estado:** COMPLETADO.
*   **Resumen de Logros:**
    1.  **Resolución de Problemas Asíncronos:** Se corrigieron las conexiones asíncronas en vistas y widgets.
    2.  **Endurecimiento del Backend:** Se implementaron mecanismos de reintento y mejor manejo de errores.
    3.  **Verificación Completa:** El sistema funciona de extremo a extremo sin crashes críticos.
*   **Conclusión:** El sistema base está estable y listo para nuevas funcionalidades avanzadas.

---

## Fase 11: [NUEVA] Implementación de Sistema de Configuración de Filtros de Mercado

*   **Objetivo:** Permitir al usuario configurar criterios de búsqueda (% incremento 24h, volumen, market cap, etc.) antes de consultar APIs de Binance/Mobula.
*   **Prioridad:** ALTA - Requisito crítico para personalización de estrategias.

### Task 11.1: [PENDIENTE] Extensión de Modelos de Configuración Backend
*   **Descripción:** Crear nuevos modelos de dominio para soportar configuración de filtros de mercado.
*   **Subtareas:**
    *   **[ ] 11.1.1:** Crear modelo `MarketScanConfiguration` en `src/ultibot_backend/core/domain_models/user_configuration_models.py`:
        - `price_change_24h_min: Optional[float]` (% mínimo incremento 24h)
        - `price_change_24h_max: Optional[float]` (% máximo incremento 24h)
        - `volume_24h_min: Optional[float]` (volumen mínimo 24h)
        - `market_cap_min: Optional[float]` (market cap mínimo)
        - `market_cap_max: Optional[float]` (market cap máximo)
        - `volatility_min: Optional[float]` (volatilidad mínima)
        - `volatility_max: Optional[float]` (volatilidad máxima)
    *   **[ ] 11.1.2:** Crear modelo `AssetTradingParameters` para configuración específica por crypto:
        - `symbol: str` (símbolo del activo)
        - `max_investment_per_trade: Optional[float]` (inversión máxima por trade)
        - `custom_stop_loss: Optional[float]` (stop-loss personalizado)
        - `custom_take_profit: Optional[float]` (take-profit personalizado)
        - `min_price: Optional[float]` (precio mínimo)
        - `max_price: Optional[float]` (precio máximo)
    *   **[ ] 11.1.3:** Crear modelo `ScanPreset` para sistemas de búsqueda predefinidos:
        - `id: str` (identificador único)
        - `name: str` (nombre del preset)
        - `description: Optional[str]` (descripción)
        - `scan_config: MarketScanConfiguration` (configuración de filtros)
        - `asset_configs: List[AssetTradingParameters]` (configuraciones de activos)
    *   **[ ] 11.1.4:** Integrar nuevos modelos en `UserConfiguration`:
        - `market_scan_presets: Optional[List[ScanPreset]]`
        - `active_scan_preset_id: Optional[str]`
        - `asset_trading_parameters: Optional[List[AssetTradingParameters]]`

### Task 11.2: [PENDIENTE] Backend - Servicios y Endpoints de Configuración
*   **Descripción:** Implementar lógica de negocio y endpoints para gestionar configuraciones de filtros.
*   **Subtareas:**
    *   **[ ] 11.2.1:** Crear `MarketScanService` en `src/ultibot_backend/services/market_scan_service.py`:
        - `apply_filters(scan_config: MarketScanConfiguration, raw_data: List[Dict]) -> List[Dict]`
        - `get_scan_presets(user_id: str) -> List[ScanPreset]`
        - `save_scan_preset(user_id: str, preset: ScanPreset) -> ScanPreset`
        - `delete_scan_preset(user_id: str, preset_id: str) -> bool`
    *   **[ ] 11.2.2:** Crear endpoints en `src/ultibot_backend/api/v1/endpoints/market_scan.py`:
        - `GET /api/v1/market-scan/presets` (obtener presets del usuario)
        - `POST /api/v1/market-scan/presets` (crear nuevo preset)
        - `PUT /api/v1/market-scan/presets/{preset_id}` (actualizar preset)
        - `DELETE /api/v1/market-scan/presets/{preset_id}` (eliminar preset)
        - `POST /api/v1/market-scan/apply-filters` (aplicar filtros a datos de mercado)
    *   **[ ] 11.2.3:** Crear endpoints en `src/ultibot_backend/api/v1/endpoints/asset_config.py`:
        - `GET /api/v1/asset-configs` (obtener configuraciones de activos)
        - `POST /api/v1/asset-configs` (crear/actualizar configuración de activo)
        - `DELETE /api/v1/asset-configs/{symbol}` (eliminar configuración)
    *   **[ ] 11.2.4:** Integrar filtros con `MarketDataService`:
        - Modificar `get_market_data_rest()` para aplicar filtros opcionales
        - Añadir parámetro `scan_config: Optional[MarketScanConfiguration]`

### Task 11.3: [PENDIENTE] Frontend - Panel de Configuración de Filtros
*   **Descripción:** Crear interfaz de usuario para configurar filtros de mercado y gestionar presets.
*   **Subtareas:**
    *   **[ ] 11.3.1:** Crear `MarketScanConfigDialog` en `src/ultibot_ui/dialogs/market_scan_config_dialog.py`:
        - Controles para % incremento 24h (spin boxes min/max)
        - Controles para volumen mínimo (spin box)
        - Controles para market cap range (spin boxes min/max)
        - Controles para volatilidad range (spin boxes min/max)
        - Lista de presets guardados con botones CRUD
        - Botones "Guardar Preset", "Cargar Preset", "Aplicar Filtros"
    *   **[ ] 11.3.2:** Crear `AssetConfigDialog` en `src/ultibot_ui/dialogs/asset_config_dialog.py`:
        - Tabla editable con columnas: Symbol, Max Investment, Stop Loss, Take Profit, Min Price, Max Price
        - Botones "Añadir Activo", "Eliminar Activo", "Guardar Configuración"
    *   **[ ] 11.3.3:** Añadir métodos al `UltiBotAPIClient` en `src/ultibot_ui/services/api_client.py`:
        - `get_scan_presets() -> List[Dict]`
        - `save_scan_preset(preset_data: Dict) -> Dict`
        - `delete_scan_preset(preset_id: str) -> bool`
        - `get_asset_configs() -> List[Dict]`
        - `save_asset_config(config_data: Dict) -> Dict`
        - `apply_market_filters(scan_config: Dict) -> List[Dict]`
    *   **[ ] 11.3.4:** Integrar diálogos en `MainWindow`:
        - Añadir botón "Configurar Filtros de Mercado" en barra de herramientas
        - Conectar botón con `MarketScanConfigDialog`
        - Añadir menú "Configuración de Activos" con `AssetConfigDialog`

---

## Fase 12: [NUEVA] Sistema de Configuración de Parámetros de Trading

*   **Objetivo:** Hacer configurables los umbrales de confianza (incluyendo 50% para paper trading) y parámetros específicos de trading.
*   **Prioridad:** ALTA - Requisito crítico para flexibilidad operativa.

### Task 12.1: [PENDIENTE] Configuración de Umbrales de Confianza Dinámicos
*   **Descripción:** Permitir al usuario modificar umbrales de confianza por modo de operación.
*   **Subtareas:**
    *   **[ ] 12.1.1:** Extender `ConfidenceThresholds` en `user_configuration_models.py`:
        - Añadir validación para permitir paper_trading >= 0.5 (50%)
        - Asegurar que real_trading siga siendo >= 0.95 por defecto
        - Añadir `strategy_specific_thresholds: Optional[Dict[str, ConfidenceThresholds]]`
    *   **[ ] 12.1.2:** Crear `ConfidenceConfigDialog` en `src/ultibot_ui/dialogs/confidence_config_dialog.py`:
        - Sliders para paper trading threshold (50%-95%)
        - Sliders para real trading threshold (85%-99%)
        - Configuración específica por estrategia (Scalping, Day Trading, Arbitrage)
        - Botones "Restaurar Defaults", "Guardar Configuración"
    *   **[ ] 12.1.3:** Modificar `AIOrchestratorService` para usar umbrales dinámicos:
        - Cargar umbrales desde `UserConfiguration` al analizar oportunidades
        - Aplicar umbral específico de estrategia si existe
        - Fallback a umbral global si no hay específico

### Task 12.2: [PENDIENTE] Sistema de Configuración Avanzada de Trading
*   **Descripción:** Implementar configuración granular de parámetros de trading por activo y estrategia.
*   **Subtareas:**
    *   **[ ] 12.2.1:** Crear `TradingParametersService` en `src/ultibot_backend/services/trading_parameters_service.py`:
        - `get_asset_parameters(symbol: str) -> Optional[AssetTradingParameters]`
        - `save_asset_parameters(params: AssetTradingParameters) -> bool`
        - `get_effective_stop_loss(symbol: str, strategy: str) -> float`
        - `get_effective_take_profit(symbol: str, strategy: str) -> float`
    *   **[ ] 12.2.2:** Crear endpoints en `src/ultibot_backend/api/v1/endpoints/trading_params.py`:
        - `GET /api/v1/trading-params/confidence-thresholds`
        - `PUT /api/v1/trading-params/confidence-thresholds`
        - `GET /api/v1/trading-params/asset/{symbol}`
        - `PUT /api/v1/trading-params/asset/{symbol}`
    *   **[ ] 12.2.3:** Integrar con `TradingEngineService`:
        - Usar configuraciones específicas al evaluar trades
        - Aplicar stop-loss y take-profit personalizados por activo
        - Respetar límites de inversión por activo

### Task 12.3: [PENDIENTE] Panel de Control Unificado de Configuración
*   **Descripción:** Crear vista centralizada para todas las configuraciones avanzadas.
*   **Subtareas:**
    *   **[ ] 12.3.1:** Crear `AdvancedConfigurationView` en `src/ultibot_ui/views/advanced_config_view.py`:
        - Pestañas para "Filtros de Mercado", "Parámetros de Trading", "Umbrales de Confianza"
        - Integración de todos los diálogos creados anteriormente
        - Vista unificada del estado actual de configuraciones
        - Botón "Exportar Configuración", "Importar Configuración"
    *   **[ ] 12.3.2:** Añadir a `MainWindow`:
        - Nueva pestaña "Configuración Avanzada" en el menú principal
        - Conectar con `AdvancedConfigurationView`
        - Indicador visual de configuraciones activas

---

## Fase 13: [NUEVA] Funcionalidades Adicionales Críticas

*   **Objetivo:** Implementar funcionalidades complementarias para un sistema completo de trading personalizable.
*   **Prioridad:** MEDIA - Mejoras de calidad de vida y funcionalidad.

### Task 13.1: [PENDIENTE] Sistema de Alertas Personalizables Avanzadas
*   **Descripción:** Expandir el sistema de notificaciones para alertas basadas en condiciones de mercado personalizadas.
*   **Subtareas:**
    *   **[ ] 13.1.1:** Crear modelo `CustomAlert` en `user_configuration_models.py`:
        - `alert_id: str`, `name: str`, `description: Optional[str]`
        - `trigger_conditions: Dict[str, Any]` (condiciones de mercado)
        - `notification_channels: List[NotificationChannel]`
        - `is_active: bool`, `trigger_count: int`
    *   **[ ] 13.1.2:** Crear `AlertsService` en backend para monitorear condiciones
    *   **[ ] 13.1.3:** Crear `CustomAlertsDialog` en frontend para configurar alertas

### Task 13.2: [PENDIENTE] Monitor de Performance en Tiempo Real
*   **Descripción:** Dashboard avanzado de métricas y performance del sistema.
*   **Subtareas:**
    *   **[ ] 13.2.1:** Crear `PerformanceMonitorWidget` con métricas clave:
        - Win rate por estrategia en tiempo real
        - P&L acumulado (paper vs real)
        - Número de oportunidades detectadas vs ejecutadas
        - Latencia promedio de análisis IA
    *   **[ ] 13.2.2:** Crear gráficos de performance histórica:
        - Curva de equity en tiempo real
        - Distribución de trades por resultado
        - Heatmap de performance por par de divisas
    *   **[ ] 13.2.3:** Integrar en vista principal del dashboard

### Task 13.3: [PENDIENTE] Sistema de Exportación/Importación de Configuraciones
*   **Descripción:** Permitir backup y sharing de configuraciones complejas.
*   **Subtareas:**
    *   **[ ] 13.3.1:** Crear `ConfigurationExportService` en backend:
        - `export_user_configuration(user_id: str) -> Dict`
        - `import_user_configuration(user_id: str, config_data: Dict) -> bool`
        - Validación de integridad de configuraciones importadas
    *   **[ ] 13.3.2:** Crear `ConfigBackupDialog` en frontend:
        - Exportar toda la configuración a archivo JSON
        - Importar configuración desde archivo con preview de cambios
        - Crear "Configuration Templates" predefinidos
    *   **[ ] 13.3.3:** Añadir al menú "Archivo":
        - "Exportar Configuración..."
        - "Importar Configuración..."
        - "Cargar Template de Configuración..."

### Task 13.4: [PENDIENTE] Sistema de Backtesting Básico Integrado
*   **Descripción:** Herramienta simple de backtesting para validar configuraciones.
*   **Subtareas:**
    *   **[ ] 13.4.1:** Crear `BacktestingService` en backend:
        - Simular estrategias sobre datos históricos
        - Aplicar configuraciones de filtros y parámetros
        - Generar métricas de performance
    *   **[ ] 13.4.2:** Crear `BacktestingView` en frontend:
        - Selección de periodo de backtesting
        - Configuración de estrategias a testear
        - Visualización de resultados comparativos
    *   **[ ] 13.4.3:** Integrar con datos históricos existentes en `market_data`

---

## Fase 14: [NUEVA] Verificación Final y Optimización

*   **Objetivo:** Realizar verificación completa de todas las nuevas funcionalidades y optimizar el sistema.
*   **Prioridad:** ALTA - Asegurar estabilidad y performance del sistema completo.

### Task 14.1: [PENDIENTE] Testing Completo de Nuevas Funcionalidades
*   **Subtareas:**
    *   **[ ] 14.1.1:** Crear tests unitarios para todos los nuevos servicios
    *   **[ ] 14.1.2:** Crear tests de integración para flujos de configuración
    *   **[ ] 14.1.3:** Testing manual de todas las nuevas UIs

### Task 14.2: [PENDIENTE] Optimización de Performance
*   **Subtareas:**
    *   **[ ] 14.2.1:** Profiling de operaciones de filtrado de mercado
    *   **[ ] 14.2.2:** Optimización de queries de base de datos
    *   **[ ] 14.2.3:** Caching de configuraciones frecuentemente usadas

### Task 14.3: [PENDIENTE] Documentación y Entrega Final
*   **Subtareas:**
    *   **[ ] 14.3.1:** Actualizar documentación de usuario con nuevas funcionalidades
    *   **[ ] 14.3.2:** Crear guías de configuración paso a paso
    *   **[ ] 14.3.3:** Video demostración del sistema completo

---

## NOTAS DE IMPLEMENTACIÓN

### Principios de Diseño a Seguir:
1. **Configurabilidad Máxima:** Todo parámetro crítico debe ser modificable por el usuario
2. **Datos Reales:** Priorizar siempre datos en vivo de APIs sobre mocks
3. **Experiencia de Usuario:** Las configuraciones deben ser intuitivas y con valores por defecto sensatos
4. **Robustez:** Validación exhaustiva de configuraciones para prevenir errores operativos
5. **Performance:** Las configuraciones no deben impactar negativamente la latencia de trading

### Tecnologías Clave a Utilizar:
- **Backend:** Pydantic para validación, FastAPI para endpoints
- **Frontend:** PyQt5 con diálogos modales, QSettings para persistencia local
- **Persistencia:** Supabase/PostgreSQL para configuraciones complejas
- **Validación:** Type hints exhaustivos y validators de Pydantic

### Orden de Prioridad Recomendado:
1. **Fase 11** (Filtros de Mercado) - Base fundamental para personalización
2. **Fase 12** (Parámetros de Trading) - Flexibilidad operativa crítica
3. **Fase 13** (Funcionalidades Adicionales) - Mejoras de calidad de vida
4. **Fase 14** (Verificación Final) - Estabilización y entrega
