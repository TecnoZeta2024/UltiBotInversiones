"""
MCP Tool Hub - Hub centralizado de herramientas MCP.

Este servicio gestiona el registro, descubrimiento y ejecución de herramientas MCP
(Model Context Protocol), proporcionando una interfaz unificada para el AI Orchestrator.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from uuid import UUID, uuid4

from ..domain_models.ai_models import (
    ToolAction,
    ToolResult,
    AIRequestPriority,
)
from ..exceptions import (
    ToolNotFoundError,
    ToolExecutionError,
    InvalidParameterError,
    TimeoutError,
)
from ..ports import (
    ILoggingPort,
    IEventPublisher,
)

logger = logging.getLogger(__name__)

class ToolDescriptor:
    """
    Descriptor de una herramienta MCP.
    
    Contiene metadatos sobre la herramienta incluyendo nombre, descripción,
    parámetros esperados y configuración.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters_schema: Dict[str, Any],
        category: str = "general",
        timeout_seconds: int = 30,
        requires_credentials: bool = False,
        version: str = "1.0.0"
    ):
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema
        self.category = category
        self.timeout_seconds = timeout_seconds
        self.requires_credentials = requires_credentials
        self.version = version
        self.created_at = datetime.utcnow()
    
    def dict(self) -> Dict[str, Any]:
        """Convierte el descriptor a diccionario."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters_schema": self.parameters_schema,
            "category": self.category,
            "timeout_seconds": self.timeout_seconds,
            "requires_credentials": self.requires_credentials,
            "version": self.version,
            "created_at": self.created_at.isoformat()
        }

class BaseMCPAdapter:
    """
    Clase base abstracta para adaptadores MCP.
    
    Todos los adaptadores de herramientas MCP deben heredar de esta clase
    e implementar los métodos abstractos.
    """
    
    def __init__(self, name: str, description: str, category: str = "general"):
        self.name = name
        self.description = description
        self.category = category
        self._is_initialized = False
        self._last_execution_time: Optional[datetime] = None
        self._execution_count = 0
        self._error_count = 0
    
    async def initialize(self) -> None:
        """
        Inicializa el adaptador.
        
        Este método debe ser llamado antes de usar el adaptador.
        Puede ser overridden por subclases para setup específico.
        """
        self._is_initialized = True
        logger.info(f"MCP Adapter '{self.name}' initialized successfully")
    
    async def get_tool_descriptor(self) -> ToolDescriptor:
        """
        Obtiene el descriptor de la herramienta.
        
        Returns:
            ToolDescriptor: Descriptor completo de la herramienta
        """
        if not self._is_initialized:
            await self.initialize()
        
        return ToolDescriptor(
            name=self.name,
            description=self.description,
            parameters_schema=self._get_parameters_schema(),
            category=self.category,
            timeout_seconds=self._get_timeout_seconds(),
            requires_credentials=self._requires_credentials()
        )
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la herramienta con los parámetros dados.
        
        Args:
            parameters: Parámetros para la ejecución
            
        Returns:
            dict: Resultado de la ejecución
            
        Raises:
            ToolExecutionError: Error en la ejecución
            InvalidParameterError: Parámetros inválidos
        """
        if not self._is_initialized:
            await self.initialize()
        
        # Validar parámetros
        self._validate_parameters(parameters)
        
        start_time = time.time()
        self._last_execution_time = datetime.utcnow()
        
        try:
            # Pre-ejecución
            await self._pre_execute_hook(parameters)
            
            # Ejecución principal
            result = await self._execute_implementation(parameters)
            
            # Post-ejecución
            await self._post_execute_hook(parameters, result)
            
            self._execution_count += 1
            execution_time = (time.time() - start_time) * 1000
            
            logger.debug(
                f"Tool '{self.name}' executed successfully in {execution_time:.2f}ms"
            )
            
            return result
            
        except Exception as e:
            self._error_count += 1
            execution_time = (time.time() - start_time) * 1000
            
            logger.error(
                f"Tool '{self.name}' execution failed after {execution_time:.2f}ms: {str(e)}"
            )
            
            raise ToolExecutionError(f"Tool '{self.name}' execution failed: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del adaptador.
        
        Returns:
            dict: Estado del adaptador
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "is_initialized": self._is_initialized,
            "execution_count": self._execution_count,
            "error_count": self._error_count,
            "last_execution": self._last_execution_time.isoformat() if self._last_execution_time else None,
            "success_rate": (
                (self._execution_count - self._error_count) / self._execution_count
                if self._execution_count > 0 else 0.0
            )
        }
    
    # Métodos abstractos que deben ser implementados por subclases
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        Retorna el schema de parámetros para la herramienta.
        
        Returns:
            dict: Schema JSON de parámetros
        """
        raise NotImplementedError("Subclasses must implement _get_parameters_schema")
    
    def _get_timeout_seconds(self) -> int:
        """
        Retorna el timeout en segundos para la herramienta.
        
        Returns:
            int: Timeout en segundos
        """
        return 30  # Default timeout
    
    def _requires_credentials(self) -> bool:
        """
        Indica si la herramienta requiere credenciales.
        
        Returns:
            bool: True si requiere credenciales
        """
        return False  # Default: no credentials required
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Valida los parámetros de entrada.
        
        Args:
            parameters: Parámetros a validar
            
        Raises:
            InvalidParameterError: Si los parámetros son inválidos
        """
        # Implementación básica - puede ser overridden por subclases
        schema = self._get_parameters_schema()
        required_params = schema.get("required", [])
        
        for param in required_params:
            if param not in parameters:
                raise InvalidParameterError(
                    f"Missing required parameter '{param}' for tool '{self.name}'"
                )
    
    async def _pre_execute_hook(self, parameters: Dict[str, Any]) -> None:
        """
        Hook ejecutado antes de la ejecución principal.
        
        Args:
            parameters: Parámetros de ejecución
        """
        pass  # Override in subclasses if needed
    
    async def _post_execute_hook(
        self,
        parameters: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Hook ejecutado después de la ejecución principal.
        
        Args:
            parameters: Parámetros de ejecución
            result: Resultado de la ejecución
        """
        pass  # Override in subclasses if needed
    
    async def _execute_implementation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementación específica de la ejecución de la herramienta.
        
        Este método debe ser implementado por cada adaptador específico.
        
        Args:
            parameters: Parámetros de ejecución
            
        Returns:
            dict: Resultado de la ejecución
        """
        raise NotImplementedError("Subclasses must implement _execute_implementation")

class MCPToolHub:
    """
    Hub centralizado para gestión de herramientas MCP.
    
    Proporciona registro dinámico, descubrimiento y ejecución de herramientas MCP
    con soporte para categorización, timeouts y logging.
    """
    
    def __init__(
        self,
        logging_port: Optional[ILoggingPort] = None,
        event_publisher: Optional[IEventPublisher] = None,
        max_concurrent_executions: int = 5
    ):
        """
        Inicializa el MCP Tool Hub.
        
        Args:
            logging_port: Puerto de logging
            event_publisher: Publicador de eventos
            max_concurrent_executions: Máximo de ejecuciones concurrentes
        """
        self._tools: Dict[str, BaseMCPAdapter] = {}
        self._categories: Dict[str, List[str]] = {}
        self._logging_port = logging_port
        self._event_publisher = event_publisher
        self._max_concurrent_executions = max_concurrent_executions
        self._execution_semaphore = asyncio.Semaphore(max_concurrent_executions)
        
        # Métricas
        self._total_executions = 0
        self._successful_executions = 0
        self._failed_executions = 0
        self._start_time = datetime.utcnow()
    
    def register_tool(self, adapter: BaseMCPAdapter) -> None:
        """
        Registra una herramienta MCP en el hub.
        
        Args:
            adapter: Adaptador de la herramienta a registrar
            
        Raises:
            ValueError: Si ya existe una herramienta con el mismo nombre
        """
        if adapter.name in self._tools:
            raise ValueError(f"Tool '{adapter.name}' is already registered")
        
        self._tools[adapter.name] = adapter
        
        # Actualizar categorías
        category = adapter.category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(adapter.name)
        
        logger.info(f"Registered MCP tool '{adapter.name}' in category '{category}'")
    
    def unregister_tool(self, tool_name: str) -> bool:
        """
        Desregistra una herramienta del hub.
        
        Args:
            tool_name: Nombre de la herramienta a desregistrar
            
        Returns:
            bool: True si se desregistró exitosamente
        """
        if tool_name not in self._tools:
            return False
        
        adapter = self._tools[tool_name]
        category = adapter.category
        
        # Remover de herramientas
        del self._tools[tool_name]
        
        # Remover de categorías
        if category in self._categories:
            self._categories[category].remove(tool_name)
            if not self._categories[category]:
                del self._categories[category]
        
        logger.info(f"Unregistered MCP tool '{tool_name}'")
        return True
    
    async def list_available_tools(self, category: Optional[str] = None) -> List[ToolDescriptor]:
        """
        Lista todas las herramientas disponibles.
        
        Args:
            category: Filtrar por categoría (opcional)
            
        Returns:
            List[ToolDescriptor]: Lista de descriptores de herramientas
        """
        tools = []
        
        for tool_name, adapter in self._tools.items():
            if category is None or adapter.category == category:
                try:
                    descriptor = await adapter.get_tool_descriptor()
                    tools.append(descriptor)
                except Exception as e:
                    if self._logging_port:
                        await self._logging_port.log_warning(
                            f"Failed to get descriptor for tool '{tool_name}': {str(e)}"
                        )
        
        return tools
    
    def list_categories(self) -> List[str]:
        """
        Lista todas las categorías disponibles.
        
        Returns:
            List[str]: Lista de categorías
        """
        return list(self._categories.keys())
    
    def get_tools_by_category(self, category: str) -> List[str]:
        """
        Obtiene herramientas por categoría.
        
        Args:
            category: Nombre de la categoría
            
        Returns:
            List[str]: Lista de nombres de herramientas en la categoría
        """
        return self._categories.get(category, [])
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta una herramienta MCP específica.
        
        Args:
            tool_name: Nombre de la herramienta
            parameters: Parámetros para la ejecución
            timeout_override: Timeout personalizado (opcional)
            
        Returns:
            dict: Resultado de la ejecución
            
        Raises:
            ToolNotFoundError: Si la herramienta no existe
            ToolExecutionError: Error en la ejecución
            TimeoutError: Timeout en la ejecución
        """
        if tool_name not in self._tools:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found")
        
        adapter = self._tools[tool_name]
        
        # Obtener timeout
        descriptor = await adapter.get_tool_descriptor()
        timeout = timeout_override or descriptor.timeout_seconds
        
        async with self._execution_semaphore:
            self._total_executions += 1
            
            if self._logging_port:
                await self._logging_port.log_debug(
                    f"Executing tool '{tool_name}' with timeout {timeout}s",
                    extra={
                        "tool_name": tool_name,
                        "parameters": parameters,
                        "timeout": timeout
                    }
                )
            
            try:
                # Ejecutar con timeout
                result = await asyncio.wait_for(
                    adapter.execute(parameters),
                    timeout=timeout
                )
                
                self._successful_executions += 1
                
                if self._logging_port:
                    await self._logging_port.log_info(
                        f"Tool '{tool_name}' executed successfully",
                        extra={
                            "tool_name": tool_name,
                            "execution_count": self._total_executions
                        }
                    )
                
                return result
                
            except asyncio.TimeoutError:
                self._failed_executions += 1
                
                if self._logging_port:
                    await self._logging_port.log_error(
                        f"Tool '{tool_name}' execution timed out after {timeout}s"
                    )
                
                raise TimeoutError(f"Tool '{tool_name}' timed out after {timeout}s")
                
            except Exception as e:
                self._failed_executions += 1
                
                if self._logging_port:
                    await self._logging_port.log_error(
                        f"Tool '{tool_name}' execution failed: {str(e)}",
                        extra={
                            "tool_name": tool_name,
                            "error": str(e)
                        }
                    )
                
                raise
    
    def get_tool_status(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de una herramienta específica.
        
        Args:
            tool_name: Nombre de la herramienta
            
        Returns:
            dict: Estado de la herramienta o None si no existe
        """
        if tool_name not in self._tools:
            return None
        
        return self._tools[tool_name].get_status()
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado del hub de herramientas.
        
        Returns:
            dict: Estado completo del hub
        """
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        return {
            "hub_status": {
                "total_tools": len(self._tools),
                "categories": len(self._categories),
                "uptime_seconds": uptime,
                "healthy": len(self._tools) > 0
            },
            "execution_metrics": {
                "total_executions": self._total_executions,
                "successful_executions": self._successful_executions,
                "failed_executions": self._failed_executions,
                "success_rate": (
                    self._successful_executions / self._total_executions
                    if self._total_executions > 0 else 0.0
                ),
                "executions_per_minute": (
                    (self._total_executions * 60) / uptime
                    if uptime > 0 else 0.0
                )
            },
            "categories": {
                category: len(tools)
                for category, tools in self._categories.items()
            },
            "tools": [
                {
                    "name": name,
                    "category": adapter.category,
                    "status": adapter.get_status()
                }
                for name, adapter in self._tools.items()
            ]
        }
    
    async def health_check(self) -> bool:
        """
        Verifica la salud del hub y todas las herramientas.
        
        Returns:
            bool: True si el hub está saludable
        """
        if not self._tools:
            return False
        
        # Verificar que al menos el 80% de las herramientas estén funcionando
        healthy_tools = 0
        
        for tool_name, adapter in self._tools.items():
            try:
                status = adapter.get_status()
                if status["success_rate"] >= 0.8:
                    healthy_tools += 1
            except Exception:
                continue
        
        health_ratio = healthy_tools / len(self._tools)
        return health_ratio >= 0.8
