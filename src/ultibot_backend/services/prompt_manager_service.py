"""
Módulo para el servicio de gestión de prompts.
"""
from typing import Dict, Any

from ..core.ports import IPromptManager, IPromptRepository
from ..core.exceptions import PromptNotFoundError

class PromptManagerService(IPromptManager):
    """
    Servicio para gestionar la lógica de negocio de los prompts.
    Implementa la interfaz IPromptManager y utiliza un repositorio para la persistencia.
    """

    def __init__(self, prompt_repository: IPromptRepository):
        """
        Inicializa el servicio con un repositorio de prompts.

        Args:
            prompt_repository: Un adaptador que implementa la interfaz IPromptRepository.
        """
        self._repository = prompt_repository

    async def get_prompt(self, name: str) -> str:
        """
        Obtiene la plantilla de la versión más reciente y activa de un prompt.

        Args:
            name: El nombre del prompt a buscar.

        Returns:
            La plantilla del prompt como un string.

        Raises:
            PromptNotFoundError: Si el prompt no se encuentra o no está activo.
        """
        prompt_template = await self._repository.get_latest_prompt(name)
        if not prompt_template:
            raise PromptNotFoundError(f"Prompt '{name}' no encontrado o no está activo.")
        return prompt_template.template

    async def render_prompt(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Renderiza una plantilla de prompt con las variables proporcionadas.

        Args:
            template: La plantilla del prompt (string).
            variables: Un diccionario con las variables a reemplazar.

        Returns:
            El prompt renderizado como un string.
        """
        rendered_prompt = template
        for key, value in variables.items():
            rendered_prompt = rendered_prompt.replace(f"{{{key}}}", str(value))
        return rendered_prompt
