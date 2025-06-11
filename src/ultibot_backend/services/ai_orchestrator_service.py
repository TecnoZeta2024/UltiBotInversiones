import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import HTTPException
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import GoogleAPIError

from src.ultibot_backend.core.domain_models.ai import AIResponse, TradingAIResponse
from src.ultibot_backend.app_config import AppSettings

logger = logging.getLogger(__name__)

DEFAULT_PROMPT_TEMPLATE = """
Eres un analista de trading de criptomonedas experto con amplia experiencia en mercados financieros.
Tu misión es evaluar oportunidades de trading y proporcionar recomendaciones fundamentadas para maximizar
las ganancias mientras gestionas el riesgo de manera responsable.

**CONTEXTO DE LA ESTRATEGIA:**
{strategy_context}

**OPORTUNIDAD DE TRADING DETECTADA:**
{opportunity_context}

**HISTORIAL DE PERFORMANCE (últimas operaciones):**
{historical_context}

**DATOS DE HERRAMIENTAS DE ANÁLISIS:**
{tool_outputs}

**INSTRUCCIONES CRÍTICAS:**
1. Evalúa la oportunidad considerando:
   - Tendencias técnicas y fundamentales
   - Contexto histórico de la estrategia
   - Condiciones actuales del mercado
   - Gestión de riesgo apropiada

2. Proporciona una recomendación clara y justificada:
   - COMPRAR: Alta probabilidad de ganancia
   - VENDER: Alta probabilidad de pérdida o toma de ganancias
   - ESPERAR: Condiciones no óptimas o necesidad de más información

3. Cuantifica tu nivel de confianza (0.0 = sin confianza, 1.0 = máxima confianza)

4. Para operaciones reales, requiere confianza ≥ 0.95
   Para paper trading, confianza ≥ 0.75 es aceptable

5. Si detectas riesgos significativos, inclúyelos en las advertencias

6. Sugiere precios específicos cuando sea apropiado (entrada, stop loss, take profit)

**IMPORTANTE:** Responde ÚNICAMENTE en el formato JSON estructurado solicitado.

**FORMATO DE SALIDA REQUERIDO:**
{format_instructions}
"""

