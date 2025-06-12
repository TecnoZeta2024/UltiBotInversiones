"""
AI Studio ViewModel - Lógica de negocio para la gestión visual de prompts
Parte de la arquitectura MVVM - maneja estado y comandos de la UI
"""

from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import json
import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtWidgets import QMessageBox

from ..services.api_client import APIClient
from ..models import (
    PromptTemplateModel, 
    PromptVersionModel,
    PromptRenderResultModel,
    AIStudioStateModel
)

logger = logging.getLogger(__name__)

class AIStudioViewModel(QObject):
    """
    ViewModel para AI Studio - Gestión completa de prompts con UI
    
    Señales para binding reactivo con la Vista:
    - Cambios de estado
    - Actualizaciones de datos
    - Resultados de operaciones
    - Errores y notificaciones
    """
    
    # Señales de estado
    prompts_list_changed = pyqtSignal(list)  # Lista de prompts actualizada
    current_prompt_changed = pyqtSignal(dict)  # Prompt actual seleccionado
    prompt_versions_changed = pyqtSignal(list)  # Versiones del prompt actual
    
    # Señales de operaciones
    prompt_saved = pyqtSignal(str)  # Prompt guardado exitosamente
    prompt_rendered = pyqtSignal(dict)  # Resultado de renderizado
    prompt_tested = pyqtSignal(dict)  # Resultado de test con IA
    
    # Señales de UI
    loading_state_changed = pyqtSignal(bool)  # Estado de carga
    error_occurred = pyqtSignal(str)  # Error para mostrar al usuario
    status_message_changed = pyqtSignal(str)  # Mensaje de estado
    
    # Señales de filtros y búsqueda
    search_results_changed = pyqtSignal(list)  # Resultados de búsqueda
    categories_changed = pyqtSignal(list)  # Categorías disponibles
    
    def __init__(self, api_client: APIClient, parent=None):
        super().__init__(parent)
        self._api = api_client
        
        # Estado interno
        self._state = AIStudioStateModel()
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save_prompt)
        self._auto_save_timer.setSingleShot(True)
        
        # Cache local
        self._prompts_cache: Dict[str, PromptTemplateModel] = {}
        self._versions_cache: Dict[str, List[PromptVersionModel]] = {}
        self._categories_cache: List[str] = []
        
        # Estado de operaciones
        self._is_loading = False
        self._has_unsaved_changes = False
        self._last_render_result = None
        
        # Configuración
        self._auto_save_delay_ms = 2000  # 2 segundos de delay para auto-save
        self._max_history_entries = 10
        
        logger.info("AIStudioViewModel inicializado")
    
    # === Propiedades públicas ===
    
    @property
    def is_loading(self) -> bool:
        """Indica si hay una operación en curso"""
        return self._is_loading
    
    @property
    def has_unsaved_changes(self) -> bool:
        """Indica si hay cambios sin guardar"""
        return self._has_unsaved_changes
    
    @property
    def current_prompt(self) -> Optional[PromptTemplateModel]:
        """Prompt actualmente seleccionado"""
        return self._state.current_prompt
    
    @property
    def current_template_text(self) -> str:
        """Texto del template actual"""
        if self._state.current_prompt:
            return self._state.current_prompt.template
        return ""
    
    @property
    def current_variables(self) -> Dict[str, Any]:
        """Variables del prompt actual"""
        if self._state.current_prompt:
            return self._state.current_prompt.variables
        return {}
    
    # === Inicialización y carga inicial ===
    
    @pyqtSlot()
    async def initialize(self):
        """Inicializa el ViewModel cargando datos iniciales"""
        try:
            self._set_loading(True)
            await self._load_initial_data()
            self.status_message_changed.emit("AI Studio listo")
            logger.info("AI Studio inicializado exitosamente")
        except Exception as e:
            error_msg = f"Error inicializando AI Studio: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            self._set_loading(False)
    
    # === Gestión de prompts ===
    
    @pyqtSlot()
    async def refresh_prompts_list(self):
        """Actualiza la lista de prompts desde el backend"""
        try:
            self._set_loading(True)
            
            response = await self._api.get("/api/v1/prompts")
            if response.get("success"):
                prompts_data = response.get("data", [])
                prompts = [PromptTemplateModel.from_dict(p) for p in prompts_data]
                
                # Actualizar cache
                self._prompts_cache.clear()
                for prompt in prompts:
                    self._prompts_cache[prompt.name] = prompt
                
                # Extraer categorías únicas
                categories = list(set(p.category for p in prompts))
                self._categories_cache = sorted(categories)
                
                # Emitir señales
                self.prompts_list_changed.emit([p.to_dict() for p in prompts])
                self.categories_changed.emit(self._categories_cache)
                
                logger.debug(f"Cargados {len(prompts)} prompts")
            else:
                raise Exception(response.get("error", "Error desconocido"))
                
        except Exception as e:
            error_msg = f"Error cargando prompts: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            self._set_loading(False)
    
    @pyqtSlot(str)
    async def select_prompt(self, prompt_name: str):
        """Selecciona un prompt específico"""
        try:
            self._set_loading(True)
            
            if prompt_name in self._prompts_cache:
                prompt = self._prompts_cache[prompt_name]
                self._state.current_prompt = prompt
                
                # Cargar versiones del prompt
                await self._load_prompt_versions(prompt_name)
                
                # Resetear estado de edición
                self._has_unsaved_changes = False
                self._auto_save_timer.stop()
                
                # Emitir señales
                self.current_prompt_changed.emit(prompt.to_dict())
                self.status_message_changed.emit(f"Prompt '{prompt_name}' seleccionado")
                
                logger.debug(f"Prompt '{prompt_name}' seleccionado")
            else:
                raise Exception(f"Prompt '{prompt_name}' no encontrado en cache")
                
        except Exception as e:
            error_msg = f"Error seleccionando prompt: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            self._set_loading(False)
    
    @pyqtSlot(str)
    def update_template_text(self, new_text: str):
        """Actualiza el texto del template (para auto-save)"""
        if self._state.current_prompt:
            if self._state.current_prompt.template != new_text:
                self._state.current_prompt.template = new_text
                self._has_unsaved_changes = True
                
                # Reiniciar timer de auto-save
                self._auto_save_timer.stop()
                self._auto_save_timer.start(self._auto_save_delay_ms)
                
                logger.debug("Template modificado - auto-save programado")
    
    @pyqtSlot(str, str)
    def update_prompt_metadata(self, field: str, value: str):
        """Actualiza metadatos del prompt (descripción, categoría, etc.)"""
        if self._state.current_prompt:
            if hasattr(self._state.current_prompt, field):
                setattr(self._state.current_prompt, field, value)
                self._has_unsaved_changes = True
                
                # Auto-save para metadatos
                self._auto_save_timer.stop()
                self._auto_save_timer.start(self._auto_save_delay_ms)
                
                logger.debug(f"Metadato '{field}' actualizado")
    
    @pyqtSlot()
    async def save_current_prompt(self):
        """Guarda el prompt actual como nueva versión"""
        if not self._state.current_prompt:
            self.error_occurred.emit("No hay prompt seleccionado para guardar")
            return
        
        try:
            self._set_loading(True)
            
            payload = {
                "name": self._state.current_prompt.name,
                "template": self._state.current_prompt.template,
                "variables": self._state.current_prompt.variables,
                "description": self._state.current_prompt.description,
                "category": self._state.current_prompt.category
            }
            
            response = await self._api.post("/api/v1/prompts/versions", payload)
            
            if response.get("success"):
                new_version = response.get("data")
                self._has_unsaved_changes = False
                self._auto_save_timer.stop()
                
                # Actualizar cache con nueva versión
                self._state.current_prompt.version = new_version["version"]
                self._state.current_prompt.updated_at = datetime.fromisoformat(
                    new_version["updated_at"]
                )
                
                # Recargar versiones
                await self._load_prompt_versions(self._state.current_prompt.name)
                
                success_msg = f"Prompt guardado como v{new_version['version']}"
                self.prompt_saved.emit(success_msg)
                self.status_message_changed.emit(success_msg)
                
                logger.info(f"Prompt '{self._state.current_prompt.name}' guardado exitosamente")
            else:
                raise Exception(response.get("error", "Error guardando prompt"))
                
        except Exception as e:
            error_msg = f"Error guardando prompt: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            self._set_loading(False)
    
    # === Playground y testing ===
    
    @pyqtSlot(dict)
    async def test_prompt_with_variables(self, variables: Dict[str, Any]):
        """Prueba el prompt actual con variables en el playground"""
        if not self._state.current_prompt:
            self.error_occurred.emit("No hay prompt seleccionado para probar")
            return
        
        try:
            self._set_loading(True)
            
            # Primero renderizar el template
            render_result = await self._render_prompt(variables)
            
            if render_result:
                # Luego probar con IA (opcional)
                ai_result = await self._test_with_ai(render_result["content"])
                
                test_result = {
                    "rendered_prompt": render_result["content"],
                    "variables_used": variables,
                    "ai_response": ai_result,
                    "timestamp": datetime.now().isoformat(),
                    "prompt_name": self._state.current_prompt.name,
                    "prompt_version": self._state.current_prompt.version
                }
                
                self._last_render_result = test_result
                self.prompt_tested.emit(test_result)
                self.status_message_changed.emit("Prompt probado exitosamente")
                
                logger.info(f"Prompt '{self._state.current_prompt.name}' probado con IA")
            
        except Exception as e:
            error_msg = f"Error probando prompt: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            self._set_loading(False)
    
    @pyqtSlot(dict)
    async def render_prompt_only(self, variables: Dict[str, Any]):
        """Solo renderiza el prompt sin probar con IA"""
        if not self._state.current_prompt:
            self.error_occurred.emit("No hay prompt seleccionado para renderizar")
            return
        
        try:
            result = await self._render_prompt(variables)
            if result:
                self.prompt_rendered.emit(result)
                logger.debug("Prompt renderizado exitosamente")
        except Exception as e:
            error_msg = f"Error renderizando prompt: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
    
    # === Búsqueda y filtros ===
    
    @pyqtSlot(str)
    async def search_prompts(self, query: str):
        """Busca prompts por contenido o nombre"""
        try:
            if not query.strip():
                # Si no hay query, mostrar todos los prompts
                all_prompts = list(self._prompts_cache.values())
                self.search_results_changed.emit([p.to_dict() for p in all_prompts])
                return
            
            self._set_loading(True)
            
            params = {"query": query}
            response = await self._api.get("/api/v1/prompts/search", params=params)
            
            if response.get("success"):
                results_data = response.get("data", [])
                results = [PromptTemplateModel.from_dict(p) for p in results_data]
                
                self.search_results_changed.emit([r.to_dict() for r in results])
                self.status_message_changed.emit(f"Encontrados {len(results)} prompts")
                
                logger.debug(f"Búsqueda '{query}' retornó {len(results)} resultados")
            else:
                raise Exception(response.get("error", "Error en búsqueda"))
                
        except Exception as e:
            error_msg = f"Error en búsqueda: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            self._set_loading(False)
    
    @pyqtSlot(str)
    def filter_by_category(self, category: str):
        """Filtra prompts por categoría"""
        try:
            if category == "all" or not category:
                # Mostrar todos los prompts
                all_prompts = list(self._prompts_cache.values())
                filtered = all_prompts
            else:
                # Filtrar por categoría específica
                filtered = [p for p in self._prompts_cache.values() if p.category == category]
            
            self.search_results_changed.emit([p.to_dict() for p in filtered])
            self.status_message_changed.emit(f"Filtrados {len(filtered)} prompts")
            
            logger.debug(f"Filtrado por categoría '{category}': {len(filtered)} prompts")
            
        except Exception as e:
            error_msg = f"Error filtrando por categoría: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
    
    # === Gestión de versiones ===
    
    @pyqtSlot(int)
    async def load_prompt_version(self, version: int):
        """Carga una versión específica del prompt actual"""
        if not self._state.current_prompt:
            return
        
        try:
            self._set_loading(True)
            
            response = await self._api.get(
                f"/api/v1/prompts/{self._state.current_prompt.name}/versions/{version}"
            )
            
            if response.get("success"):
                version_data = response.get("data")
                prompt = PromptTemplateModel.from_dict(version_data)
                
                self._state.current_prompt = prompt
                self._has_unsaved_changes = False
                
                self.current_prompt_changed.emit(prompt.to_dict())
                self.status_message_changed.emit(f"Cargada versión {version}")
                
                logger.info(f"Versión {version} cargada")
            else:
                raise Exception(response.get("error", "Error cargando versión"))
                
        except Exception as e:
            error_msg = f"Error cargando versión: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            self._set_loading(False)
    
    # === Métodos privados ===
    
    async def _load_initial_data(self):
        """Carga datos iniciales del ViewModel"""
        await self.refresh_prompts_list()
    
    async def _load_prompt_versions(self, prompt_name: str):
        """Carga todas las versiones de un prompt"""
        try:
            response = await self._api.get(f"/api/v1/prompts/{prompt_name}/versions")
            
            if response.get("success"):
                versions_data = response.get("data", [])
                versions = [PromptVersionModel.from_dict(v) for v in versions_data]
                
                self._versions_cache[prompt_name] = versions
                self.prompt_versions_changed.emit([v.to_dict() for v in versions])
                
                logger.debug(f"Cargadas {len(versions)} versiones para '{prompt_name}'")
            
        except Exception as e:
            logger.warning(f"Error cargando versiones de '{prompt_name}': {str(e)}")
    
    async def _render_prompt(self, variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Renderiza el prompt actual con variables"""
        if not self._state.current_prompt:
            return None
        
        payload = {
            "name": self._state.current_prompt.name,
            "variables": variables
        }
        
        response = await self._api.post("/api/v1/prompts/render", payload)
        
        if response.get("success"):
            return response.get("data")
        else:
            raise Exception(response.get("error", "Error renderizando prompt"))
    
    async def _test_with_ai(self, rendered_prompt: str) -> Optional[str]:
        """Prueba el prompt renderizado con IA"""
        try:
            payload = {
                "prompt": rendered_prompt,
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = await self._api.post("/api/v1/ai/generate", payload)
            
            if response.get("success"):
                return response.get("data", {}).get("generated_text", "")
            else:
                logger.warning(f"IA no disponible: {response.get('error', 'Error desconocido')}")
                return None
        except Exception as e:
            logger.warning(f"Error probando con IA: {str(e)}")
            return None
    
    @pyqtSlot()
    async def _auto_save_prompt(self):
        """Auto-guarda el prompt actual si hay cambios"""
        if self._has_unsaved_changes and self._state.current_prompt:
            try:
                await self.save_current_prompt()
                logger.debug("Auto-save ejecutado exitosamente")
            except Exception as e:
                logger.error(f"Error en auto-save: {str(e)}")
    
    def _set_loading(self, loading: bool):
        """Actualiza el estado de carga"""
        if self._is_loading != loading:
            self._is_loading = loading
            self.loading_state_changed.emit(loading)
    
    # === Cleanup ===
    
    def cleanup(self):
        """Limpia recursos del ViewModel"""
        self._auto_save_timer.stop()
        logger.info("AIStudioViewModel limpiado")
