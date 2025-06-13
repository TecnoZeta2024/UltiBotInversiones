import asyncio
import logging
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# --- Configuraciones y Imports Arquitectónicos ---
from src.ultibot_backend.dependencies import get_settings
from src.ultibot_backend.core.ports import IPersistencePort
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
# Corregido: La ubicación correcta de los modelos de configuración de usuario.
from src.ultibot_backend.core.domain_models.user_configuration_models import (
    UserConfiguration, 
    RiskProfileSettings, 
    RealTradingSettings,
    RiskProfile
)

# Configurar un logger básico para el script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """
    Script para poblar la configuración de gestión de capital del usuario fijo.
    Este script interactúa directamente con el puerto de persistencia para mayor simplicidad.
    """
    logger.info("Iniciando script para poblar la configuración del usuario...")
    
    app_settings = get_settings()

    if not app_settings.database_url or not app_settings.fixed_user_id:
        logger.error("Error crítico: DATABASE_URL o FIXED_USER_ID no están configurados.")
        return

    logger.info(f"Usando DATABASE_URL: {app_settings.database_url[:20]}...")
    logger.info(f"Poblando configuración para User ID: {app_settings.fixed_user_id}")

    # 1. Inicializar el motor de la base de datos y la sesión
    engine = create_async_engine(app_settings.database_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db_session:
        try:
            # 2. Instanciar el puerto de persistencia
            persistence_port: IPersistencePort = SupabasePersistenceService(db_session=db_session)

            # 3. Definir la configuración por defecto usando la nueva estructura de modelos
            user_id_str = app_settings.fixed_user_id
            now = datetime.now(timezone.utc)

            default_config = UserConfiguration(
                user_id=user_id_str,
                # --- Campos Requeridos y Esenciales con Defaults ---
                id=str(UUID(int=0)), # Proporcionar un ID por defecto
                telegram_chat_id=None,
                notification_preferences=[],
                enable_telegram_notifications=True,
                default_paper_trading_capital=10000.0,
                paper_trading_active=True,
                paper_trading_assets=[],
                watchlists=[],
                favorite_pairs=[],
                risk_profile=RiskProfile.MODERATE,
                risk_profile_settings=RiskProfileSettings(
                    daily_capital_risk_percentage=0.01,  # 1%
                    per_trade_capital_risk_percentage=0.005, # 0.5%
                    max_drawdown_percentage=0.05 # 5%
                ),
                real_trading_settings=RealTradingSettings(
                    real_trading_mode_active=False,
                    real_trades_executed_count=0,
                    max_concurrent_operations=5,
                    max_real_trades=10,
                    daily_loss_limit_absolute=None,
                    daily_profit_target_absolute=None,
                    asset_specific_stop_loss=None,
                    auto_pause_trading_conditions=None
                ),
                # --- Nuevos campos opcionales inicializados como None ---
                market_scan_presets=None,
                active_market_scan_preset_id=None,
                custom_market_scan_configurations=None,
                asset_trading_parameters=None,
                alert_configurations=None,
                performance_metrics=None,
                performance_history=None,
                ai_strategy_configurations=None,
                ai_analysis_confidence_thresholds=None,
                mcp_server_preferences=None,
                selected_theme=None,
                dashboard_layout_profiles=None,
                active_dashboard_layout_profile_id=None,
                dashboard_layout_config=None,
                cloud_sync_preferences=None,
                created_at=now,
                updated_at=now
            )

            # 4. Guardar la configuración usando directamente el puerto de persistencia
            logger.info("Guardando la configuración del usuario en la base de datos...")
            # El puerto espera un diccionario, por lo que se convierte el modelo Pydantic.
            config_dict = default_config.model_dump(mode='json', by_alias=True)
            await persistence_port.upsert_user_configuration(config_dict)
            logger.info("Configuración de usuario poblada y guardada correctamente.")

        except Exception as e:
            logger.error(f"Ocurrió un error al poblar la configuración del usuario: {e}", exc_info=True)
        finally:
            await engine.dispose()
            logger.info("Conexión a la base de datos cerrada.")


if __name__ == "__main__":
    asyncio.run(main())
