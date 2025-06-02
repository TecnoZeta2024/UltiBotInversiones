from __future__ import annotations # Importar para type hints adelantados

from fastapi import FastAPI
from uuid import UUID
import logging
from typing import Optional

from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.order_execution_service import OrderExecutionService, PaperOrderExecutionService # Importar OrderExecutionService
from src.ultibot_backend.services.trading_engine_service import TradingEngineService # Importar TradingEngineService
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService # Importar AIOrchestratorService
from src.ultibot_backend.adapters.mobula_adapter import MobulaAdapter # Importar MobulaAdapter
from langchain_google_genai import ChatGoogleGenerativeAI # Importar ChatGoogleGenerativeAI
from src.shared.data_types import ServiceName, UserConfiguration

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="UltiBot Backend")

# Instancias de servicios (se inicializarán al inicio de la aplicación)
# Se declaran como globales para que puedan ser accedidas por las funciones de dependencia.
credential_service: Optional[CredentialService] = None
notification_service: Optional[NotificationService] = None
binance_adapter: Optional[BinanceAdapter] = None
market_data_service: Optional[MarketDataService] = None
persistence_service: Optional[SupabasePersistenceService] = None
portfolio_service: Optional[PortfolioService] = None
config_service: Optional[ConfigService] = None
order_execution_service: Optional[OrderExecutionService] = None # Añadir OrderExecutionService
paper_order_execution_service: Optional[PaperOrderExecutionService] = None # Añadir PaperOrderExecutionService
trading_engine_service: Optional[TradingEngineService] = None # Añadir TradingEngineService
ai_orchestrator_service: Optional[AIOrchestratorService] = None # Añadir AIOrchestratorService
mobula_adapter: Optional[MobulaAdapter] = None # Añadir MobulaAdapter
llm_provider: Optional[ChatGoogleGenerativeAI] = None # Añadir llm_provider
user_configuration: Optional[UserConfiguration] = None # Para almacenar la configuración cargada

# Asumimos un user_id fijo para la v1.0 de una aplicación local
# En una aplicación real, esto vendría de la autenticación del usuario.
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001") 

# --- Funciones de dependencia para inyección en FastAPI ---
# Estas funciones devuelven las instancias globales de los servicios
# que se inicializan en el evento de startup.

def get_persistence_service() -> SupabasePersistenceService:
    if persistence_service is None:
        raise RuntimeError("PersistenceService no inicializado.")
    return persistence_service

def get_credential_service() -> CredentialService:
    if credential_service is None:
        raise RuntimeError("CredentialService no inicializado.")
    return credential_service

def get_binance_adapter() -> BinanceAdapter:
    if binance_adapter is None:
        raise RuntimeError("BinanceAdapter no inicializado.")
    return binance_adapter

def get_market_data_service() -> MarketDataService:
    if market_data_service is None:
        raise RuntimeError("MarketDataService no inicializado.")
    return market_data_service

def get_portfolio_service() -> PortfolioService:
    if portfolio_service is None:
        raise RuntimeError("PortfolioService no inicializado.")
    return portfolio_service

def get_notification_service() -> NotificationService:
    if notification_service is None:
        raise RuntimeError("NotificationService no inicializado.")
    return notification_service

def get_config_service() -> ConfigService:
    if config_service is None:
        raise RuntimeError("ConfigService no inicializado.")
    return config_service

