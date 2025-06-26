# API Contract Health Report

## 1. Propósito y Alcance
Este documento audita la coherencia de los contratos de la API entre el frontend y el backend de UltiBotInversiones. El objetivo es identificar y documentar cada endpoint, su método HTTP, su ruta y los modelos de datos (Pydantic) que utiliza para las solicitudes y respuestas.

## 2. Cómo Interpretar este Diagrama
- **Endpoint:** La ruta de la API y el método HTTP.
- **Request Model:** El modelo Pydantic que define la estructura de los datos de la solicitud. `N/A` si no aplica.
- **Response Model:** El modelo Pydantic que define la estructura de los datos de la respuesta.
- **Contrato Verificado:** Estado de la auditoría estática.
  - ✅: El contrato ha sido analizado.
  - ⏳: Pendiente de análisis.

## 3. Tabla de Contratos de API

| Endpoint | Request Model | Response Model | Contrato Verificado |
| --- | --- | --- | --- |
| `GET /binance/status` | `N/A` | `BinanceConnectionStatus` | ✅ |
| `GET /binance/balances` | `N/A` | `List[AssetBalance]` | ✅ |
| `POST /binance/verify` | `str` (query param) | `dict` | ✅ |
| `GET /config` | `N/A` | `UserConfiguration` | ✅ |
| `PATCH /config` | `UserConfigurationUpdate` | `UserConfiguration` | ✅ |
| `POST /config/real-trading-mode/activate` | `N/A` | `dict` | ✅ |
| `POST /config/real-trading-mode/deactivate` | `N/A` | `dict` | ✅ |
| `GET /config/real-trading-mode/status` | `N/A` | `dict` | ✅ |
| `GET /gemini/opportunities` | `N/A` | `List[dict]` | ✅ |
| `GET /tickers` | `str` (query param) | `List[Dict[str, Any]]` | ✅ |
| `GET /klines` | `str`, `str`, `int`, `Optional[int]`, `Optional[int]` (query params) | `List[Dict[str, Any]]` | ✅ |
| `GET /history` | `int` (query param) | `List[Notification]` | ✅ |
| `POST /{notification_id}/mark-as-read` | `UUID` (path param) | `Notification` | ✅ |
| `GET /opportunities/real-trading-candidates` | `N/A` | `List[Opportunity]` | ✅ |
| `GET /strategies` | `Optional[OperatingMode]` (query param) | `StrategyPerformanceResponse` | ✅ |
| `GET /metrics` | `OperatingMode`, `Optional[datetime]`, `Optional[datetime]` (query params) | `PerformanceMetrics` | ✅ |
| `GET /snapshot/{user_id}` | `UUID` (path), `TradingMode` (query) | `PortfolioSnapshot` | ✅ |
| `GET /summary` | `TradingMode` (query) | `PortfolioSummary` | ✅ |
| `GET /balance` | `TradingMode` (query) | `dict` | ✅ |
| `GET /paper/performance_summary` | `Optional[str]`, `Optional[datetime]`, `Optional[datetime]` (query params) | `PerformanceMetrics` | ✅ |
| `GET /real/performance_summary` | `Optional[str]`, `Optional[datetime]`, `Optional[datetime]` (query params) | `PerformanceMetrics` | ✅ |
| `POST /strategies` | `CreateTradingStrategyRequest` | `TradingStrategyResponse` | ✅ |
| `GET /strategies` | `N/A` | `StrategyListResponse` | ✅ |
| `GET /strategies/{strategy_id}` | `str` (path param) | `TradingStrategyResponse` | ✅ |
| `PUT /strategies/{strategy_id}` | `str` (path), `UpdateTradingStrategyRequest` (body) | `TradingStrategyResponse` | ✅ |
| `DELETE /strategies/{strategy_id}` | `str` (path param) | `N/A` | ✅ |
| `PATCH /strategies/{strategy_id}/activate` | `str` (path), `ActivateStrategyRequest` (body) | `StrategyActivationResponse` | ✅ |
| `PATCH /strategies/{strategy_id}/deactivate` | `str` (path), `ActivateStrategyRequest` (body) | `StrategyActivationResponse` | ✅ |
| `GET /strategies/active/{mode}` | `str` (path param) | `StrategyListResponse` | ✅ |
| `GET /telegram/status` | `N/A` | `TelegramConnectionStatus` | ✅ |
| `POST /telegram/verify` | `N/A` | `TelegramConnectionStatus` | ✅ |
| `GET /` | `TradingMode`, `Optional[str]`, `Optional[str]`, `Optional[date]`, `Optional[date]`, `int`, `int` (query params) | `List[Trade]` | ✅ |
| `GET /open` | `TradingMode` (query) | `List[Trade]` | ✅ |
| `GET /count` | `TradingMode`, `Optional[str]`, `Optional[date]`, `Optional[date]` (query params) | `dict` | ✅ |
| `GET /history/paper` | `Optional[str]`, `Optional[datetime]`, `Optional[datetime]`, `int`, `int` (query params) | `TradeHistoryResponse` | ✅ |
| `GET /history/real` | `Optional[str]`, `Optional[datetime]`, `Optional[datetime]`, `int`, `int` (query params) | `TradeHistoryResponse` | ✅ |
| `POST /real/confirm-opportunity/{opportunity_id}` | `UUID` (path), `ConfirmRealTradeRequest` (body) | `dict` | ✅ |
| `POST /market-order` | `MarketOrderRequest` (body) | `TradeOrderDetails` | ✅ |
| `GET /paper-balances` | `N/A` | `dict` | ✅ |
| `POST /paper-balances/reset` | `float` (query param) | `dict` | ✅ |
| `GET /supported-modes` | `N/A` | `dict` | ✅ |

