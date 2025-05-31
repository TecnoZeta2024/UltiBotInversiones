import json
from typing import Any, Dict, Optional, Type
from uuid import UUID

from pydantic import BaseModel, Field

from .base_mcp_tool import BaseMCPTool, BaseMCPToolSchema
from ultibot_backend.services.credential_service import CredentialService


class MockMCPToolInputSchema(BaseMCPToolSchema):
    """
    Esquema de entrada para la herramienta MCP Mock.
    """
    query: str = Field(..., description="Consulta simulada para el MCP Mock.")
    parametro_opcional: Optional[str] = Field(None, description="Un parámetro opcional de ejemplo.")


class MockMCPTool(BaseMCPTool):
    """
    Herramienta MCP Mock de ejemplo.

    Esta herramienta simula la interacción con un servidor MCP.
    Devuelve una respuesta mockeada basada en la entrada.
    """
    name: str = "mock_mcp_signal_tool" # Nombre específico para esta herramienta mock
    description: str = (
        "Una herramienta MCP mock que simula la recepción de señales de trading. "
        "Útil para pruebas y desarrollo."
    )
    args_schema: Type[BaseModel] = MockMCPToolInputSchema

    # No es necesario sobreescribir __init__ si la inicialización de BaseMCPTool es suficiente.
    # Si se necesita lógica adicional, se puede sobreescribir:
    # def __init__(self, mcp_config: Dict[str, Any], credential_service: CredentialService, **kwargs):
    #     super().__init__(mcp_config, credential_service, **kwargs)
    #     # Lógica adicional de inicialización para MockMCPTool si es necesaria

    def _run(self, query: str, parametro_opcional: Optional[str] = None, **kwargs: Any) -> str:
        """
        Ejecuta la lógica síncrona de la herramienta MCP Mock.
        """
        # Simular la obtención de credenciales si es necesario
        # creds = self.get_credentials() # Esto actualmente lanza NotImplementedError
        # if self.credential_id and not creds:
        #     return json.dumps({"error": "Fallo al obtener credenciales simuladas."})

        # Lógica de simulación
        response_data = {
            "message": "Respuesta simulada del MockMCPTool",
            "query_recibida": query,
            "parametro_opcional_recibido": parametro_opcional,
            "mcp_id": self.mcp_id,
            "mcp_url": self.mcp_url,
            "simulated_signal": {
                "coin_pair": "BTC/USDT",
                "signal_type": "BUY",
                "confidence": 0.75,
                "source": self.name
            }
        }
        if self.credential_id:
            response_data["credential_id_usado"] = self.credential_id
            # response_data["simulated_api_key_usada"] = creds.get("api_key") if creds else "N/A"


        return json.dumps(response_data)

    async def _arun(self, query: str, parametro_opcional: Optional[str] = None, **kwargs: Any) -> str:
        """
        Ejecuta la lógica asíncrona de la herramienta MCP Mock.
        Para este mock, simplemente llama a la versión síncrona.
        """
        # En una implementación real, aquí iría código asíncrono (ej. httpx.get)
        # from asyncio import to_thread
        # return await to_thread(self._run, query=query, parametro_opcional=parametro_opcional, **kwargs)
        
        # Por ahora, para el mock, podemos devolver directamente una simulación.
        # creds_dict = None
        # if self.credential_id:
        #     try:
        #         # La llamada a get_credentials es síncrona y actualmente lanza error.
        #         # Para avanzar, la comentaremos en el mock.
        #         # creds = self.get_credentials() 
        #         # if creds:
        #         #    creds_dict = {"api_key": creds.get("api_key"), "api_secret": creds.get("api_secret")}
        #         pass
        #     except NotImplementedError:
        #         pass # Ignorar para el mock por ahora

        response_data = {
            "message": "Respuesta simulada ASÍNCRONA del MockMCPTool",
            "query_recibida": query,
            "parametro_opcional_recibido": parametro_opcional,
            "mcp_id": self.mcp_id,
            "mcp_url": self.mcp_url,
            "simulated_signal": {
                "coin_pair": "ETH/USDT",
                "signal_type": "STRONG_BUY",
                "confidence": 0.85,
                "source": self.name
            }
        }
        if self.credential_id:
            response_data["credential_id_usado"] = self.credential_id
            # if creds_dict:
            #     response_data["simulated_api_key_usada"] = creds_dict.get("api_key")

        return json.dumps(response_data)

    # El método factoría from_user_config_mcp de BaseMCPTool es un @classmethod
    # y está pensado para ser llamado en la clase que se quiere instanciar.
    # No es necesario re-implementarlo aquí a menos que la creación de MockMCPTool
    # sea diferente de lo que haría una llamada genérica a un constructor.
    # Si BaseMCPTool.from_user_config_mcp fuera un factory más genérico que
    # devuelve el tipo correcto, entonces no se necesitaría aquí.
    # Como está ahora, BaseMCPTool.from_user_config_mcp lanza NotImplementedError.
    # Una solución sería tener un registro de tipos de herramientas y un factory global.
    # Por ahora, para que esta herramienta sea usable, podemos añadir un método
    # constructor simple o asumir que se instancia directamente.

    # Para que sea instanciable directamente con la configuración:
    @classmethod
    def from_config(cls, mcp_config: Dict[str, Any], credential_service: CredentialService) -> "MockMCPTool":
        """
        Crea una instancia de MockMCPTool desde una configuración.
        """
        # Extraer los campos necesarios de mcp_config y pasarlos individualmente
        # al constructor de la clase base.
        mcp_id = mcp_config.get("mcp_id", "") # Proporcionar un valor por defecto de cadena vacía
        mcp_url = mcp_config.get("mcp_url", "") # Proporcionar un valor por defecto de cadena vacía
        mcp_type = mcp_config.get("mcp_type", "") # Proporcionar un valor por defecto de cadena vacía
        is_enabled = mcp_config.get("is_enabled", True)
        credential_id = mcp_config.get("credential_id") # Este puede ser None, ya que es Optional en BaseMCPTool

        return cls(
            mcp_id=mcp_id,
            mcp_url=mcp_url,
            mcp_type=mcp_type,
            is_enabled=is_enabled,
            credential_id=credential_id,
            credential_service=credential_service
        )
