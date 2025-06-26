# Mapa de Contratos de API: Frontend-Backend

**Última Actualización:** 2025-06-26 01:30 UTC
**Agente Responsable:** Leadcoder
**Misión:** [TASK-BACKEND-REFACTOR-001]

Este documento mapea cada llamada a la API desde la UI del frontend a su correspondiente endpoint en el backend. Sirve como el "contrato" que debe cumplirse durante la refactorización para garantizar una comunicación sin errores.

| UI Component / Service | Frontend Method (`api_client`) | HTTP Method | Backend Endpoint | Request Payload Schema (Pydantic/Dict) | Expected Response Schema (Pydantic/Dict) | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Configuración** | | | | | | |
| `main_window.py` | `get_user_configuration` | GET | `/api/v1/config/user` | `None` | `UserConfiguration` | |
| `workers.py` | `get_user_configuration` | GET | `/api/v1/config/user` | `None` | `UserConfiguration` | |
| `market_data_widget.py`| `get_user_configuration` | GET | `/api/v1/config/user` | `None` | `UserConfiguration` | |
| `ui_config_service.py` | `get_user_configuration` | GET | `/api/v1/config/user/{user_id}` | `None` | `UserConfiguration` | La ruta parece variar. **Verificar consistencia**. |
| `workers.py` | `update_user_configuration` | PUT | `/api/v1/config/user` | `UserConfiguration` | `UserConfiguration` | |
| `market_data_widget.py`| `update_user_configuration` | PUT | `/api/v1/config/user` | `UserConfiguration` | `UserConfiguration` | |
| `ui_config_service.py` | `save_user_configuration` | PUT | `/api/v1/config/user/{user_id}` | `dict` | `{"success": bool}` | La ruta y el schema de respuesta difieren. **Unificar**. |
| **Trading Mode** | | | | | | |
| `workers.py` | `activate_real_trading_mode` | POST | `/api/v1/trading/mode/activate` | `None` | `{"status": str}` | |
| `workers.py` | `deactivate_real_trading_mode`| POST | `/api/v1/trading/mode/deactivate`| `None` | `{"status": str}` | |
| **Estrategias** | | | | | | |
| `workers.py` | `get_strategies` | GET | `/api/v1/strategies/` | `None` | `List[AIStrategyConfiguration]` | |
| `ui_strategy_service.py`| `get_strategies` | GET | `/api/v1/strategies/` | `None` | `List[AIStrategyConfiguration]` | |
| `strategy_config_dialog.py`| `create_strategy_config` | POST | `/api/v1/strategies/` | `AIStrategyConfiguration` | `AIStrategyConfiguration` | |
| `ui_strategy_service.py`| `create_strategy_config` | POST | `/api/v1/strategies/` | `dict` | `AIStrategyConfiguration` | El payload debe ser el modelo Pydantic. |
| `strategy_config_dialog.py`| `update_strategy_config` | PUT | `/api/v1/strategies/{strategy_id}` | `AIStrategyConfiguration` | `AIStrategyConfiguration` | |
| `ui_strategy_service.py`| `update_strategy_config` | PUT | `/api/v1/strategies/{strategy_id}` | `dict` | `AIStrategyConfiguration` | El payload debe ser el modelo Pydantic. |
| `ui_strategy_service.py`| `delete_strategy_config` | DELETE | `/api/v1/strategies/{strategy_id}` | `None` | `{"status": str, "id": str}` | |
| `ui_strategy_service.py`| `update_strategy_status` | PUT | `/api/v1/strategies/{strategy_id}/status` | `{"is_active": bool, "trading_mode": str}` | `AIStrategyConfiguration` | |
| **Datos de Mercado** | | | | | | |
| `workers.py` | `get_market_data` | GET | `/api/v1/market/tickers` | `{"symbols": List[str]}` | `List[Ticker]` | El payload es un query param, no un body. |
| `market_data_widget.py`| `get_market_data` | GET | `/api/v1/market/tickers` | `{"symbols": List[str]}` | `List[Ticker]` | El payload es un query param, no un body. |
| `ui_market_data_service.py`| `get_market_data` | GET | `/api/v1/market/tickers` | `{"symbols": List[str]}` | `List[Ticker]` | El payload es un query param, no un body. |
| `chart_widget.py` | `get_ohlcv_data` | GET | `/api/v1/market/ohlcv` | `{"symbol": str, "interval": str, "limit": int}` | `List[Kline]` | Query params. |
| `ui_market_data_service.py`| `get_ohlcv_data` | GET | `/api/v1/market/ohlcv` | `{"symbol": str, "interval": str, "limit": int}` | `List[Kline]` | Query params. |
| **Trades y Órdenes** | | | | | | |
| `workers.py` | `get_trades` | GET | `/api/v1/trades/` | `{"user_id": str, "trading_mode": str, "status": str, "limit": int}` | `List[Trade]` | Query params. |
| `dashboard_view.py` | `get_trades` | GET | `/api/v1/trades/` | `{"trading_mode": "both"}` | `List[Trade]` | Query params. |
| `portfolio_widget.py` | `get_trades` | GET | `/api/v1/trades/` | `{"trading_mode": str, "status": "open"}` | `List[Trade]` | Query params. |
| `paper_trading_report_widget.py`| `get_trades` | GET | `/api/v1/trades/` | `{"user_id": str, ...}` | `List[Trade]` | Query params. |
| `order_form_widget.py` | `execute_market_order` | POST | `/api/v1/orders/market` | `Order` | `OrderResult` | |
| `trading_terminal_view.py`| `create_order` | POST | `/api/v1/orders/` | `Order` | `OrderResult` | **Endpoint inconsistente** con el anterior. Unificar. |
| **Portfolio** | | | | | | |
| `portfolio_widget.py` | `get_portfolio_snapshot` | GET | `/api/v1/portfolio/snapshot` | `{"user_id": str, "trading_mode": str}` | `PortfolioSnapshot` | Query params. |
| `portfolio_view.py` | `get_portfolio_snapshot` | GET | `/api/v1/portfolio/snapshot` | `{"user_id": str, "trading_mode": str}` | `PortfolioSnapshot` | Query params. |
| `ui_market_data_service.py`| `get_portfolio_snapshot` | GET | `/api/v1/portfolio/snapshot` | `{"user_id": str, "trading_mode": str}` | `PortfolioSnapshot` | Query params. |
| **Oportunidades IA** | | | | | | |
| `opportunities_view.py`| `get_ai_opportunities` | GET | `/api/v1/ai/opportunities` | `None` | `List[Opportunity]` | |
| `opportunities_view.py`| `analyze_opportunity_with_ai`| POST | `/api/v1/ai/analyze` | `{"user_id": str, "opportunity_id": str}` | `AIAnalysis` | |
| `opportunities_view.py`| `execute_trade_from_opportunity`| POST | `/api/v1/ai/execute_trade` | `{"user_id": str, "opportunity_id": str}` | `Trade` | |
| `real_trade_confirmation_dialog.py`| `confirm_real_trade_opportunity`| POST | `/api/v1/ai/confirm_trade` | `{"opportunity_id": str}` | `Trade` | **Endpoint inconsistente**. Unificar con el anterior. |
| **Notificaciones** | | | | | | |
| `notification_widget.py`| `get_notification_history` | GET | `/api/v1/notifications/` | `{"limit": int}` | `List[Notification]` | Query params. |
| `ui_market_data_service.py`| `get_notification_history` | GET | `/api/v1/notifications/` | `{"limit": int}` | `List[Notification]` | Query params. |
| **Inicialización** | | | | | | |
| `main_window.py` | `initialize_client` | N/A | N/A | N/A | N/A | Operación interna del cliente HTTP. |
| `main_window.py` | `close` | N/A | N/A | N/A | N/A | Operación interna del cliente HTTP. |