## 4. Observaciones y Análisis del Oráculo
- **Cobertura Extensa:** La API cubre una amplia gama de funcionalidades, desde la gestión de la configuración y las estrategias hasta la consulta de datos de mercado, el estado de las conexiones y el rendimiento del portafolio.
- **Consistencia de Modelos:** Se observa un uso consistente de modelos Pydantic (`response_model`) para definir los contratos de respuesta, lo cual es una excelente práctica para la robustez y la auto-documentación de la API.
- **Parámetros de Consulta:** Múltiples endpoints utilizan parámetros de consulta para filtrado y paginación, lo que proporciona flexibilidad a los clientes de la API.
- **Rutas Anidadas:** Se identifican varias agrupaciones lógicas de rutas (ej. `/config/...`, `/strategies/...`, `/binance/...`), lo que mejora la organización.
- **Discrepancias Notadas:** El `TASKLIST.md` existente ([TASK-UI-REFACTOR-002]) ya identifica varias discrepancias entre las expectativas del frontend y la implementación actual del backend. Este informe de salud sirve como una validación y un mapa completo del estado actual, confirmando la necesidad de dicha refactorización.

## 5. Siguientes Pasos Sugeridos
1.  **Alinear Contratos:** Utilizar este informe como la "fuente de verdad" para ejecutar las tareas de refactorización listadas en `memory/TASKLIST.md` ([TASK-UI-REFACTOR-002]). El objetivo es que el cliente (`api_client.py`) y los routers del servidor estén perfectamente sincronizados.
2.  **Implementar Pruebas de Humo:** Crear una suite de tests de integración (`pytest`) que recorra cada uno de los endpoints listados en esta tabla. Para cada endpoint:
    -   Enviar un payload válido y verificar que se recibe un código de estado `2xx`.
    -   Verificar que la estructura de la respuesta coincide con el `Response Model` definido.
    -   Enviar un payload inválido (cuando aplique) y verificar que se recibe un error `4xx` (ej. `422 Unprocessable Entity`).
3.  **Revisar Rutas Raíz:** El router de `trades.py` está montado en la raíz (`""`). Considerar moverlo a un prefijo como `/trades` para mantener la consistencia con los otros routers.
