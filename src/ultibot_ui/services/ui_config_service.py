from uuid import UUID
from src.ultibot_backend.services.config_service import ConfigService as BackendConfigService
from src.ultibot_backend.models.user_config import UserConfig # Assuming UserConfig is the model

class UIConfigService:
    def __init__(self, backend_config_service: BackendConfigService):
        self._backend_service = backend_config_service

    async def load_user_configuration(self, user_id: UUID) -> UserConfig:
        return await self._backend_service.load_user_configuration(user_id)

    async def save_user_configuration(self, user_id: UUID, config: UserConfig):
        await self._backend_service.save_user_configuration(user_id, config)
