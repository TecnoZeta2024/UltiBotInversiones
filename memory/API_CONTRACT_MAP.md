# API Contract Map (Updated Draft)

This document outlines the API endpoints identified in the `ultibot_backend` and their associated request/response models. This is a living document and will be updated as the audit progresses.

## Endpoints

### `strategies.py`

| Method | Path | Description | Request Model | Response Model |
|---|---|---|---|---|
| `POST` | `/api/v1/strategies` | Create new trading strategy | `CreateTradingStrategyRequest` | `TradingStrategyResponse` |
| `GET` | `/api/v1/strategies` | List trading strategies | - | `StrategyListResponse` |
| `GET` | `/api/v1/strategies/{strategy_id}` | Get trading strategy by ID | - | `TradingStrategyResponse` |
| `PUT` | `/api/v1/strategies/{strategy_id}` | Update trading strategy | `UpdateTradingStrategyRequest` | `TradingStrategyResponse` |
| `DELETE` | `/api/v1/strategies/{strategy_id}` | Delete trading strategy | - | `204 No Content` |
| `PATCH` | `/api/v1/strategies/{strategy_id}/activate` | Activate trading strategy | `ActivateStrategyRequest` | `StrategyActivationResponse` |
| `PATCH` | `/api/v1/strategies/{strategy_id}/deactivate` | Deactivate trading strategy | `ActivateStrategyRequest` | `StrategyActivationResponse` |
| `GET` | `/api/v1/strategies/active/{mode}` | Get active strategies by mode | - | `StrategyListResponse` |

### `trading.py`

| Method | Path | Description | Request Model | Response Model |
|---|---|---|---|---|
| `POST` | `/api/v1/real/confirm-opportunity/{opportunity_id}` | Confirm real trading opportunity | `ConfirmRealTradeRequest` | `{"message": ..., "trade_details": ...}` |
| `POST` | `/api/v1/market-order` | Execute a market order | `MarketOrderRequest` | `TradeOrderDetails` |
| `GET` | `/api/v1/paper-balances` | Get paper trading balances | - | `{"user_id": ..., "trading_mode": ..., "balances": ...}` |
| `POST` | `/api/v1/paper-balances/reset` | Reset paper trading balances | `initial_capital` (query param) | `{"user_id": ..., "trading_mode": ..., "message": ..., "new_balance": ...}` |
| `GET` | `/api/v1/supported-modes` | Get supported trading modes | - | `{"supported_trading_modes": ..., "description": ...}` |

### `opportunities.py`

| Method | Path | Description | Request Model | Response Model |
|---|---|---|---|---|
| `GET` | `/api/v1/gemini/opportunities` | List existing AI opportunities | - | `List[Opportunity]` |
| `GET` | `/api/v1/opportunities/real-trading-candidates` | List high-confidence opportunities for real trading | - | `List[Opportunity]` |
| `POST` | `/api/v1/gemini/opportunities` | Process AI analysis to generate opportunities | `AIAnalysisRequest` | `AIAnalysisResponse` |

### `config.py`

| Method | Path | Description | Request Model | Response Model |
|---|---|---|---|---|
| `GET` | `/api/v1/config` | Get user configuration | - | `UserConfiguration` |
| `PATCH` | `/api/v1/config` | Update user configuration | `UserConfigurationUpdate` | `UserConfiguration` |
| `POST` | `/api/v1/config/real-trading-mode/activate` | Activate real trading mode | - | `{"message": ...}` |
| `POST` | `/api/v1/config/real-trading-mode/deactivate` | Deactivate real trading mode | - | `{"message": ...}` |
| `GET` | `/api/v1/config/real-trading-mode/status` | Get real trading mode status | - | `dict` |

### `market_data.py`

| Method | Path | Description | Request Model | Response Model |
|---|---|---|---|---|
| `GET` | `/api/v1/tickers` | Get ticker data for symbols | `symbols_str` (query param) | `List[Dict[str, Any]]` |
| `GET` | `/api/v1/klines` | Get candlestick (OHLCV) data | `symbol`, `interval`, `limit`, `start_time`, `end_time` (query params) | `List[Dict[str, Any]]` |
