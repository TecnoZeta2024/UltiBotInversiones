# Script para poblar la configuración de gestión de capital del usuario fijo en Supabase
import asyncio
from uuid import UUID
from datetime import datetime
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.shared.data_types import UserConfiguration, RiskProfileSettings, RealTradingSettings
from src.ultibot_backend.app_config import settings
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.services.market_data_service import MarketDataService
import json

async def main():
    persistence_service = SupabasePersistenceService()
    await persistence_service.connect()
    binance_adapter = BinanceAdapter()
    credential_service = CredentialService(persistence_service=persistence_service, binance_adapter=binance_adapter)
    market_data_service = MarketDataService(credential_service=credential_service, binance_adapter=binance_adapter)
    portfolio_service = PortfolioService(market_data_service=market_data_service, persistence_service=persistence_service)  # market_data_service puede ser None para este script
    config_service = ConfigService(
        persistence_service=persistence_service,
        credential_service=credential_service,
        portfolio_service=portfolio_service
    )

    user_id = settings.FIXED_USER_ID
    now = datetime.utcnow()

    config = UserConfiguration(
        user_id=user_id,
        defaultPaperTradingCapital=10000.0,
        paperTradingActive=True,
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.5,
            perTradeCapitalRiskPercentage=0.1,
            takeProfitPercentage=0.02,
            trailingStopLossPercentage=0.01,
            trailingStopCallbackRate=0.005
        ),
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True,
            real_trades_executed_count=0,
            max_real_trades=5,
            daily_capital_risked_usd=0.0,
            last_daily_reset=now
        ),
        createdAt=now,
        updatedAt=now
    )

    config_dict = config.model_dump(mode='json', by_alias=True)
    # Serializar los campos anidados manualmente solo si existen
    if config.riskProfileSettings is not None:
        config_dict['riskProfileSettings'] = json.dumps(config.riskProfileSettings.model_dump(mode='json', by_alias=True))
    if config.realTradingSettings is not None:
        config_dict['realTradingSettings'] = json.dumps(config.realTradingSettings.model_dump(mode='json', by_alias=True))

    await config_service.persistence_service.upsert_user_configuration(user_id, config_dict)
    print("Configuración de usuario poblada correctamente.")
    await persistence_service.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