---
## Discrepancy Log (Auditoría en Progreso)

### 1. Módulo de Configuración de Usuario
- **Estado:** **AUDITADO Y CONFIRMADO**
- **Resumen de Desviaciones:**
    - **Ruta del Endpoint:** El backend expone `/api/v1/config`. El frontend intenta acceder a `/api/v1/config/user` y `/api/v1/config/user/{user_id}`. **ACCIÓN REQUERIDA:** Corregir todas las llamadas en el frontend a la ruta correcta.
    - **Método HTTP:** El backend utiliza `PATCH` para actualizaciones parciales (`UserConfigurationUpdate`). El frontend utiliza `PUT`. **ACCIÓN REQUERIDA:** Cambiar las llamadas de actualización en el frontend a `PATCH`.
    - **Schema de Payload:** El frontend envía `dict` en lugar de un modelo Pydantic validado en algunos servicios. **ACCIÓN REQUERIDA:** Estandarizar el envío del modelo `UserConfiguration` desde el frontend.
    - **Schema de Respuesta:** El `ui_config_service.py` del frontend espera `{"success": bool}` en la respuesta de actualización, pero el backend devuelve el objeto `UserConfiguration` completo. **ACCIÓN REERIDA:** Ajustar el frontend para que maneje el objeto `UserConfiguration` como respuesta.
    - **Convención de Nombres (Casing):** Los modelos del backend usan `camelCase` para los alias JSON. **ACCIÓN REQUERIDA:** Asegurar que el `api_client` del frontend serialice y deserialice los objetos respetando `camelCase`.

