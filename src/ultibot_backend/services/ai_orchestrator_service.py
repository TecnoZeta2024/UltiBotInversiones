"""
Service responsible for orchestrating AI-based analysis and trading decisions.
"""
import logging
import asyncio
import time
from injector import inject
from typing import Dict, Any, List

from ultibot_backend.core.ports import (
    IAIModelAdapter,
    IMCPToolHub,
    IPromptManager,
)
from ultibot_backend.core.domain_models.ai_models import (
    TradingOpportunity,
    AIAnalysisResult,
    ToolExecutionRequest,
    ToolExecutionResult,
    AIProcessingStage,
    OpportunityData,
)

logger = logging.getLogger(__name__)

class AIOrchestratorService:
    """
    Orchestrates the flow of data to AI models, executes tools,
    interprets responses, and synthesizes trading recommendations.
    """

    @inject
    def __init__(
        self,
        gemini_adapter: IAIModelAdapter,
        tool_hub: IMCPToolHub,
        prompt_manager: IPromptManager,
    ):
        self.gemini_adapter = gemini_adapter
        self.tool_hub = tool_hub
        self.prompt_manager = prompt_manager
        logger.info("AIOrchestratorService initialized.")

    async def analyze_opportunity(self, opportunity: TradingOpportunity) -> AIAnalysisResult:
        """
        Analyzes a trading opportunity through a multi-stage process:
        1.  Planning: Generates a plan of which tools to use.
        2.  Execution: Runs the planned tools to gather data.
        3.  Synthesis: Analyzes the gathered data to make a recommendation.
        """
        start_time = time.perf_counter()
        logger.info(f"Starting AI analysis for opportunity: {opportunity.opportunity_id}")

        try:
            # 1. Planning Stage
            planning_prompt = await self._get_rendered_prompt(
                "opportunity_planning",
                {
                    "context": opportunity.dict(),
                    "tools": await self.tool_hub.list_available_tools(),
                },
            )
            planning_response = await self.gemini_adapter.generate(planning_prompt)
            
            tool_requests = self._parse_tool_requests(planning_response)

            # 2. Execution Stage
            tool_results = await self._execute_tools(tool_requests)

            # 3. Synthesis Stage
            synthesis_prompt = await self._get_rendered_prompt(
                "opportunity_synthesis",
                {
                    "opportunity": opportunity.dict(),
                    "tool_results": [result.dict() for result in tool_results],
                },
            )
            synthesis_response = await self.gemini_adapter.generate(synthesis_prompt)
            
            final_result = self._parse_synthesis_response(synthesis_response, opportunity, tool_results)

            processing_time_ms = (time.perf_counter() - start_time) * 1000
            final_result.total_execution_time_ms = processing_time_ms
            final_result.ai_metadata["processing_time_ms"] = processing_time_ms
            
            logger.info(f"AI analysis completed for {opportunity.opportunity_id} in {processing_time_ms:.2f}ms. Recommendation: {final_result.recommendation}")
            return final_result

        except Exception as e:
            logger.error(f"Error during AI analysis for opportunity {opportunity.opportunity_id}: {e}", exc_info=True)
            return AIAnalysisResult(
                request_id=opportunity.opportunity_id,
                stage=AIProcessingStage.FAILED,
                recommendation="ERROR",
                confidence=0.0,
                reasoning=f"An internal error occurred: {e}",
                total_execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    async def _get_rendered_prompt(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Helper to get and render a prompt."""
        template = await self.prompt_manager.get_prompt(template_name)
        return await self.prompt_manager.render_prompt(template, variables)

    def _parse_tool_requests(self, planning_response: Dict[str, Any]) -> List[ToolExecutionRequest]:
        """Parses the AI's planning response to extract tool execution requests."""
        requests = []
        # This logic assumes a specific structure from the planning prompt response
        actions = planning_response.get("plan", {}).get("tool_actions", [])
        for action in actions:
            if "name" in action and "parameters" in action:
                requests.append(ToolExecutionRequest(tool_name=action["name"], parameters=action["parameters"]))
        return requests

    async def _execute_tools(self, tool_requests: List[ToolExecutionRequest]) -> List[ToolExecutionResult]:
        """Executes a list of tool requests concurrently."""
        if not tool_requests:
            return []
        
        tasks = [
            self.tool_hub.execute_tool(req.tool_name, req.parameters)
            for req in tool_requests
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out potential exceptions, logging them
        final_results = []
        for res in results:
            if isinstance(res, ToolExecutionResult):
                final_results.append(res)
            elif isinstance(res, Exception):
                logger.error(f"Tool execution failed: {res}", exc_info=True)
        return final_results

    def _parse_synthesis_response(
        self, 
        synthesis_response: Dict[str, Any], 
        opportunity: TradingOpportunity,
        tool_results: List[ToolExecutionResult]
    ) -> AIAnalysisResult:
        """Parses the final synthesis response from the AI into a structured result."""
        analysis = synthesis_response.get("analysis", {})
        return AIAnalysisResult(
            request_id=opportunity.opportunity_id,
            stage=AIProcessingStage.COMPLETED,
            recommendation=analysis.get("recommendation", "HOLD"),
            confidence=analysis.get("confidence", 0.5),
            reasoning=analysis.get("reasoning", "No specific reasoning provided."),
            tool_results=tool_results,
            ai_metadata={
                "model_version": self.gemini_adapter.get_model_name(),
                "tools_used": [res.tool_name for res in tool_results],
            }
        )


# Alias para compatibilidad con tests que esperan el nombre AIOrchestrator
AIOrchestrator = AIOrchestratorService
