"""
API endpoints para gestión de prompts del AI Studio
Proporciona CRUD completo para templates de prompts con versionado
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import time

from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from pydantic import BaseModel, Field

from src.ultibot_backend.dependencies import PromptManagerDep, AIOrchestratorDep
from src.ultibot_backend.core.domain_models.prompt_models import PromptTemplate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prompts", tags=["Prompts"])

# === MODELOS DE REQUEST/RESPONSE ===

class PromptCreateRequest(BaseModel):
    """Request para crear un nuevo prompt."""
    name: str = Field(..., min_length=1, max_length=100)
    template_text: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PromptUpdateRequest(BaseModel):
    """Request para actualizar un prompt existente."""
    template_text: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PromptRenderRequest(BaseModel):
    """Request para renderizar un prompt con variables."""
    name: str = Field(..., min_length=1, max_length=100)
    variables: Dict[str, Any] = Field(default_factory=dict)

class AIGenerateRequest(BaseModel):
    """Request para generar respuesta con IA."""
    prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(default=500, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    model: str = Field(default="gemini-1.5-flash")

class PromptResponse(BaseModel):
    """Response con datos de un prompt."""
    id: str
    name: str
    template_text: str
    version: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

# === ENDPOINTS ===

@router.get("/", response_model=List[PromptResponse])
async def list_prompts(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    prompt_service = PromptManagerDep
):
    """Lista todos los prompts disponibles."""
    try:
        prompts = await prompt_service.list_prompts(category=category)
        logger.info(f"Listados {len(prompts)} prompts")
        return [p.model_dump() for p in prompts]
    except Exception as e:
        logger.error(f"Error listando prompts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{name}", response_model=PromptResponse)
async def get_prompt(
    name: str = Path(..., description="Nombre del prompt"),
    prompt_service = PromptManagerDep
):
    """Obtiene un prompt específico por nombre."""
    try:
        prompt = await prompt_service.get_prompt_template_by_name(name)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' no encontrado")
        return prompt.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo prompt '{name}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    request: PromptCreateRequest,
    prompt_service = PromptManagerDep
):
    """Crea un nuevo prompt."""
    try:
        new_prompt_template = PromptTemplate(**request.model_dump())
        created_prompt = await prompt_service.create_prompt_template(new_prompt_template)
        logger.info(f"Prompt '{created_prompt.name}' creado exitosamente")
        return created_prompt.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando prompt: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.put("/{name}", response_model=PromptResponse)
async def update_prompt(
    name: str = Path(..., description="Nombre del prompt"),
    request: PromptUpdateRequest = ...,
    prompt_service = PromptManagerDep
):
    """Actualiza un prompt existente (crea nueva versión)."""
    try:
        updated_prompt = await prompt_service.update_prompt_template(name, **request.model_dump())
        logger.info(f"Prompt '{name}' actualizado a versión {updated_prompt.version}")
        return updated_prompt.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error actualizando prompt '{name}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/render")
async def render_prompt(
    request: PromptRenderRequest,
    prompt_service = PromptManagerDep
):
    """Renderiza un prompt con variables específicas."""
    try:
        content = await prompt_service.render_prompt_template_by_name(request.name, request.variables)
        return {"name": request.name, "rendered_content": content}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error renderizando prompt '{request.name}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    name: str = Path(..., description="Nombre del prompt"),
    prompt_service = PromptManagerDep
):
    """Elimina un prompt (lo marca como inactivo)."""
    try:
        await prompt_service.delete_prompt_template(name)
        logger.info(f"Prompt '{name}' eliminado")
        return
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error eliminando prompt '{name}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/ai/generate")
async def generate_ai_response(
    request: AIGenerateRequest,
    ai_orchestrator = AIOrchestratorDep
):
    """Genera una respuesta usando IA para un prompt dado."""
    try:
        start_time = time.time()
        response = await ai_orchestrator.generate_simple_response(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            model=request.model
        )
        generation_time = time.time() - start_time
        
        return {
            "generated_text": response,
            "model_used": request.model,
            "generation_time": round(generation_time, 2)
        }
    except Exception as e:
        logger.error(f"Error generando respuesta de IA: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generando respuesta de IA: {str(e)}")