### 2. Módulo de Creación de Órdenes
- **Estado:** **AUDITADO Y CONFIRMADO**
- **Resumen de Desviaciones:**
    - **Ruta del Endpoint:** El backend expone una ruta unificada `POST /api/v1/trading/market-order`. El frontend intenta acceder a `/api/v1/orders/market` y `/api/v1/orders/`. **ACCIÓN REQUERIDA:** Refactorizar todas las llamadas de creación de órdenes en el frontend para que apunten al endpoint correcto y utilicen el `MarketOrderRequest` schema.

### 3. Módulo de Ejecución de Trade (IA)
- **Estado:** **AUDITADO Y CONFIRMADO**
- **Resumen de Desviaciones:**
    - **Ruta del Endpoint:** El backend expone `POST /api/v1/trading/real/confirm-opportunity/{opportunity_id}` para la confirmación manual de trades de IA. El frontend intenta acceder a `/api/v1/ai/execute_trade` y `/api/v1/ai/confirm_trade`. **ACCIÓN REQUERIDA:** Refactorizar las llamadas en `opportunities_view.py` y `real_trade_confirmation_dialog.py` para que apunten al endpoint correcto.

### 4. Módulo de Gestión de Estrategias
- **Estado:** **AUDITADO Y CONFIRMADO**
- **Resumen de Desviaciones:**
    - **Schema de Lista:** El endpoint `GET /strategies` devuelve un objeto `StrategyListResponse` (`{"strategies": [...], "total_count": ...}`), no una lista plana. **ACCIÓN REQUERIDA:** El frontend debe ser actualizado para procesar este objeto.
    - **Schemas de Creación/Actualización:** El backend utiliza modelos específicos (`CreateTradingStrategyRequest`, `UpdateTradingStrategyRequest`) que son diferentes del modelo `AIStrategyConfiguration` que el frontend intenta usar. **ACCIÓN REQUERIDA:** El frontend debe construir y enviar los modelos de solicitud correctos.
    - **Schema de Eliminación:** El endpoint `DELETE /strategies/{strategy_id}` devuelve un `204 No Content`. El frontend espera un cuerpo JSON. **ACCIÓN REQUERIDA:** El frontend debe manejar correctamente una respuesta vacía en la eliminación.
    - **Schema de Activación/Desactivación:** El backend utiliza endpoints `PATCH` (`/activate`, `/deactivate`) que esperan un payload `ActivateStrategyRequest`. El frontend utiliza un endpoint `PUT` (`/status`) con un payload completamente diferente. **ACCIÓN REQUERIDA:** El frontend debe ser refactorizado para usar los endpoints, métodos y schemas correctos para cambiar el estado de una estrategia.

### 5. Consistencia General
- **Estado:** **AUDITADO Y CONFIRMADO**
- **Resumen de Desviaciones:**
    - **Uso de Query Parameters:** El backend utiliza correctamente `Query Parameters` para las peticiones `GET` (ej. `GET /tickers?symbols=BTC/USDT,ETH/USDT`). El frontend intenta enviar un cuerpo JSON en estas peticiones. **ACCIÓN REQUERIDA:** Refactorizar el `api_client` del frontend para que construya correctamente las URLs con query parameters para todas las peticiones `GET` que requieran filtros.
    - **Payloads de `dict`:** Se confirma que varios servicios del frontend envían `dict` crudos en lugar de modelos Pydantic validados, aumentando el riesgo de enviar datos malformados. **ACCIÓN REQUERIDA:** Estandarizar el uso de modelos Pydantic en la capa de servicio del frontend antes de realizar la llamada a la API.
