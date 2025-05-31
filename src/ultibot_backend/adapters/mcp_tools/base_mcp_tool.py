from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from ultibot_backend.services.credential_service import CredentialService
from ultibot_backend.services.config_service import UserConfiguration


class BaseMCPToolSchema(BaseModel):
    """
    Esquema base para los argumentos de las herramientas MCP.
    Las herramientas específicas pueden heredar de este y añadir sus propios campos.
    """
    pass


class BaseMCPTool(BaseTool, ABC):
    """
    Clase base abstracta para adaptadores de herramientas MCP.

    Esta clase proporciona una estructura común para interactuar con
    servidores MCP, integrándose con LangChain como una herramienta.
    Las implementaciones específicas para cada tipo de MCP deben heredar
    de esta clase.
    """
    # name: str # Eliminado para evitar conflicto con BaseTool.name
    # description: str # Eliminado para evitar conflicto con BaseTool.description
    args_schema: Optional[Type[BaseModel]] = BaseMCPToolSchema
    # return_direct: bool = False # Por defecto, las herramientas devuelven su salida para ser usada por el LLM.

    # Atributos específicos de MCP (ahora son parte de los argumentos del constructor de BaseTool)
    mcp_id: str = Field(..., description="Identificador único del servidor MCP.")
    mcp_url: str = Field(..., description="URL del servidor MCP.")
    mcp_type: str = Field(..., description="Tipo de servidor MCP (ej. 'trending_signal', 'sentiment_analysis').")
    is_enabled: bool = Field(True, description="Indica si la herramienta MCP está habilitada.")
    credential_id: Optional[str] = Field(None, description="ID de la credencial asociada, si el MCP la requiere.")

    # Servicios inyectados
    credential_service: CredentialService = Field(..., exclude=True) # Excluir de la serialización de la herramienta

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, mcp_config: Dict[str, Any], credential_service: CredentialService, **kwargs):
        """
        Inicializa la herramienta MCP.

        Args:
            mcp_config: Configuración del servidor MCP (ej. de UserConfiguration.mcpServerPreferences).
            credential_service: Instancia del servicio de credenciales.
        """
        super().__init__(
            name=mcp_config.get("id"), # Usar el id del MCP como nombre de la herramienta
            description=mcp_config.get("description", f"Herramienta para interactuar con el MCP {mcp_config.get('id')} en {mcp_config.get('url')}."),
            mcp_id=mcp_config.get("id"),
            mcp_url=mcp_config.get("url"),
            mcp_type=mcp_config.get("type"),
            is_enabled=mcp_config.get("isEnabled", True),
            credential_id=mcp_config.get("credentialId"),
            credential_service=credential_service,
            **kwargs
        )

    @abstractmethod
    def _run(self, *args: Any, **kwargs: Any) -> str:
        """
        Ejecuta la lógica principal de la herramienta MCP de forma síncrona.
        Este método debe ser implementado por las subclases.
        """
        raise NotImplementedError("Las herramientas MCP deben implementar el método _run.")

    @abstractmethod
    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        """
        Ejecuta la lógica principal de la herramienta MCP de forma asíncrona.
        Este método debe ser implementado por las subclases para operaciones asíncronas.
        """
        raise NotImplementedError("Las herramientas MCP deben implementar el método _arun para uso asíncrono.")

    def to_langchain_tool(self) -> BaseTool:
        """
        Convierte esta instancia de BaseMCPTool en una instancia de LangChain BaseTool.
        Esto es necesario porque BaseMCPTool hereda de BaseModel y BaseTool,
        y LangChain espera una instancia de BaseTool para sus agentes.
        """
        # LangChain BaseTool ya tiene name, description, args_schema, _run, _arun
        # Simplemente devolvemos self, ya que BaseMCPTool ya es una BaseTool.
        # Sin embargo, si BaseMCPTool tuviera atributos adicionales que no son parte de BaseTool
        # y que no queremos exponer, o si la inicialización de BaseTool fuera diferente,
        # podríamos crear una clase wrapper aquí.
        # Para este caso, como BaseMCPTool ya hereda de BaseTool y maneja sus atributos,
        # simplemente devolvemos la instancia.
        return self

    async def get_credentials_async(self) -> Optional[Dict[str, Optional[str]]]:
        """
        Obtiene las credenciales para el MCP de forma asíncrona si se ha configurado un credential_id.
        Este método está diseñado para ser llamado desde _arun.
        """
        from uuid import UUID # Importar UUID aquí para evitar dependencia a nivel de módulo si no es necesaria siempre
        import logging # Importar logging
        logger = logging.getLogger(__name__)

        if self.credential_id:
            try:
                credential_uuid = UUID(self.credential_id)
                # Llamada asíncrona al servicio de credenciales
                creds_model = await self.credential_service.get_decrypted_credential_by_id(credential_uuid)
                
                if creds_model:
                    # Los campos en APICredential devueltos por get_decrypted_credential_by_id
                    # llamados encrypted_api_key, etc., contienen los datos desencriptados.
                    # Es importante que el contrato de get_decrypted_credential_by_id sea claro al respecto.
                    api_key = creds_model.encrypted_api_key # Contiene la API key desencriptada
                    api_secret = creds_model.encrypted_api_secret # Contiene el API secret desencriptado
                    
                    # other_details_str = creds_model.encrypted_other_details # Contiene JSON str desencriptado
                    # other_details = json.loads(other_details_str) if other_details_str else None
                    
                    return {"api_key": api_key, "api_secret": api_secret}
                else:
                    logger.warning(f"No se encontraron credenciales para el ID: {self.credential_id}")
                    return None
            except ValueError:
                logger.error(f"El credential_id '{self.credential_id}' no es un UUID válido.")
                return None
            except Exception as e:
                logger.error(f"Error al obtener credenciales para {self.mcp_id} (cred_id: {self.credential_id}): {e}", exc_info=True)
                return None
        return None

    @classmethod
    def from_user_config_mcp(
        cls,
        mcp_server_preference: Dict[str, Any], # Debería ser un modelo Pydantic UserConfiguration.MCPServerPreference
        credential_service: CredentialService,
        # config_service: ConfigService # Podría ser necesario para obtener más detalles
    ) -> "BaseMCPTool":
        """
        Método factoría para crear una instancia de herramienta MCP
        a partir de la configuración del usuario.
        """
        # Aquí se podría tener lógica para instanciar diferentes subclases de BaseMCPTool
        # basadas en mcp_server_preference.type.
        # Por ahora, asumimos que esta clase base (o una subclase directa) se instancia.
        # Este método probablemente necesitará ser sobreescrito o especializado en un gestor.
        
        # Ejemplo simple: si se quisiera una clase específica por tipo
        # if mcp_server_preference.get("type") == "some_specific_type":
        #     return SpecificMCPTool(mcp_config=mcp_server_preference, credential_service=credential_service)
        
        # Para este ejemplo base, instanciamos directamente, pero esto fallará porque es abstracta.
        # La idea es que una clase concreta llame a super() o este método sea usado por un factory.
        # Por lo tanto, este método es más un placeholder conceptual aquí.
        raise NotImplementedError(
            "Este método factoría debe ser implementado por una clase concreta o un gestor de herramientas MCP."
        )
