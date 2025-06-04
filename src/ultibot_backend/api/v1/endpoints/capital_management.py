from fastapi import APIRouter, Depends, status
from src.ultibot_backend.dependencies import get_config_service
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.app_config import settings

router = APIRouter()

@router.get("/capital-management/status", status_code=status.HTTP_200_OK)
async def get_capital_management_status(config_service: ConfigService = Depends(get_config_service)):
    """
    Devuelve el estado de gestión de capital para el usuario actual.
    """
    user_id = str(settings.FIXED_USER_ID)
    config = await config_service.get_user_configuration(user_id)
    real_settings = getattr(config, 'realTradingSettings', None)
    risk_settings = getattr(config, 'riskProfileSettings', None)
    if not real_settings or not risk_settings:
        return {
            "error": "No se encontró configuración de gestión de capital para el usuario."
        }
    total_capital = getattr(real_settings, 'total_capital_usd', 10000.0)
    daily_limit = total_capital * getattr(risk_settings, 'dailyCapitalRiskPercentage', 0.5)
    committed_today = getattr(real_settings, 'daily_capital_risked_usd', 0.0)
    available = daily_limit - committed_today
    usage_pct = (committed_today / daily_limit) * 100 if daily_limit else 0.0
    return {
        "total_capital_usd": total_capital,
        "daily_capital_limit_usd": daily_limit,
        "daily_capital_committed_usd": committed_today,
        "available_for_new_trades_usd": available,
        "daily_usage_percentage": usage_pct,
        "high_risk_positions_count": getattr(real_settings, 'high_risk_positions_count', 0),
        "capital_alerts": []
    }
