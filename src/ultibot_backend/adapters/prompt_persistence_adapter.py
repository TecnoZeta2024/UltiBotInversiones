"""
Adaptador de Persistencia para Prompts - Implementa IPromptRepository
Parte de la capa de adaptadores - puede usar dependencias externas
"""

from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import json
import logging
from datetime import timezone # ADDED timezone

from supabase import create_client, Client
from ..core.ports import IPromptRepository
from ..core.domain_models.prompt_models import PromptTemplate, PromptVersion
from ..core.exceptions import PromptNotFoundError, PersistenceError

logger = logging.getLogger(__name__)

class PromptPersistenceAdapter(IPromptRepository):
    """
    Adaptador para persistencia de prompts en Supabase
    
    Implementa la interfaz IPromptRepository definida en el núcleo
    """
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Inicializa el adaptador con credenciales de Supabase
        
        Args:
            supabase_url: URL del proyecto Supabase
            supabase_key: API key de Supabase
        """
        self._client: Client = create_client(supabase_url, supabase_key)
        self._table_name = "ai_prompts"
        self._view_name = "active_prompts"
        
        # Cache de conexión
        self._connection_verified = False
        self._last_health_check = None
    
    async def get_latest_prompt(self, name: str) -> Optional[PromptTemplate]:
        """
        Obtiene la versión más reciente y activa de un prompt
        
        Args:
            name: Nombre del prompt
            
        Returns:
            PromptTemplate o None si no existe
        """
        try:
            await self._ensure_connection()
            
            response = self._client.table(self._view_name)\
                .select("*")\
                .eq("name", name)\
                .order("version", desc=True)\
                .limit(1)\
                .execute()
            
            if not response.data:
                logger.debug(f"Prompt '{name}' no encontrado")
                return None
            
            prompt_data = response.data[0]
            return self._map_to_domain_model(prompt_data)
            
        except Exception as e:
            logger.error(f"Error obteniendo prompt '{name}': {str(e)}")
            raise PersistenceError(f"Error obteniendo prompt '{name}': {str(e)}")
    
    async def get_prompt_version(self, name: str, version: int) -> Optional[PromptTemplate]:
        """
        Obtiene una versión específica de un prompt
        
        Args:
            name: Nombre del prompt
            version: Número de versión
            
        Returns:
            PromptTemplate o None si no existe
        """
        try:
            await self._ensure_connection()
            
            response = self._client.table(self._table_name)\
                .select("*")\
                .eq("name", name)\
                .eq("version", version)\
                .limit(1)\
                .execute()
            
            if not response.data:
                return None
            
            prompt_data = response.data[0]
            return self._map_to_domain_model(prompt_data)
            
        except Exception as e:
            logger.error(f"Error obteniendo prompt '{name}' v{version}: {str(e)}")
            raise PersistenceError(f"Error obteniendo prompt '{name}' v{version}: {str(e)}")
    
    async def list_prompts(
        self, 
        category: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[PromptTemplate]:
        """
        Lista prompts disponibles, opcionalmente filtrados por categoría
        
        Args:
            category: Categoría opcional para filtrar
            include_inactive: Si incluir prompts inactivos
            
        Returns:
            Lista de PromptTemplate
        """
        try:
            await self._ensure_connection()
            
            # Usar vista para activos o tabla completa para incluir inactivos
            table_ref = self._view_name if not include_inactive else self._table_name
            
            query = self._client.table(table_ref).select("*")
            
            if category:
                query = query.eq("category", category)
            
            if include_inactive:
                # Si usando tabla completa, obtener solo versiones más recientes
                query = query.order("name").order("version", desc=True)
            else:
                query = query.order("name")
            
            response = query.execute()
            
            prompts = []
            seen_names = set()
            
            for prompt_data in response.data:
                # Si incluye inactivos, solo tomar la versión más reciente de cada prompt
                if include_inactive and prompt_data["name"] in seen_names:
                    continue
                
                prompts.append(self._map_to_domain_model(prompt_data))
                seen_names.add(prompt_data["name"])
            
            logger.debug(f"Listados {len(prompts)} prompts (categoría: {category})")
            return prompts
            
        except Exception as e:
            logger.error(f"Error listando prompts: {str(e)}")
            raise PersistenceError(f"Error listando prompts: {str(e)}")
    
    async def create_prompt_version(
        self,
        name: str,
        template: str,
        variables: Dict[str, str],
        description: Optional[str] = None,
        category: str = "general",
        creator: str = "system"
    ) -> PromptTemplate:
        """
        Crea una nueva versión de un prompt
        
        Args:
            name: Nombre del prompt
            template: Contenido del template
            variables: Variables esperadas
            description: Descripción opcional
            category: Categoría del prompt
            creator: Creador de la versión
            
        Returns:
            PromptTemplate con la nueva versión creada
        """
        try:
            await self._ensure_connection()
            
            # Usar función stored procedure para manejo atómico de versiones
            response = self._client.rpc("create_prompt_version", {
                "prompt_name": name,
                "new_template": template,
                "new_variables": json.dumps(variables),
                "new_description": description,
                "new_category": category,
                "creator": creator
            }).execute()
            
            if not response.data:
                raise PersistenceError(f"Error creando versión de prompt '{name}'")
            
            prompt_data = response.data
            logger.info(f"Creada nueva versión de prompt '{name}': v{prompt_data['version']}")
            
            return self._map_to_domain_model(prompt_data)
            
        except Exception as e:
            logger.error(f"Error creando versión de prompt '{name}': {str(e)}")
            raise PersistenceError(f"Error creando versión de prompt '{name}': {str(e)}")
    
    async def update_prompt_status(self, name: str, version: int, is_active: bool) -> bool:
        """
        Actualiza el estado activo/inactivo de una versión específica
        
        Args:
            name: Nombre del prompt
            version: Versión específica
            is_active: Nuevo estado
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            await self._ensure_connection()
            
            response = self._client.table(self._table_name)\
                .update({"is_active": is_active, "updated_at": datetime.now(timezone.utc).isoformat()})\ # MODIFIED
                .eq("name", name)\
                .eq("version", version)\
                .execute()
            
            success = len(response.data) > 0
            
            if success:
                logger.info(f"Prompt '{name}' v{version} {'activado' if is_active else 'desactivado'}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error actualizando estado de prompt '{name}' v{version}: {str(e)}")
            raise PersistenceError(f"Error actualizando estado de prompt '{name}' v{version}: {str(e)}")
    
    async def get_prompt_versions(self, name: str) -> List[PromptVersion]:
        """
        Obtiene todas las versiones de un prompt
        
        Args:
            name: Nombre del prompt
            
        Returns:
            Lista de PromptVersion ordenadas por versión descendente
        """
        try:
            await self._ensure_connection()
            
            response = self._client.table(self._table_name)\
                .select("id, version, description, is_active, created_at, created_by")\
                .eq("name", name)\
                .order("version", desc=True)\
                .execute()
            
            versions = []
            for version_data in response.data:
                versions.append(PromptVersion(
                    id=version_data["id"],
                    prompt_name=name,
                    version=version_data["version"],
                    description=version_data.get("description"),
                    is_active=version_data["is_active"],
                    created_at=datetime.fromisoformat(version_data["created_at"].replace("Z", "+00:00")),
                    created_by=version_data["created_by"]
                ))
            
            logger.debug(f"Obtenidas {len(versions)} versiones para prompt '{name}'")
            return versions
            
        except Exception as e:
            logger.error(f"Error obteniendo versiones de prompt '{name}': {str(e)}")
            raise PersistenceError(f"Error obteniendo versiones de prompt '{name}': {str(e)}")
    
    async def delete_prompt_version(self, name: str, version: int) -> bool:
        """
        Elimina una versión específica de un prompt (soft delete - marca como inactivo)
        
        Args:
            name: Nombre del prompt
            version: Versión a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            # Por seguridad, hacer soft delete marcando como inactivo
            return await self.update_prompt_status(name, version, False)
            
        except Exception as e:
            logger.error(f"Error eliminando prompt '{name}' v{version}: {str(e)}")
            raise PersistenceError(f"Error eliminando prompt '{name}' v{version}: {str(e)}")
    
    async def search_prompts(
        self, 
        query: str, 
        category: Optional[str] = None
    ) -> List[PromptTemplate]:
        """
        Busca prompts por contenido o descripción
        
        Args:
            query: Término de búsqueda
            category: Categoría opcional para filtrar
            
        Returns:
            Lista de PromptTemplate que coinciden
        """
        try:
            await self._ensure_connection()
            
            # Usar búsqueda de texto completo en PostgreSQL
            db_query = self._client.table(self._view_name)\
                .select("*")\
                .or_(f"template.ilike.%{query}%,description.ilike.%{query}%,name.ilike.%{query}%")
            
            if category:
                db_query = db_query.eq("category", category)
            
            response = db_query.execute()
            
            prompts = [self._map_to_domain_model(data) for data in response.data]
            
            logger.debug(f"Búsqueda '{query}' retornó {len(prompts)} prompts")
            return prompts
            
        except Exception as e:
            logger.error(f"Error buscando prompts con query '{query}': {str(e)}")
            raise PersistenceError(f"Error buscando prompts: {str(e)}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de salud de la conexión con la base de datos
        
        Returns:
            Diccionario con métricas de salud
        """
        try:
            start_time = datetime.now(timezone.utc) # MODIFIED
            
            # Test básico de conectividad
            response = self._client.table(self._table_name)\
                .select("count", count="exact")\
                .limit(1)\
                .execute()
            
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000 # MODIFIED
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "total_prompts": response.count if hasattr(response, 'count') else 0,
                "connection_verified": self._connection_verified,
                "last_check": datetime.now(timezone.utc).isoformat() # MODIFIED
            }
            
        except Exception as e:
            logger.error(f"Health check falló: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection_verified": False,
                "last_check": datetime.now(timezone.utc).isoformat() # MODIFIED
            }
    
    # === Métodos privados ===
    
    async def _ensure_connection(self) -> None:
        """Verifica que la conexión esté disponible"""
        if not self._connection_verified:
            try:
                # Test simple de conectividad
                self._client.table(self._table_name).select("1").limit(1).execute()
                self._connection_verified = True
                self._last_health_check = datetime.now(timezone.utc) # MODIFIED
                logger.debug("Conexión con Supabase verificada")
            except Exception as e:
                logger.error(f"Error verificando conexión: {str(e)}")
                raise PersistenceError(f"Error de conexión con base de datos: {str(e)}")
    
    def _map_to_domain_model(self, data: Dict[str, Any]) -> PromptTemplate:
        """
        Mapea datos de la BD al modelo de dominio
        
        Args:
            data: Datos raw de la base de datos
            
        Returns:
            PromptTemplate con los datos mapeados
        """
        try:
            # Parsear variables JSON
            variables = {}
            if data.get("variables"):
                if isinstance(data["variables"], str):
                    variables = json.loads(data["variables"])
                else:
                    variables = data["variables"]
            
            # Parsear tags si existen
            tags = data.get("tags", [])
            if isinstance(tags, str):
                tags = json.loads(tags) if tags else []
            
            return PromptTemplate(
                id=data["id"],
                name=data["name"],
                version=data["version"],
                template=data["template"],
                variables=variables,
                description=data.get("description"),
                category=data.get("category", "general"),
                is_active=data.get("is_active", True),
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")) if data.get("updated_at") else None,
                created_by=data.get("created_by", "system"),
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Error mapeando datos a modelo de dominio: {str(e)}")
            logger.error(f"Datos problemáticos: {data}")
            raise PersistenceError(f"Error procesando datos de prompt: {str(e)}")