@app.on_event("startup")
async def startup_event():
    """
    Evento que se ejecuta al iniciar la aplicación FastAPI.
    Inicializa servicios y realiza verificaciones iniciales.
    """
    global credential_service, notification_service, binance_adapter, market_data_service, persistence_service, portfolio_service, config_service, order_execution_service, paper_order_execution_service, trading_engine_service, ai_orchestrator_service, mobula_adapter, llm_provider, user_configuration
    logger.info("Iniciando UltiBot Backend...")
    
    from src.ultibot_backend.app_config import settings # Importar settings aquí para asegurar que esté disponible

    # Leer manualmente CREDENTIAL_ENCRYPTION_KEY desde .env para evitar problemas de carga
    raw_env_key = None
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("CREDENTIAL_ENCRYPTION_KEY="):
                    raw_env_key = line.strip().split("=", 1)[1].strip('"')
                    break
    except Exception as e:
        logger.error(f"No se pudo leer manualmente CREDENTIAL_ENCRYPTION_KEY desde .env: {e}")

    logger.info(f"CREDENTIAL_ENCRYPTION_KEY desde settings: {settings.CREDENTIAL_ENCRYPTION_KEY}")
    logger.info(f"CREDENTIAL_ENCRYPTION_KEY leída manualmente desde .env: {raw_env_key}")

    # Usar la clave leída manualmente si está disponible, de lo contrario, la de settings
    effective_encryption_key = raw_env_key if raw_env_key else settings.CREDENTIAL_ENCRYPTION_KEY

    # Inicializar PersistenceService primero
    persistence_service = SupabasePersistenceService()
    await persistence_service.connect() # Conectar a la base de datos al inicio

    credential_service = CredentialService(encryption_key=effective_encryption_key)
    binance_adapter = BinanceAdapter() # Inicializar BinanceAdapter
    market_data_service = MarketDataService(credential_service=credential_service, binance_adapter=binance_adapter) # Inicializar MarketDataService
    portfolio_service = PortfolioService(market_data_service=market_data_service, persistence_service=persistence_service) # Inicializar PortfolioService
    
    # Initialize ConfigService first (now NotificationService is optional in its constructor)
    config_service = ConfigService(
        persistence_service=persistence_service,
        credential_service=credential_service,
        portfolio_service=portfolio_service
        # notification_service is not passed here initially
    )
    
    # Then initialize NotificationService, providing ConfigService to it
    notification_service = NotificationService(
        credential_service=credential_service, 
        persistence_service=persistence_service,
        config_service=config_service  # Pass ConfigService here
    )

    # Now, inject NotificationService back into ConfigService
    config_service.set_notification_service(notification_service)

    # Inicializar OrderExecutionService y PaperOrderExecutionService
    order_execution_service = OrderExecutionService(binance_adapter=binance_adapter)
    paper_order_execution_service = PaperOrderExecutionService()

    # Inicializar TradingEngineService
    trading_engine_service = TradingEngineService(
        config_service=config_service,
        order_execution_service=order_execution_service,
        paper_order_execution_service=paper_order_execution_service,
        credential_service=credential_service,
        market_data_service=market_data_service,
        portfolio_service=portfolio_service,
        persistence_service=persistence_service,
        notification_service=notification_service,
        binance_adapter=binance_adapter
    )

    # Inicializar MobulaAdapter
    mobula_adapter = MobulaAdapter()

    # Inicializar LLM Provider (ejemplo con ChatGoogleGenerativeAI)
    # Asegúrate de que GOOGLE_API_KEY esté configurado en el entorno o settings
    try:
        llm_provider = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7) # Ajusta el modelo y parámetros según necesidad
        logger.info("LLM Provider (ChatGoogleGenerativeAI) inicializado.")
    except Exception as e:
        logger.error(f"Error al inicializar LLM Provider: {e}", exc_info=True)
        # Considerar si la aplicación debe detenerse si el LLM no se puede inicializar
        llm_provider = None # Asegurar que es None si falla

    # Inicializar AIOrchestratorService
    if persistence_service and credential_service and config_service and llm_provider and mobula_adapter and binance_adapter and notification_service:
        ai_orchestrator_service = AIOrchestratorService(
            config_service=config_service,
            credential_service=credential_service,
            persistence_service=persistence_service,
            llm_provider=llm_provider,
            mobula_adapter=mobula_adapter,
            binance_adapter=binance_adapter,
            notification_service=notification_service
        )
        logger.info("AIOrchestratorService inicializado.")
        # Llamar a async_init para cargar herramientas MCP
        await ai_orchestrator_service.async_init(user_id=str(FIXED_USER_ID))
        logger.info(f"AIOrchestratorService async_init completado para el usuario {FIXED_USER_ID}.")
    else:
        logger.error("No se pudo inicializar AIOrchestratorService debido a dependencias faltantes.")


    logger.info("Todos los servicios principales inicializados.")

    # Cargar la configuración del usuario al inicio
    try:
        # Ensure user_id is passed as string, as get_user_configuration expects Optional[str]
        user_configuration = await config_service.get_user_configuration(user_id_str=str(FIXED_USER_ID)) 
        logger.info(f"Configuración de usuario cargada exitosamente para {FIXED_USER_ID}.")
    except Exception as e:
        logger.error(f"Error al cargar la configuración de usuario al inicio: {e}", exc_info=True)
        user_configuration = config_service.get_default_configuration(user_id=FIXED_USER_ID) 
        logger.warning("Se utilizará la configuración por defecto debido a un error de carga.")

    # Iniciar el monitor de trading real si está habilitado en la configuración del usuario
    if trading_engine_service and user_configuration and user_configuration.realTradingSettings:
        if user_configuration.realTradingSettings.real_trading_mode_active:
            logger.info("Real Trading Mode is active. Starting real trading monitor.")
            await trading_engine_service.start_real_trading_monitor()
        else:
            logger.info("Real Trading Mode is not active. Real trading monitor will not be started.")
    elif not trading_engine_service:
        logger.error("TradingEngineService not initialized. Cannot start real trading monitor.")
    elif not user_configuration or not user_configuration.realTradingSettings:
        logger.error("User configuration or realTradingSettings not available. Cannot determine if real trading monitor should start.")


    # Verificar si la URL de la base de datos está configurada antes de intentar la verificación de credenciales
    if settings.DATABASE_URL:
        # Intentar verificar las credenciales de Telegram al inicio
        try:
            telegram_credential = await credential_service.get_credential(
                user_id=FIXED_USER_ID,
                service_name=ServiceName.TELEGRAM_BOT,
                credential_label="default_telegram_bot"
            )
            if telegram_credential:
                logger.info(f"Credenciales de Telegram encontradas para el usuario {FIXED_USER_ID}. Iniciando verificación...")
                # Usar el método verify_credential del CredentialService, pasándole el notification_service
                is_telegram_verified = await credential_service.verify_credential(
                    credential=telegram_credential,
                    notification_service=notification_service
                )
                if is_telegram_verified:
                    logger.info("Verificación inicial de Telegram completada con éxito.")
                else:
                    logger.warning("La verificación inicial de Telegram falló. Revise las credenciales.")
            else:
                logger.info(f"No se encontraron credenciales de Telegram para el usuario {FIXED_USER_ID}. Omite la verificación inicial.")
        except Exception as e:
            logger.error(f"Error durante la verificación inicial de Telegram: {e}", exc_info=True)
    else:
        logger.warning("DATABASE_URL no está configurada. Se omitirá la verificación inicial de credenciales de Telegram.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento que se ejecuta al apagar la aplicación FastAPI.
    Cierra recursos.
    """
    logger.info("Apagando UltiBot Backend...")
    if notification_service:
        await notification_service.close()
    if binance_adapter: # Cerrar BinanceAdapter
        await binance_adapter.close()
    if persistence_service: # Cerrar PersistenceService
        await persistence_service.disconnect()
    logger.info("UltiBot Backend apagado.")


@app.get("/")
async def read_root():
    return {"message": "Welcome to UltiBot Backend"}

# Aquí se incluirán los routers de api/v1/endpoints
from src.ultibot_backend.api.v1.endpoints import telegram_status, binance_status, config, notifications, reports, portfolio
app.include_router(telegram_status.router, prefix="/api/v1", tags=["telegram"]) # Añadir tags
app.include_router(binance_status.router, prefix="/api/v1", tags=["binance"]) # Incluir el router de Binance
app.include_router(config.router, prefix="/api/v1", tags=["config"]) # Incluir el router de configuración
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"]) # Incluir el router de notificaciones
app.include_router(reports.router, prefix="/api/v1", tags=["reports"]) # Incluir el router de reportes
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"]) # Incluir el router de portafolio

# Importar y incluir el router de oportunidades por separado para depuración
from src.ultibot_backend.api.v1.endpoints import opportunities
app.include_router(opportunities.router) # Incluir el router de oportunidades sin prefix ni tags