class AIOrchestratorService:
    """
    Servicio para orquestar las interacciones con el modelo de IA (Gemini),
    incluyendo la construcción de prompts, el análisis y el parseo de respuestas.
    """

    def __init__(self, app_settings: AppSettings):
        self.app_settings = app_settings
        # Acceder a la clave de forma segura
        self.gemini_api_key = getattr(app_settings, 'GEMINI_API_KEY', None)
        
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY no está configurada. El servicio de IA no funcionará.")
            self.llm = None
            self.parser = None
            self.output_fixing_parser = None
            self.prompt_template = None
        else:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro-latest",
                google_api_key=self.gemini_api_key,
                temperature=0.7,
                convert_system_message_to_human=True
            )
            self.parser = PydanticOutputParser(pydantic_object=AIResponse)
            self.trading_parser = PydanticOutputParser(pydantic_object=TradingAIResponse)
            self.output_fixing_parser = OutputFixingParser.from_llm(
                parser=self.parser, llm=self.llm
            )
            self.trading_output_fixing_parser = OutputFixingParser.from_llm(
                parser=self.trading_parser, llm=self.llm
            )
            prompt_template_str = getattr(app_settings, 'prompt_template', DEFAULT_PROMPT_TEMPLATE)
            self.prompt_template = PromptTemplate(
                template=prompt_template_str,
                input_variables=[
                    "strategy_context",
                    "opportunity_context",
                    "historical_context",
                    "tool_outputs",
                ],
                partial_variables={"format_instructions": self.parser.get_format_instructions()},
            )
            self.trading_prompt_template = PromptTemplate(
                template=prompt_template_str,
                input_variables=[
                    "strategy_context",
                    "opportunity_context",
                    "historical_context",
                    "tool_outputs",
                ],
                partial_variables={"format_instructions": self.trading_parser.get_format_instructions()},
            )
            logger.info(f"AIOrchestrator initialized with {self.llm.model} and PydanticOutputParser.")

    async def analyze_opportunity_with_strategy_context_async(
        self,
        strategy_context: str,
        opportunity_context: str,
        historical_context: str,
        tool_outputs: str,
        analysis_id: Optional[uuid.UUID] = None,
    ) -> AIResponse:
        """
        Analiza una oportunidad de trading de forma asíncrona.
        """
        if not self.llm or not self.prompt_template or not self.parser or not self.output_fixing_parser:
            raise HTTPException(status_code=503, detail="AI service is not configured (GEMINI_API_KEY is missing).")

        analysis_id = analysis_id or uuid.uuid4()
        logger.info(f"Starting AI analysis for ID: {analysis_id}...")

        try:
            chain = self.prompt_template | self.llm | self.parser
            
            logger.debug(f"Invoking LLM chain for analysis ID: {analysis_id}")
            response_content = await chain.ainvoke(
                {
                    "strategy_context": strategy_context,
                    "opportunity_context": opportunity_context,
                    "historical_context": historical_context,
                    "tool_outputs": tool_outputs,
                }
            )
            logger.info(f"Successfully parsed AI response for {analysis_id}: {response_content.model_dump_json(indent=2)}")
            return response_content

        except OutputParserException as e:
            logger.warning(
                f"Failed to parse LLM output for {analysis_id}. Attempting to fix with OutputFixingParser. Original error: {e}"
            )
            try:
                # Re-invocar la cadena sin el parser original para obtener el texto crudo
                raw_chain = self.prompt_template | self.llm
                raw_response = await raw_chain.ainvoke({
                    "strategy_context": strategy_context,
                    "opportunity_context": opportunity_context,
                    "historical_context": historical_context,
                    "tool_outputs": tool_outputs,
                })
                fixed_response = self.output_fixing_parser.parse(raw_response.content)
                logger.info(f"Successfully fixed and parsed AI response for {analysis_id} using OutputFixingParser.")
                return fixed_response
            except Exception as fix_e:
                logger.error(f"Failed to fix and parse LLM output for {analysis_id}: {fix_e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to parse and fix AI response: {fix_e}")
        
        except GoogleAPIError as gemini_err:
            logger.error(f"Gemini API specific error for {analysis_id}: {gemini_err}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"AI provider error: {gemini_err}")

        except Exception as e:
            logger.error(f"An unexpected error occurred during AI analysis for {analysis_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred during AI analysis: {e}")

    async def analyze_trading_opportunity_async(
        self,
        strategy_context: str,
        opportunity_context: str,
        historical_context: str,
        tool_outputs: str,
        analysis_id: Optional[uuid.UUID] = None,
    ) -> TradingAIResponse:
        """
        Analiza una oportunidad de trading específicamente para obtener recomendaciones estructuradas.
        
        Args:
            strategy_context: Contexto de la estrategia de trading
            opportunity_context: Información de la oportunidad detectada
            historical_context: Historial de operaciones previas
            tool_outputs: Resultados de herramientas de análisis
            analysis_id: ID único para el análisis (opcional)
            
        Returns:
            TradingAIResponse: Respuesta estructurada con recomendación de trading
            
        Raises:
            HTTPException: Si el servicio no está configurado o hay errores
        """
        if not self.llm or not self.trading_prompt_template or not self.trading_parser:
            raise HTTPException(
                status_code=503, 
                detail="AI service is not configured (GEMINI_API_KEY is missing)."
            )

        analysis_id = analysis_id or uuid.uuid4()
        logger.info(f"Starting trading analysis for ID: {analysis_id}...")

        try:
            chain = self.trading_prompt_template | self.llm | self.trading_parser
            
            logger.debug(f"Invoking trading LLM chain for analysis ID: {analysis_id}")
            response_content = await chain.ainvoke(
                {
                    "strategy_context": strategy_context,
                    "opportunity_context": opportunity_context,
                    "historical_context": historical_context,
                    "tool_outputs": tool_outputs,
                }
            )
            
            # Añadir el analysis_id a la respuesta
            response_content.analysis_id = str(analysis_id)
            
            logger.info(f"Successfully parsed trading AI response for {analysis_id}")
            logger.info(f"Recommendation: {response_content.recommendation.value} (Confidence: {response_content.confidence:.2%})")
            
            return response_content

        except OutputParserException as e:
            logger.warning(
                f"Failed to parse trading LLM output for {analysis_id}. Attempting to fix with OutputFixingParser. Original error: {e}"
            )
            try:
                # Re-invocar la cadena sin el parser original para obtener el texto crudo
                raw_chain = self.trading_prompt_template | self.llm
                raw_response = await raw_chain.ainvoke({
                    "strategy_context": strategy_context,
                    "opportunity_context": opportunity_context,
                    "historical_context": historical_context,
                    "tool_outputs": tool_outputs,
                })
                fixed_response = self.trading_output_fixing_parser.parse(raw_response.content)
                fixed_response.analysis_id = str(analysis_id)
                logger.info(f"Successfully fixed and parsed trading AI response for {analysis_id} using OutputFixingParser.")
                return fixed_response
            except Exception as fix_e:
                logger.error(f"Failed to fix and parse trading LLM output for {analysis_id}: {fix_e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to parse and fix trading AI response: {fix_e}")
        
        except GoogleAPIError as gemini_err:
            logger.error(f"Gemini API specific error for trading analysis {analysis_id}: {gemini_err}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"AI provider error: {gemini_err}")

        except Exception as e:
            logger.error(f"An unexpected error occurred during trading analysis for {analysis_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred during trading analysis: {e}")
