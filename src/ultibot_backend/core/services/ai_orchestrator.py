"""
AI Orchestrator Service - Orquestador central de inteligencia artificial.

Este servicio coordina el flujo completo de análisis de IA:
1. Planificación: Genera un plan de análisis usando prompts
2. Ejecución: Ejecuta herramientas MCP según el plan
3. Síntesis: Combina resultados en una recomendación final

Mantiene la pureza del dominio al depender solo de puertos.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ..domain_models.ai_models import (
    AIAnalysisRequest,
    AIAnalysisPlan,
    AIAnalysisResult,
    AIInteractionLog,
    AIModelType,
    AIProcessingStage,
    AIRequestPriority,
    ToolAction,
    ToolExecutionResult,
    TradingOpportunity,
)
from ..exceptions import (
    AIServiceError,
    InvalidParameterError,
    ServiceUnavailableError,
    TimeoutError,
)
from ..ports import (
    IEventPublisher,
    ILoggingPort,
    IAIProvider,
    IMCPToolHub,
    IPromptManager,
)

logger = logging.getLogger(__name__)

class AIOrchestratorService:
    """
    Servicio orquestador de IA que maneja el flujo completo de análisis.
    
    Implementa el patrón de tres fases:
    1. PLANNING: Analiza la oportunidad y genera un plan de herramientas
    2. EXECUTION: Ejecuta las herramientas MCP según el plan
    3. SYNTHESIS: Combina los resultados en una recomendación final
    """
    
    def __init__(
        self,
        ai_provider: IAIProvider,
        tool_hub: IMCPToolHub,
        prompt_manager: IPromptManager,
        event_publisher: IEventPublisher,
        logging_port: ILoggingPort,
        max_concurrent_tools: int = 3,
        global_timeout_seconds: int = 300
    ):
        """
        Inicializa el AI Orchestrator Service.
        
        Args:
            ai_provider: Proveedor de IA (ej. GeminiAdapter)
            tool_hub: Hub de herramientas MCP
            prompt_manager: Gestor de prompts
            event_publisher: Publicador de eventos
            logging_port: Puerto de logging
            max_concurrent_tools: Máximo de herramientas concurrentes
            global_timeout_seconds: Timeout global para todo el proceso
        """
        self._ai_provider = ai_provider
        self._tool_hub = tool_hub
        self._prompt_manager = prompt_manager
        self._event_publisher = event_publisher
        self._logging_port = logging_port
        self._max_concurrent_tools = max_concurrent_tools
        self._global_timeout_seconds = global_timeout_seconds
        
        # Métricas internas
        self._active_analyses: Dict[UUID, AIAnalysisRequest] = {}
        self._completed_analyses: List[AIAnalysisResult] = []
        
    async def analyze_opportunity(
        self,
        opportunity: TradingOpportunity,
        strategy_context: Optional[Dict[str, Any]] = None,
        priority: AIRequestPriority = AIRequestPriority.MEDIUM
    ) -> AIAnalysisResult:
        """
        Analiza una oportunidad de trading usando IA.
        
        Args:
            opportunity: Oportunidad de trading a analizar
            strategy_context: Contexto adicional de la estrategia
            priority: Prioridad del análisis
            
        Returns:
            Resultado completo del análisis de IA
            
        Raises:
            AIServiceError: Error en el servicio de IA
            TimeoutError: Timeout en el análisis
            ServiceUnavailableError: Servicio no disponible
        """
        # Crear request
        request = AIAnalysisRequest(
            opportunity_id=opportunity.opportunity_id,
            market_data=opportunity.dict(),
            strategy_context=strategy_context,
            priority=priority,
            timeout_seconds=self._global_timeout_seconds
        )
        
        # Registrar análisis activo
        self._active_analyses[request.request_id] = request
        
        try:
            # Log inicio del análisis
            await self._logging_port.log_info(
                f"Iniciando análisis IA para oportunidad {opportunity.opportunity_id}",
                extra={
                    "request_id": str(request.request_id),
                    "symbol": opportunity.symbol,
                    "strategy": opportunity.strategy_name,
                    "priority": priority.value
                }
            )
            
            start_time = time.time()
            
            # Ejecutar análisis completo con timeout
            result = await asyncio.wait_for(
                self._execute_full_analysis(request, opportunity),
                timeout=self._global_timeout_seconds
            )
            
            total_time = (time.time() - start_time) * 1000
            result = result.copy(update={"total_execution_time_ms": total_time})
            
            # Almacenar resultado
            self._completed_analyses.append(result)
            
            # Log éxito
            await self._logging_port.log_info(
                f"Análisis IA completado exitosamente para {opportunity.opportunity_id}",
                extra={
                    "request_id": str(request.request_id),
                    "confidence": result.confidence_score,
                    "execution_time_ms": total_time,
                    "tools_used": len(result.tool_results)
                }
            )
            
            return result
            
        except asyncio.TimeoutError:
            await self._logging_port.log_error(
                f"Timeout en análisis IA para {opportunity.opportunity_id}",
                extra={"request_id": str(request.request_id)}
            )
            raise TimeoutError(f"AI analysis timed out after {self._global_timeout_seconds}s")
            
        except Exception as e:
            await self._logging_port.log_error(
                f"Error en análisis IA para {opportunity.opportunity_id}: {str(e)}",
                extra={"request_id": str(request.request_id), "error": str(e)}
            )
            raise AIServiceError(f"AI analysis failed: {str(e)}")
            
        finally:
            # Limpiar análisis activo
            self._active_analyses.pop(request.request_id, None)
    
    async def _execute_full_analysis(
        self,
        request: AIAnalysisRequest,
        opportunity: TradingOpportunity
    ) -> AIAnalysisResult:
        """
        Ejecuta el análisis completo en tres fases.
        
        Args:
            request: Request de análisis
            opportunity: Oportunidad a analizar
            
        Returns:
            Resultado del análisis
        """
        # FASE 1: PLANIFICACIÓN
        plan = await self._execute_planning_phase(request, opportunity)
        
        # FASE 2: EJECUCIÓN DE HERRAMIENTAS
        tool_results = await self._execute_tools_phase(request, plan)
        
        # FASE 3: SÍNTESIS
        result = await self._execute_synthesis_phase(request, plan, tool_results)
        
        return result
    
    async def _execute_planning_phase(
        self,
        request: AIAnalysisRequest,
        opportunity: TradingOpportunity
    ) -> AIAnalysisPlan:
        """
        Fase 1: Planificación del análisis.
        
        Usa IA para generar un plan de herramientas a ejecutar.
        """
        await self._logging_port.log_debug(
            f"Iniciando fase de planificación para {request.opportunity_id}"
        )
        
        # Obtener prompt de planificación
        planning_prompt = await self._prompt_manager.get_prompt_template(
            "opportunity_planning"
        )
        
        # Obtener herramientas disponibles
        available_tools = await self._tool_hub.list_available_tools()
        
        # Preparar contexto para IA
        context = {
            "opportunity": opportunity.dict(),
            "strategy_context": request.strategy_context or {},
            "available_tools": [tool.dict() for tool in available_tools],
            "max_tools": request.max_tools_per_stage,
            "priority": request.priority.value
        }
        
        # Renderizar prompt
        rendered_prompt = await self._prompt_manager.render_prompt(
            planning_prompt,
            context
        )
        
        start_time = time.time()
        
        # Llamar a IA para planificación
        ai_response = await self._ai_provider.generate_text(
            prompt=rendered_prompt,
            context=context,
            max_tokens=1500,
            temperature=0.3  # Baja temperatura para planificación consistente
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        # Parsear respuesta de IA y crear plan
        plan = await self._parse_planning_response(request, ai_response)
        
        # Log de interacción
        await self._log_ai_interaction(
            request.request_id,
            "planning",
            AIProcessingStage.PLANNING,
            planning_prompt.template,
            context,
            rendered_prompt,
            ai_response,
            execution_time
        )
        
        await self._logging_port.log_info(
            f"Plan de análisis generado: {len(plan.tool_actions)} herramientas",
            extra={
                "request_id": str(request.request_id),
                "tools_planned": [action.name for action in plan.tool_actions],
                "confidence": plan.confidence_score
            }
        )
        
        return plan
    
    async def _execute_tools_phase(
        self,
        request: AIAnalysisRequest,
        plan: AIAnalysisPlan
    ) -> List[ToolExecutionResult]:
        """
        Fase 2: Ejecución de herramientas MCP.
        
        Ejecuta las herramientas especificadas en el plan.
        """
        await self._logging_port.log_debug(
            f"Iniciando fase de ejecución: {len(plan.tool_actions)} herramientas"
        )
        
        if not plan.tool_actions:
            await self._logging_port.log_warning(
                "No hay herramientas para ejecutar en el plan"
            )
            return []
        
        # Agrupar herramientas por prioridad
        tool_groups = self._group_tools_by_priority(plan.tool_actions)
        
        all_results = []
        
        # Ejecutar herramientas por grupos de prioridad
        for priority, actions in tool_groups.items():
            await self._logging_port.log_debug(
                f"Ejecutando {len(actions)} herramientas de prioridad {priority}"
            )
            
            # Ejecutar herramientas concurrentemente dentro del grupo
            batch_results = await self._execute_tool_batch(actions)
            all_results.extend(batch_results)
        
        # Filtrar solo resultados exitosos
        successful_results = [r for r in all_results if r.success]
        
        await self._logging_port.log_info(
            f"Herramientas ejecutadas: {len(successful_results)}/{len(all_results)} exitosas",
            extra={
                "request_id": str(request.request_id),
                "successful_tools": [r.tool_name for r in successful_results],
                "failed_tools": [r.tool_name for r in all_results if not r.success]
            }
        )
        
        return successful_results
    
    async def _execute_synthesis_phase(
        self,
        request: AIAnalysisRequest,
        plan: AIAnalysisPlan,
        tool_results: List[ToolExecutionResult]
    ) -> AIAnalysisResult:
        """
        Fase 3: Síntesis de resultados.
        
        Combina todos los resultados en una recomendación final.
        """
        await self._logging_port.log_debug(
            f"Iniciando fase de síntesis con {len(tool_results)} resultados"
        )
        
        # Obtener prompt de síntesis
        synthesis_prompt = await self._prompt_manager.get_prompt_template(
            "opportunity_synthesis"
        )
        
        # Preparar contexto para síntesis
        context = {
            "opportunity_id": request.opportunity_id,
            "market_data": request.market_data,
            "strategy_context": request.strategy_context or {},
            "plan_reasoning": plan.reasoning,
            "tool_results": [result.dict() for result in tool_results],
            "total_tools_executed": len(tool_results)
        }
        
        # Renderizar prompt
        rendered_prompt = await self._prompt_manager.render_prompt(
            synthesis_prompt,
            context
        )
        
        start_time = time.time()
        
        # Llamar a IA para síntesis
        ai_response = await self._ai_provider.generate_text(
            prompt=rendered_prompt,
            context=context,
            max_tokens=2000,
            temperature=0.5  # Temperatura media para síntesis balanceada
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        # Parsear respuesta y crear resultado
        result = await self._parse_synthesis_response(
            request,
            plan,
            ai_response,
            tool_results
        )
        
        # Log de interacción
        await self._log_ai_interaction(
            request.request_id,
            "synthesis",
            AIProcessingStage.SYNTHESIS,
            synthesis_prompt.template,
            context,
            rendered_prompt,
            ai_response,
            execution_time
        )
        
        await self._logging_port.log_info(
            f"Síntesis completada con confianza {result.confidence_score}",
            extra={
                "request_id": str(request.request_id),
                "recommendation": result.recommendation[:100] + "...",
                "confidence": result.confidence_score
            }
        )
        
        return result
    
    async def _parse_planning_response(
        self,
        request: AIAnalysisRequest,
        ai_response: str
    ) -> AIAnalysisPlan:
        """
        Parsea la respuesta de IA para crear un plan de análisis.
        
        Args:
            request: Request original
            ai_response: Respuesta de la IA
            
        Returns:
            Plan de análisis parseado
        """
        # TODO: Implementar parser más sofisticado con JSON estructurado
        # Por ahora, usar un parser simple que busca patrones
        
        plan = AIAnalysisPlan(
            request_id=request.request_id,
            reasoning=ai_response[:500],  # Primeros 500 caracteres como razonamiento
            estimated_duration_ms=30000,  # 30 segundos estimado
            confidence_score=0.8  # Confianza por defecto
        )
        
        # Extraer acciones de herramientas de la respuesta
        # Buscar patrones como "USE_TOOL: nombre_herramienta"
        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('USE_TOOL:'):
                tool_name = line.replace('USE_TOOL:', '').strip()
                action = ToolAction(
                    name=tool_name,
                    parameters={},
                    priority=request.priority
                )
                plan.add_tool_action(action)
        
        # Si no se encontraron herramientas, añadir una por defecto
        if not plan.tool_actions:
            default_action = ToolAction(
                name="market_sentiment_analyzer",
                parameters={"symbol": request.market_data.get("symbol", "")},
                priority=request.priority
            )
            plan.add_tool_action(default_action)
        
        return plan
    
    async def _parse_synthesis_response(
        self,
        request: AIAnalysisRequest,
        plan: AIAnalysisPlan,
        ai_response: str,
        tool_results: List[ToolExecutionResult]
    ) -> AIAnalysisResult:
        """
        Parsea la respuesta de síntesis para crear el resultado final.
        
        Args:
            request: Request original
            plan: Plan ejecutado
            ai_response: Respuesta de síntesis
            tool_results: Resultados de herramientas
            
        Returns:
            Resultado final del análisis
        """
        # TODO: Implementar parser más sofisticado
        # Por ahora, usar parser simple
        
        # Extraer recomendación (primeros párrafos)
        paragraphs = ai_response.split('\n\n')
        recommendation = paragraphs[0] if paragraphs else ai_response[:200]
        
        # Extraer evaluación de riesgo
        risk_assessment = "MEDIUM"  # Por defecto
        if "high risk" in ai_response.lower():
            risk_assessment = "HIGH"
        elif "low risk" in ai_response.lower():
            risk_assessment = "LOW"
        
        # Extraer confianza (buscar patrones como "confidence: 85%")
        confidence_score = 0.75  # Por defecto
        import re
        confidence_match = re.search(r'confidence[:\s]+(\d+)%', ai_response.lower())
        if confidence_match:
            confidence_score = float(confidence_match.group(1)) / 100.0
        
        result = AIAnalysisResult(
            request_id=request.request_id,
            plan_id=plan.plan_id,
            stage=AIProcessingStage.COMPLETED,
            recommendation=recommendation,
            confidence_score=confidence_score,
            risk_assessment=risk_assessment,
            tool_results=tool_results,
            total_execution_time_ms=0.0,  # Se actualiza después
            tokens_used=len(ai_response) // 4,  # Estimación
            model_used=AIModelType.GEMINI_PRO
        )
        
        return result
    
    def _group_tools_by_priority(
        self,
        tool_actions: List[ToolAction]
    ) -> Dict[AIRequestPriority, List[ToolAction]]:
        """
        Agrupa herramientas por prioridad para ejecución ordenada.
        
        Args:
            tool_actions: Lista de acciones de herramientas
            
        Returns:
            Diccionario agrupado por prioridad
        """
        groups = {}
        for action in tool_actions:
            if action.priority not in groups:
                groups[action.priority] = []
            groups[action.priority].append(action)
        
        # Ordenar por prioridad: CRITICAL > HIGH > MEDIUM > LOW
        priority_order = [
            AIRequestPriority.CRITICAL,
            AIRequestPriority.HIGH,
            AIRequestPriority.MEDIUM,
            AIRequestPriority.LOW
        ]
        
        ordered_groups = {}
        for priority in priority_order:
            if priority in groups:
                ordered_groups[priority] = groups[priority]
        
        return ordered_groups
    
    async def _execute_tool_batch(
        self,
        tool_actions: List[ToolAction]
    ) -> List[ToolExecutionResult]:
        """
        Ejecuta un lote de herramientas concurrentemente.
        
        Args:
            tool_actions: Acciones de herramientas a ejecutar
            
        Returns:
            Lista de resultados
        """
        # Limitar concurrencia
        semaphore = asyncio.Semaphore(self._max_concurrent_tools)
        
        async def execute_single_tool(action: ToolAction) -> ToolExecutionResult:
            async with semaphore:
                try:
                    start_time = time.time()
                    
                    result = await asyncio.wait_for(
                        self._tool_hub.execute_tool(action.name, action.parameters),
                        timeout=action.timeout_seconds or 30
                    )
                    
                    execution_time = (time.time() - start_time) * 1000
                    
                    return ToolExecutionResult(
                        tool_name=action.name,
                        success=True,
                        data=result,
                        execution_time_ms=execution_time,
                        timestamp=datetime.utcnow()
                    )
                    
                except asyncio.TimeoutError:
                    return ToolExecutionResult(
                        tool_name=action.name,
                        success=False,
                        error=f"Timeout after {action.timeout_seconds}s",
                        execution_time_ms=0.0,
                        timestamp=datetime.utcnow()
                    )
                    
                except Exception as e:
                    return ToolExecutionResult(
                        tool_name=action.name,
                        success=False,
                        error=str(e),
                        execution_time_ms=0.0,
                        timestamp=datetime.utcnow()
                    )
        
        # Ejecutar todas las herramientas concurrentemente
        tasks = [execute_single_tool(action) for action in tool_actions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar excepciones y convertir a ToolExecutionResult
        tool_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tool_results.append(ToolExecutionResult(
                    tool_name=tool_actions[i].name,
                    success=False,
                    error=str(result),
                    execution_time_ms=0.0,
                    timestamp=datetime.utcnow()
                ))
            else:
                tool_results.append(result)
        
        return tool_results
    
    async def _log_ai_interaction(
        self,
        request_id: UUID,
        interaction_type: str,
        stage: AIProcessingStage,
        prompt_template: str,
        prompt_variables: Dict[str, Any],
        rendered_prompt: str,
        ai_response: str,
        execution_time_ms: float
    ) -> None:
        """
        Registra una interacción con IA para debugging.
        
        Args:
            request_id: ID del request
            interaction_type: Tipo de interacción
            stage: Etapa de procesamiento
            prompt_template: Template del prompt
            prompt_variables: Variables del prompt
            rendered_prompt: Prompt renderizado
            ai_response: Respuesta de IA
            execution_time_ms: Tiempo de ejecución
        """
        # Crear log de interacción
        interaction_log = AIInteractionLog(
            request_id=request_id,
            interaction_type=interaction_type,
            stage=stage,
            prompt_template=prompt_template,
            prompt_variables=prompt_variables,
            rendered_prompt=rendered_prompt,
            ai_response=ai_response,
            tokens_input=len(rendered_prompt) // 4,
            tokens_output=len(ai_response) // 4,
            model_used=AIModelType.GEMINI_PRO,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.utcnow()
        )
        
        # Log para debugging
        await self._logging_port.log_debug(
            f"AI Interaction logged: {interaction_type}",
            extra={
                "request_id": str(request_id),
                "stage": stage.value,
                "execution_time_ms": execution_time_ms,
                "tokens_input": interaction_log.tokens_input,
                "tokens_output": interaction_log.tokens_output
            }
        )
    
    # Métodos de consulta y estado
    
    def get_active_analyses(self) -> List[AIAnalysisRequest]:
        """Obtiene la lista de análisis activos."""
        return list(self._active_analyses.values())
    
    def get_completed_analyses(self) -> List[AIAnalysisResult]:
        """Obtiene la lista de análisis completados."""
        return self._completed_analyses.copy()
    
    def get_analysis_by_id(self, request_id: UUID) -> Optional[AIAnalysisResult]:
        """Busca un análisis por ID."""
        for result in self._completed_analyses:
            if result.request_id == request_id:
                return result
        return None
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado del sistema de IA.
        
        Returns:
            Estado del sistema incluyendo métricas y salud
        """
        ai_status = await self._ai_provider.get_status()
        tool_status = await self._tool_hub.get_status()
        
        return {
            "ai_orchestrator": {
                "active_analyses": len(self._active_analyses),
                "completed_analyses": len(self._completed_analyses),
                "healthy": len(self._active_analyses) < 10  # Límite razonable
            },
            "ai_provider": ai_status,
            "tool_hub": tool_status,
            "overall_healthy": (
                ai_status.get("healthy", False) and
                tool_status.get("healthy", False) and
                len(self._active_analyses) < 10
            )
        }
