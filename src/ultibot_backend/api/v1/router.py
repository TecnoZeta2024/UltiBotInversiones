from fastapi import APIRouter

from ultibot_backend.api.v1.endpoints import (
    ai_analysis,
    binance_status,
    config,
    gemini,
    market_configuration,
    market_data,
    notifications,
    opportunities,
    performance,
    portfolio,
    prompts,
    reports,
    strategies,
    telegram_status,
    trades,
    trading_mode,
    trading,
)

api_router = APIRouter()

# Include all the individual routers
api_router.include_router(ai_analysis.router, prefix="/ai", tags=["AI Analysis"])
api_router.include_router(binance_status.router, prefix="/status", tags=["Status"])
api_router.include_router(config.router, prefix="/config", tags=["Configuration"])
api_router.include_router(gemini.router, prefix="/gemini", tags=["Gemini"])
api_router.include_router(market_configuration.router, prefix="/market-config", tags=["Market Configuration"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["Market Data"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["Opportunities"])
api_router.include_router(performance.router, prefix="/performance", tags=["Performance"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["Strategies"])
api_router.include_router(telegram_status.router, prefix="/telegram", tags=["Telegram"])
api_router.include_router(trades.router, prefix="/trades", tags=["Trades"])
api_router.include_router(trading_mode.router, prefix="/trading-mode", tags=["Trading Mode"])
api_router.include_router(trading.router, prefix="/trading", tags=["Trading"])
