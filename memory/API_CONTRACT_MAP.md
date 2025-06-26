# Mapa de Contratos de API: Frontend (ultibot_ui)

**ID Tarea:** [TASK-UI-REFACTOR-002]
**Agente:** ui-ux
**Fecha:** 2025-06-26

Este documento mapea todas las interacciones entre el frontend (`src/ultibot_ui`) y el backend a través del `api_client`. Sirve como base para el **Protocolo de Auditoría de Contratos de API (PACA)**.

| Componente Cliente (Archivo) | Método Invocado | Endpoint Esperado (Inferido) | Notas |
| :--- | :--- | :--- | :--- |
| `src/ultibot_ui/workers.py` | `get_user_configuration` | `GET /api/v1/config/user` | **Discrepancia:** El endpoint real es `GET /api/v1/config`. |
| `src/ultibot_ui/workers.py` | `update_user_configuration` | `PUT /api/v1/config/user` | **Discrepancia:** El endpoint real es `PATCH /api/v1/config`. |
| `src/ultibot_ui/workers.py` | `activate_real_trading_mode` | `POST /api/v1/trading/mode/activate` | **Discrepancia:** El endpoint real es `POST /api/v1/config/real-trading-mode/activate`. |
| `src/ultibot_ui/workers.py` | `deactivate_real_trading_mode` | `POST /api/v1/trading/mode/deactivate` | **Discrepancia:** El endpoint real es `POST /api/v1/config/real-trading-mode/deactivate`. |
| `src/ultibot_ui/workers.py` | `get_strategies` | `GET /api/v1/strategies` | |
| `src/ultibot_ui/workers.py` | `get_trades` | `GET /api/v1/trades` | **Discrepancia:** El frontend envía un `user_id` que el backend no espera como parámetro de consulta. |
| `src/ultibot_ui/workers.py` | `get_market_data` | `GET /api/v1/market/data` | **Discrepancia:** El endpoint real es `GET /api/v1/market/tickers`. |
| `src/ultibot_ui/windows/main_window.py` | `get_user_configuration` | `GET /api/v1/config/user` | |
| `src/ultibot_ui/windows/dashboard_view.py` | `get_trades` | `GET /api/v1/trades` | |
| `src/ultibot_ui/widgets/real_trade_confirmation_dialog.py` | `confirm_real_trade_opportunity` | `POST /api/v1/opportunities/{id}/confirm` | |
| `src/ultibot_ui/widgets/portfolio_widget.py` | `get_portfolio_snapshot` | `GET /api/v1/portfolio/snapshot` | |
| `src/ultibot_ui/widgets/portfolio_widget.py` | `get_trades` | `GET /api/v1/trades` | |
| `src/ultibot_ui/widgets/paper_trading_report_widget.py` | `get_trades` | `GET /api/v1/trades` | |
| `src/ultibot_ui/widgets/order_form_widget.py` | `execute_market_order` | `POST /api/v1/orders/market` | |
| `src/ultibot_ui/widgets/notification_widget.py` | `get_notification_history` | `GET /api/v1/notifications` | |
| `src/ultibot_ui/widgets/market_data_widget.py` | `get_user_configuration` | `GET /api/v1/config/user` | |
| `src/ultibot_ui/widgets/market_data_widget.py` | `get_market_data` | `GET /api/v1/market/data` | |
| `src/ultibot_ui/widgets/market_data_widget.py` | `update_user_configuration` | `PUT /api/v1/config/user` | |
| `src/ultibot_ui/widgets/chart_widget.py` | `get_ohlcv_data` | `GET /api/v1/market/ohlcv` | **Discrepancia:** El endpoint real es `GET /api/v1/market/klines`. |
| `src/ultibot_ui/views/trading_terminal_view.py` | `execute_market_order` | `POST /api/v1/orders/market` | |
| `src/ultibot_ui/views/portfolio_view.py` | `get_portfolio_snapshot` | `GET /api/v1/portfolio/snapshot` | |
| `src/ultibot_ui/views/opportunities_view.py` | `get_ai_opportunities` | `GET /api/v1/opportunities/ai` | **Discrepancia:** El endpoint real es `GET /api/v1/opportunities/real-trading-candidates`. |
| `src/ultibot_ui/views/opportunities_view.py` | `analyze_opportunity_with_ai` | `POST /api/v1/opportunities/analyze` | **Discrepancia:** Endpoint no encontrado en el backend. |
| `src/ultibot_ui/views/opportunities_view.py` | `confirm_real_trade_opportunity` | `POST /api/v1/opportunities/{id}/confirm` | **Discrepancia:** Endpoint no encontrado en el backend. |
| `src/ultibot_ui/services/ui_strategy_service.py` | `get_strategies` | `GET /api/v1/strategies` | |
| `src/ultibot_ui/services/ui_strategy_service.py` | `create_strategy_config` | `POST /api/v1/strategies` | |
| `src/ultibot_ui/services/ui_strategy_service.py` | `update_strategy_config` | `PUT /api/v1/strategies/{id}` | |
| `src/ultibot_ui/services/ui_strategy_service.py` | `delete_strategy_config` | `DELETE /api/v1/strategies/{id}` | |
| `src/ultibot_ui/services/ui_strategy_service.py` | `activate_strategy` | `POST /api/v1/strategies/{id}/activate` | **Discrepancia:** El método real es `PATCH`. |
| `src/ultibot_ui/services/ui_strategy_service.py` | `deactivate_strategy` | `POST /api/v1/strategies/{id}/deactivate` | **Discrepancia:** El método real es `PATCH`. |
| `src/ultibot_ui/services/ui_market_data_service.py` | `get_portfolio_snapshot` | `GET /api/v1/portfolio/snapshot` | |
| `src/ultibot_ui/services/ui_market_data_service.py` | `get_ohlcv_data` | `GET /api/v1/market/ohlcv` | |
| `src/ultibot_ui/services/ui_market_data_service.py` | `get_notification_history` | `GET /api/v1/notifications` | |
| `src/ultibot_ui/services/ui_market_data_service.py` | `get_market_data` | `GET /api/v1/market/data` | |
| `src/ultibot_ui/services/ui_config_service.py` | `get_user_configuration` | `GET /api/v1/config/user` | |
| `src/ultibot_ui/services/ui_config_service.py` | `update_user_configuration` | `PUT /api/v1/config/user` | |
| `src/ultibot_ui/main.py` | `initialize_client` | N/A | Inicialización interna del cliente HTTP. |
| `src/ultibot_ui/main.py` | `close` | N/A | Cierre interno del cliente HTTP. |
| `src/ultibot_ui/dialogs/strategy_config_dialog.py` | `update_strategy_config` | `PUT /api/v1/strategies/{id}` | |
| `src/ultibot_ui/dialogs/strategy_config_dialog.py` | `create_strategy_config` | `POST /api/v1/strategies` | |
