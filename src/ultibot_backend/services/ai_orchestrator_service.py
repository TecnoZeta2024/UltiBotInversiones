import json
import logging
import re # Importar re para el fallback de regex
from typing import List, Dict, Any, Optional

from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI # Para cuando se integre Gemini
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from src.shared.data_types import Opportunity, OpportunitySourceType, OpportunityStatus, AIAnalysis, AiStrategyConfiguration
from src.ultibot_backend.services.config_service import ConfigService, UserConfiguration
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # Asumiendo que es la implementación
# Importar herramientas MCP y la base
from src.ultibot_backend.adapters.mcp_tools.base_mcp_tool import BaseMCPTool
from src.ultibot_backend.adapters.mcp_tools.mock_mcp_tool import MockMCPTool # Ejemplo
from src.ultibot_backend.core.exceptions import AIAnalysisError, MobulaAPIError, BinanceAPIError # Importar la excepción personalizada
# Importar adaptadores para verificación de datos
from src.ultibot_backend.adapters.mobula_adapter import MobulaAdapter
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
# Importar NotificationService
from src.ultibot_backend.services.notification_service import NotificationService


logger = logging.getLogger(__name__)

class AIOrchestratorService:
    def __init__(
        self,
        config_service: ConfigService,
        credential_service: CredentialService,
        persistence_service: SupabasePersistenceService,
        llm_provider: ChatGoogleGenerativeAI,
        mobula_adapter: MobulaAdapter,
        binance_adapter: BinanceAdapter,
        notification_service: NotificationService # Añadir NotificationService
    ):
        self.config_service = config_service
        self.credential_service = credential_service
        self.persistence_service = persistence_service
        self.llm = llm_provider
        self.mobula_adapter = mobula_adapter
        self.binance_adapter = binance_adapter
        self.notification_service = notification_service # Guardar instancia
        self.mcp_tools: List[BaseMCPTool] = []
        # La carga de herramientas MCP ahora debe ser asíncrona si depende de config asíncrona
        # Esto significa que __init__ no puede llamar a _load_mcp_tools directamente si es async.
        # Se necesitará un método de inicialización asíncrono separado o cargar las herramientas bajo demanda.
        # Por ahora, asumiremos que se llama a un método async_init después de la creación.
        # asyncio.create_task(self.async_init(default_user_id_if_known)) # Ejemplo

    async def async_init(self, user_id: Optional[str] = None):
        """Método de inicialización asíncrono para cargar configuraciones y herramientas."""
        # Si ConfigService requiere un user_id para su primera carga, debe proporcionarse.
        # O ConfigService podría tener un user_id por defecto o un método para establecerlo.
        await self._load_mcp_tools(user_id=user_id)


    async def _load_mcp_tools(self, user_id: Optional[str] = None):
        """
        Carga y configura las herramientas MCP basadas en la configuración del usuario.
        """
        logger.info(f"Cargando herramientas MCP para el usuario: {user_id}...")
        self.mcp_tools = []
        # Asegurarse de que user_id se pasa a get_user_configuration si es necesario.
        # ConfigService ahora maneja la lógica de user_id internamente si se setea en su init o con set_current_user_id.
        # Si AIOrchestratorService es específico de un usuario, ese user_id debe usarse.
        # Si es global, necesitará el user_id para cada operación.

        # Si el ConfigService fue inicializado con un user_id, get_user_configuration() podría no necesitarlo.
        # Si no, AIOrchestratorService debe gestionar el user_id.
        # Para este ejemplo, asumimos que ConfigService puede obtener la config del usuario actual
        # o que user_id se pasa explícitamente.

        # Si ConfigService tiene un _current_user_id, y AIOrchestratorService también lo conoce:
        # For global initialization, user_id might be FIXED_USER_ID or None if tools are generic.
        # If user_id is None, get_user_configuration might fetch a default/global config or no config.
        current_user_config = await self.config_service.get_user_configuration(user_id=user_id)

        if current_user_config and current_user_config.mcpServerPreferences: # Corregido a mcpServerPreferences
            for mcp_pref in current_user_config.mcpServerPreferences: # Corregido a mcpServerPreferences
                if mcp_pref.isEnabled: # Corregido a isEnabled
                    try:
                        # Lógica para seleccionar y crear la instancia de herramienta MCP adecuada
                        # basada en mcp_pref.type o mcp_pref.id
                        tool_instance: Optional[BaseMCPTool] = None
                        if mcp_pref.type == "mock_signal_provider": # Ejemplo
                            logger.info(f"Cargando MockMCPTool para MCP ID: {mcp_pref.id} para usuario {user_id}")
                            tool_instance = MockMCPTool.from_config(
                                mcp_config=mcp_pref.model_dump(), # Pasa el dict de la preferencia
                                credential_service=self.credential_service
                            )
                        # TODO: Añadir más tipos de MCP aquí
                        # elif mcp_pref.type == "ccxt_trending_coins":
                        #     tool_instance = CCXTTrendingCoinsTool.from_config(...)
                        else:
                            logger.warning(f"Tipo de MCP desconocido o no soportado: {mcp_pref.type} para MCP ID: {mcp_pref.id}")

                        if tool_instance:
                            self.mcp_tools.append(tool_instance)
                            logger.info(f"Herramienta MCP '{tool_instance.name}' cargada y habilitada.")
                    except Exception as e:
                        logger.error(f"Error al cargar la herramienta MCP para la preferencia {mcp_pref.id}: {e}", exc_info=True)
        
        if not self.mcp_tools:
            logger.info("No se cargaron herramientas MCP (ninguna configurada o habilitada).")
        else:
            logger.info(f"Total de {len(self.mcp_tools)} herramientas MCP cargadas.")


    async def process_mcp_signal(self, user_id: str, mcp_id: str, signal_data: Dict[str, Any]) -> Optional[Opportunity]: # UUID type hint later
        """
        Procesa una señal cruda recibida de un servidor MCP.
        Crea una entidad Opportunity en la base de datos.
        """
        logger.info(f"Procesando señal del MCP ID: {mcp_id} para usuario {user_id}. Datos: {signal_data}")

        # Obtener la configuración específica del usuario
        current_user_config = await self.config_service.get_user_configuration(user_id=user_id)
        if not current_user_config:
            logger.error(f"No se pudo obtener la configuración para el usuario {user_id}. No se puede procesar la señal MCP.")
            return None

        # Verificar si el Paper Trading está activo (AC1)
        # ConfigService.is_paper_trading_mode_active() ahora usa la config cacheada.
        # Es importante que la config para el user_id correcto esté cargada en ConfigService.
        # Una opción es que ConfigService tome user_id en is_paper_trading_mode_active
        # o que AIOrchestratorService asegure que ConfigService tiene el contexto del usuario.
        # Por ahora, asumimos que ConfigService.is_paper_trading_mode_active() funciona para el usuario actual
        # si su configuración fue cargada (lo cual hicimos arriba).
        if not self.config_service.is_paper_trading_mode_active(): 
            logger.info(f"Modo Paper Trading no está activo para el usuario {user_id}. Ignorando señal MCP.")
            return None

        # Validar que el MCP esté configurado y habilitado (AC1)
        mcp_is_valid = False
        if current_user_config.mcpServerPreferences: # Corregido a mcpServerPreferences
            for mcp_pref in current_user_config.mcpServerPreferences: # Corregido a mcpServerPreferences
                if mcp_pref.id == mcp_id and mcp_pref.isEnabled: # Corregido a isEnabled
                    mcp_is_valid = True
                    break
        
        if not mcp_is_valid:
            logger.warning(f"Señal recibida del MCP ID '{mcp_id}' para usuario {user_id}, pero no está configurado o habilitado. Ignorando.")
            return None

        try:
            # Crear la entidad Opportunity (AC2, AC3)
            opportunity_data = Opportunity(
                user_id=current_user_config.user_id, 
                source_type=OpportunitySourceType.MCP_SIGNAL,
                source_name=mcp_id, # Nombre/ID del MCP que originó la señal
                source_data=json.dumps(signal_data), # Almacenar payload original (AC4)
                status=OpportunityStatus.PENDING_AI_ANALYSIS,
                # Otros campos se llenarán más tarde (ej. symbol, ai_analysis)
                # o tendrán valores por defecto.
            )
            
            # Guardar la oportunidad en la base de datos
            saved_opportunity = await self.persistence_service.upsert_opportunity(opportunity_data.user_id, opportunity_data.model_dump())
            logger.info(f"Oportunidad creada y guardada con ID: {saved_opportunity.id} desde MCP: {mcp_id}")
            
            # Encolar/dirigir esta oportunidad para análisis de IA (Subtask 3.1)
            # En un sistema más complejo, esto podría ir a una cola de tareas (ej. Celery, Redis Stream).
            # Por ahora, llamaremos directamente al método de análisis.
            # Es importante que process_mcp_signal no espere el resultado del análisis si es largo.
            # analyze_opportunity_with_ai es async, así que podemos crear una tarea para que se ejecute en segundo plano.
            import asyncio
            asyncio.create_task(self.analyze_opportunity_with_ai(saved_opportunity))
            logger.info(f"Análisis de IA para la oportunidad {saved_opportunity.id} programado en segundo plano.")

            return saved_opportunity

        except Exception as e:
            logger.error(f"Error al procesar la señal del MCP {mcp_id}: {e}", exc_info=True)
            return None

    async def analyze_opportunity_with_ai(self, opportunity: Opportunity) -> Opportunity:
        """
        Orquesta el análisis de una oportunidad utilizando el LLM (Gemini) y las herramientas MCP disponibles.
        """
        if not opportunity:
            logger.warning("Se intentó analizar una oportunidad nula.")
            raise ValueError("La oportunidad no puede ser nula.")

        logger.info(f"Iniciando análisis de IA para la oportunidad ID: {opportunity.id}")
        opportunity.status = OpportunityStatus.AI_ANALYSIS_IN_PROGRESS
        await self.persistence_service.update_opportunity_status(opportunity.id, OpportunityStatus.AI_ANALYSIS_IN_PROGRESS)

        try:
            # Obtener la configuración del usuario para los prompts de estrategia y el modelo Gemini
            user_config = await self.config_service.get_user_configuration(user_id=opportunity.user_id)
            if not user_config or not user_config.aiStrategyConfigurations:
                raise AIAnalysisError("No se encontraron configuraciones de estrategia de IA para el usuario.")

            # Asumir que tomamos la primera configuración de estrategia si hay varias
            # TODO: Implementar lógica para seleccionar la configuración de estrategia adecuada si hay múltiples
            ai_strategy_config: Optional[AiStrategyConfiguration] = None
            if user_config.aiStrategyConfigurations:
                ai_strategy_config = user_config.aiStrategyConfigurations[0] # Tomar la primera por defecto
            
            if not ai_strategy_config:
                raise AIAnalysisError("No se encontró una configuración de estrategia de IA válida.")

            # Seleccionar el modelo Gemini (1.5 Pro/Flash) según la configuración
            gemini_model_name = ai_strategy_config.geminiModelName # Ahora se accede correctamente
            if not gemini_model_name:
                raise AIAnalysisError("Nombre del modelo Gemini no configurado en la estrategia de IA.")
            
            # Construir el prompt para Gemini
            strategy_prompt_template = ai_strategy_config.geminiPromptTemplate # Ahora se accede correctamente
            if not strategy_prompt_template:
                raise AIAnalysisError("Plantilla de prompt de análisis de oportunidad no configurada en la estrategia de IA.")

            # Inyectar datos de la oportunidad en el prompt
            source_data_dict = {}
            if opportunity.source_data: # Verificar si source_data no es None
                try:
                    source_data_dict = json.loads(opportunity.source_data)
                except json.JSONDecodeError as e:
                    # Log the error with exception info
                    logger.error(f"Failed to decode source_data JSON for opportunity ID: {opportunity.id}. Error: {e}", exc_info=True)
                    # Update status in DB immediately
                    opportunity.status = OpportunityStatus.AI_ANALYSIS_FAILED
                    await self.persistence_service.update_opportunity_status(opportunity.id, OpportunityStatus.AI_ANALYSIS_FAILED)
                    # Raise AIAnalysisError to be caught by the broader handler below, which will populate ai_analysis field
                    raise AIAnalysisError(f"Invalid source_data JSON format for opportunity ID: {opportunity.id}.") from e
            
            # Crear un mensaje humano con los detalles de la oportunidad
            human_message_content = strategy_prompt_template.format(
                opportunity_details=json.dumps(source_data_dict, indent=2),
                # Añadir otros campos relevantes de la oportunidad si el prompt los necesita
                opportunity_id=opportunity.id,
                source_name=opportunity.source_name
            )

            # Definir el prompt del agente
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="Eres un experto analista de trading de criptomonedas. Analiza la siguiente señal de oportunidad utilizando las herramientas disponibles para obtener información adicional si es necesario. Tu respuesta debe incluir una dirección sugerida (compra/venta) y un nivel de confianza numérico (0.0 a 1.0). Justifica tu análisis y tu nivel de confianza."),
                HumanMessage(content=human_message_content)
            ])

            # Preparar las herramientas MCP para que Gemini las pueda usar
            # LangChain Tools deben ser instancias de BaseTool.
            # Nuestras BaseMCPTool necesitan ser adaptadas a LangChain BaseTool si no lo son ya.
            # Asumimos que BaseMCPTool ya es compatible o se puede adaptar fácilmente.
            langchain_tools = [tool.to_langchain_tool() for tool in self.mcp_tools if tool.is_enabled] # Asumiendo un método to_langchain_tool()

            # Crear el agente
            agent = create_tool_calling_agent(self.llm, langchain_tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=langchain_tools, verbose=True) # verbose para debugging

            # Invocar al LLM (Gemini)
            ai_response = await agent_executor.ainvoke({"input": human_message_content}) # 'input' es el nombre de la variable esperada por el agente

            # Procesar ai_response['output'] para extraer análisis, confianza, etc.
            # Asumimos que la salida de Gemini será un JSON o un texto parseable.
            # Si es texto libre, se necesitará un parser más sofisticado o un segundo LLM.
            # Para esta implementación, intentaremos parsear un JSON esperado.
            
            raw_output = ai_response.get('output', '')
            suggested_action: Optional[str] = None
            calculated_confidence: Optional[float] = None
            reasoning_ai: Optional[str] = raw_output

            try:
                # Intentar parsear la salida como JSON si se espera un formato estructurado
                parsed_output = json.loads(raw_output)
                suggested_action = parsed_output.get("suggested_action")
                calculated_confidence = parsed_output.get("confidence")
                reasoning_ai = parsed_output.get("reasoning", raw_output) # Usar raw_output como fallback para reasoning si no está en JSON
            except json.JSONDecodeError:
                # El LLM idealmente debería devolver JSON. Si no, la funcionalidad es limitada.
                logger.warning(
                    f"Failed to parse LLM output as JSON for opportunity ID: {opportunity.id}. "
                    f"Raw output: '{raw_output}'. Attempting regex fallback."
                )
                
                # Fallback con Regex - Stretch Goal
                action_match = re.search(r'"action"\s*:\s*"?(BUY|SELL|HOLD)"?', raw_output, re.IGNORECASE)
                if action_match:
                    suggested_action = action_match.group(1).upper()
                    logger.info(f"Fallback regex extracted action: '{suggested_action}' for OID: {opportunity.id}")
                else:
                    logger.warning(f"Fallback regex failed to extract action for OID: {opportunity.id}")

                confidence_match = re.search(r'"confidence"\s*:\s*(\d\.\d+)', raw_output) # Busca ej: "confidence": 0.85
                if confidence_match:
                    try:
                        calculated_confidence = float(confidence_match.group(1))
                        logger.info(f"Fallback regex extracted confidence: {calculated_confidence} for OID: {opportunity.id}")
                    except ValueError:
                        logger.warning(f"Fallback regex extracted confidence value '{confidence_match.group(1)}' is not a valid float for OID: {opportunity.id}.")
                else:
                    logger.warning(f"Fallback regex failed to extract confidence for OID: {opportunity.id}")
                
                # reasoning_ai ya está seteado a raw_output por defecto, lo cual es un buen fallback.
                # Si el regex falla, suggested_action y calculated_confidence permanecerán None.

            # Actualizar el campo aiAnalysis de la entidad Opportunity
            opportunity.ai_analysis = AIAnalysis(
                calculatedConfidence=calculated_confidence,
                suggestedAction=suggested_action,
                reasoning_ai=reasoning_ai,
                rawAiOutput=raw_output,
                dataVerification=None, # Esto se llenará en la Task 2
                ai_model_used=gemini_model_name # Pasar el nombre del modelo
            )
            opportunity.status = OpportunityStatus.AI_ANALYSIS_COMPLETE 

        except AIAnalysisError as e:
            # This block will catch the AIAnalysisError raised from json.JSONDecodeError
            # as well as other AIAnalysisErrors raised directly in the try block.
            logger.error(f"AIAnalysisError for opportunity {opportunity.id}: {e}", exc_info=True)
            opportunity.status = OpportunityStatus.AI_ANALYSIS_FAILED
            # Ensure gemini_model_name is available or handled if error occurs before its definition
            current_gemini_model_name = 'N/A'
            try:
                current_gemini_model_name = gemini_model_name
            except NameError:
                logger.warning("gemini_model_name not defined when AIAnalysisError occurred.")

            opportunity.ai_analysis = AIAnalysis(
                calculatedConfidence=None,
                suggestedAction=None,
                rawAiOutput=None,
                dataVerification=None,
                reasoning_ai=f"Error de análisis: {str(e)}",
                ai_model_used=current_gemini_model_name
            )
        except Exception as e:
            logger.error(f"Unexpected error during AI analysis for opportunity {opportunity.id}: {e}", exc_info=True)
            opportunity.status = OpportunityStatus.AI_ANALYSIS_FAILED
            current_gemini_model_name = 'N/A'
            try:
                current_gemini_model_name = gemini_model_name
            except NameError:
                logger.warning("gemini_model_name not defined when Exception occurred.")
            
            opportunity.ai_analysis = AIAnalysis(
                calculatedConfidence=None,
                suggestedAction=None,
                rawAiOutput=None,
                dataVerification=None,
                reasoning_ai=f"Error inesperado: {str(e)}",
                ai_model_used=current_gemini_model_name
            )
        
        # Convertir el objeto AIAnalysis a JSON string antes de pasarlo a persistence_service
        # Asumiendo que update_opportunity_analysis espera un JSON string para ai_analysis
        # Si update_opportunity_analysis se actualiza para aceptar AIAnalysis directamente, esto cambiará.
        
        # --- INICIO DE MODIFICACIÓN PARA TASK 2.1 ---
        should_verify_data = False
        if opportunity.status == OpportunityStatus.AI_ANALYSIS_COMPLETE and \
           opportunity.ai_analysis and \
           opportunity.ai_analysis.calculatedConfidence is not None:
            
            confidence_threshold_paper = user_config.aiAnalysisConfidenceThresholds.paperTrading if user_config.aiAnalysisConfidenceThresholds else None
            
            if confidence_threshold_paper is not None: # Asegurarse de que el umbral no sea None
                if opportunity.ai_analysis.calculatedConfidence >= confidence_threshold_paper:
                    logger.info(f"Confianza de IA ({opportunity.ai_analysis.calculatedConfidence}) >= umbral ({confidence_threshold_paper}) para OID {opportunity.id}. Procediendo a verificación de datos.")
                    should_verify_data = True
                else:
                    logger.info(f"Confianza de IA ({opportunity.ai_analysis.calculatedConfidence}) < umbral ({confidence_threshold_paper}) para OID {opportunity.id}. Oportunidad será marcada como rechazada por IA.")
                    opportunity.status = OpportunityStatus.REJECTED_BY_AI # Se gestionará formalmente en Task 3
                    opportunity.status_reason = "Confianza de IA por debajo del umbral de Paper Trading."
            else:
                logger.warning(f"Umbral de confianza para Paper Trading no configurado para el usuario {opportunity.user_id}. No se procederá con la verificación de datos.")
        
        if should_verify_data:
            # --- INICIO DE MODIFICACIÓN PARA TASK 2.2 ---
            asset_symbol = opportunity.symbol if opportunity.symbol and opportunity.symbol.strip() else None # Ensure not empty string
            
            if not asset_symbol and opportunity.source_data:
                logger.info(f"opportunity.symbol is not set for OID: {opportunity.id}. Attempting to extract from source_data.")
                try:
                    # source_data_dict is already parsed earlier in the method.
                    # No need to parse json.loads(opportunity.source_data) again if it's already available.
                    # Assuming source_data_dict is in scope. If not, it needs to be parsed here.
                    # For this change, I'll assume source_data_dict from the earlier parsing is available.
                    # If source_data_dict is not guaranteed to be in scope here (e.g. if JSON parsing failed earlier and led to this path through some other logic)
                    # then it would need to be parsed here again with its own try-except.
                    # However, the current structure has JSON parsing of source_data for prompt construction happening before this.
                    # So, source_data_dict should be available.

                    potential_keys = [
                        "symbol", "Symbol", "SYMBOL",
                        "asset", "Asset", "ASSET",
                        "instrument", "Instrument", "INSTRUMENT",
                        "ticker", "Ticker", "TICKER",
                        "currency_pair", "CurrencyPair", "CURRENCY_PAIR",
                        "pair", "Pair", "PAIR"
                    ]
                    for key in potential_keys:
                        if key in source_data_dict:
                            value = source_data_dict[key]
                            if isinstance(value, str) and value.strip():
                                asset_symbol = value.strip()
                                logger.info(f"Extracted asset_symbol '{asset_symbol}' from source_data using key '{key}' for OID: {opportunity.id}.")
                                break # Found a symbol
                    
                    if not asset_symbol:
                        logger.warning(f"Could not extract a valid symbol from source_data for OID: {opportunity.id} using common keys.")

                except Exception as e: # Catching generic Exception if source_data_dict wasn't as expected or other issues.
                    logger.error(f"Error while trying to extract symbol from source_data for OID: {opportunity.id}. Error: {e}", exc_info=True)
            
            if not asset_symbol: # If still no symbol after all attempts
                logger.error(f"Failed to determine asset symbol for data verification for OID: {opportunity.id}. opportunity.symbol='{opportunity.symbol}', source_data check also failed.")
                opportunity.status = OpportunityStatus.AI_ANALYSIS_FAILED
                opportunity.status_reason = "Asset symbol not found for data verification."
                should_verify_data = False # Prevent data verification
            
            if should_verify_data and asset_symbol: # Re-check as asset_symbol might have been found
                logger.info(f"Proceeding with data verification for asset: {asset_symbol} (OID: {opportunity.id}).")
                verification_results: Dict[str, Any] = {"checks": []}
                data_verified_successfully = True # Asumir éxito inicialmente

                try:
                    # 1. Obtener datos de Mobula
                    mobula_data = await self.mobula_adapter.get_market_data(user_id=opportunity.user_id, symbol=asset_symbol)
                    if mobula_data:
                        logger.info(f"Datos de Mobula para {asset_symbol}: {mobula_data}")
                        verification_results["mobula_data"] = mobula_data
                        # Aquí se añadiría la lógica de la Subtask 2.3 para comparar y verificar
                    else:
                        logger.warning(f"No se obtuvieron datos de Mobula para {asset_symbol}.")
                        verification_results["mobula_data_error"] = "No data returned"
                        # data_verified_successfully = False # Podría ser un fallo parcial

                    # 2. Obtener datos de Binance (ej. ticker para precio y volumen)
                    # Binance usa símbolos como "BTCUSDT", Mobula podría usar "BTC" o "Bitcoin".
                    # Se necesita una normalización o mapeo de símbolos si son diferentes.
                    # Por ahora, asumimos que opportunity.symbol es compatible con Binance si es un par.
                    binance_symbol = asset_symbol 
                    if "/" in asset_symbol: # Convertir "BTC/USDT" a "BTCUSDT"
                        binance_symbol = asset_symbol.replace("/", "")
                    
                    binance_data = await self.binance_adapter.get_ticker_24hr(symbol=binance_symbol)
                    if binance_data:
                        logger.info(f"Datos de Binance para {binance_symbol}: {binance_data}")
                        verification_results["binance_data"] = binance_data
                        # Aquí se añadiría la lógica de la Subtask 2.3
                    else:
                        logger.warning(f"No se obtuvieron datos de Binance para {binance_symbol}.")
                        verification_results["binance_data_error"] = "No data returned"
                        # data_verified_successfully = False

                    # --- INICIO DE LÓGICA PARA SUBTASK 2.3 ---
                    PRICE_DISCREPANCY_THRESHOLD_PERCENT = user_config.aiAnalysisConfidenceThresholds.dataVerificationPriceDiscrepancyPercent if user_config.aiAnalysisConfidenceThresholds else 5.0
                    MIN_VOLUME_THRESHOLD_QUOTE = user_config.aiAnalysisConfidenceThresholds.dataVerificationMinVolumeQuote if user_config.aiAnalysisConfidenceThresholds else 1000.0

                    # 1. Verificación de Precio
                    mobula_price: Optional[float] = None
                    mobula_quote_currency: Optional[str] = None
                    if mobula_data and isinstance(mobula_data.get("price"), (int, float)):
                        mobula_price = float(mobula_data["price"])
                        mobula_quote_currency = mobula_data.get("price_currency") or mobula_data.get("quote_symbol") # Common fields for quote currency
                        if not mobula_quote_currency and isinstance(mobula_data.get("contracts"), list) and mobula_data["contracts"]:
                            # Fallback if price_currency is not at top level, check under contracts (Mobula specific)
                            mobula_quote_currency = mobula_data["contracts"][0].get("quote_currency", {}).get("symbol")


                    binance_price: Optional[float] = None
                    binance_quote_currency: Optional[str] = None
                    if binance_data and isinstance(binance_data.get("lastPrice"), str):
                        try:
                            binance_price = float(binance_data["lastPrice"])
                            # Infer Binance quote currency from the trading pair symbol
                            # Assumes standard pair format like BTCUSDT, ETHBTC etc.
                            if len(binance_symbol) > 3: # Basic check
                                if binance_symbol.upper().endswith("USDT"): binance_quote_currency = "USDT"
                                elif binance_symbol.upper().endswith("USDC"): binance_quote_currency = "USDC"
                                elif binance_symbol.upper().endswith("BUSD"): binance_quote_currency = "BUSD" # Common stablecoin
                                elif binance_symbol.upper().endswith("TUSD"): binance_quote_currency = "TUSD" # Common stablecoin
                                elif binance_symbol.upper().endswith("USD"): binance_quote_currency = "USD" 
                                elif binance_symbol.upper().endswith("EUR"): binance_quote_currency = "EUR"
                                elif binance_symbol.upper().endswith("BTC"): binance_quote_currency = "BTC"
                                elif binance_symbol.upper().endswith("ETH"): binance_quote_currency = "ETH"
                                # Add more common quote currencies if needed
                            logger.info(f"Extracted Binance quote currency: {binance_quote_currency} from symbol {binance_symbol}")
                        except ValueError:
                            logger.warning(f"No se pudo convertir el precio de Binance '{binance_data['lastPrice']}' a float para {binance_symbol}.")

                    price_check_result = {
                        "check_type": "price_comparison",
                        "status": "pending", # Will be updated
                        "mobula_price": mobula_price,
                        "mobula_quote_currency": mobula_quote_currency,
                        "binance_price": binance_price,
                        "binance_quote_currency": binance_quote_currency,
                    }

                    if mobula_price is None or binance_price is None:
                        missing_source = []
                        if mobula_price is None: missing_source.append("Mobula")
                        if binance_price is None: missing_source.append("Binance")
                        message = f"Price data missing from {', '.join(missing_source)}."
                        logger.warning(f"{message} for {asset_symbol}. Cannot perform price comparison.")
                        price_check_result["status"] = "failed"
                        price_check_result["message"] = message
                        data_verified_successfully = False
                    else:
                        # Both prices are available, proceed with comparison
                        perform_comparison = True
                        if mobula_quote_currency and binance_quote_currency and mobula_quote_currency.upper() != binance_quote_currency.upper():
                            # Handle USD vs USDT as a special case (often considered equivalent or close)
                            if (mobula_quote_currency.upper() == "USD" and binance_quote_currency.upper() == "USDT") or \
                               (mobula_quote_currency.upper() == "USDT" and binance_quote_currency.upper() == "USD"):
                                warning_message = f"Quote currency mismatch for {asset_symbol}: Mobula ({mobula_quote_currency}) vs Binance ({binance_quote_currency}). Comparing as if equivalent."
                                logger.warning(warning_message)
                                price_check_result["message"] = warning_message # Add to results
                            else:
                                error_message = f"Critical quote currency mismatch for {asset_symbol}: Mobula ({mobula_quote_currency}) vs Binance ({binance_quote_currency}). Price comparison skipped."
                                logger.error(error_message)
                                price_check_result["status"] = "failed" # Fail if critical mismatch
                                price_check_result["message"] = error_message
                                data_verified_successfully = False
                                perform_comparison = False
                        
                        if perform_comparison:
                            price_diff_percent = 0.0
                            if binance_price > 0: # Avoid division by zero
                                price_diff_percent = (abs(mobula_price - binance_price) / binance_price) * 100
                            price_check_result["difference_percent"] = round(price_diff_percent, 2)

                            if price_diff_percent > PRICE_DISCREPANCY_THRESHOLD_PERCENT:
                                discrepancy_message = f"Discrepancia de precio significativa para {asset_symbol}: Mobula={mobula_price} {mobula_quote_currency}, Binance={binance_price} {binance_quote_currency} ({price_diff_percent:.2f}% > {PRICE_DISCREPANCY_THRESHOLD_PERCENT}%)"
                                logger.warning(discrepancy_message)
                                price_check_result["status"] = "failed"
                                price_check_result["message"] = price_check_result.get("message", "") + " " + discrepancy_message if price_check_result.get("message") else discrepancy_message
                                data_verified_successfully = False
                            else:
                                price_check_result["status"] = "passed"
                                if not price_check_result.get("message"): # Avoid overwriting currency mismatch warning
                                    price_check_result["message"] = "Price comparison passed."
                    
                    verification_results["checks"].append(price_check_result)

                    # 2. Verificación de Volumen (usando Binance como referencia principal para el par de trading)
                    # Incorporate Mobula Volume
                    mobula_volume_details = {"source": "Mobula"}
                    if mobula_data:
                        mobula_vol = mobula_data.get('volume') or mobula_data.get('volume_24h') # Common keys for volume
                        if mobula_vol is not None:
                            mobula_volume_details['volume'] = mobula_vol
                            # Try to get volume quote currency, might be same as price or specified
                            mobula_volume_details['quote_currency'] = mobula_data.get('volume_quote_currency') or mobula_quote_currency # Use price quote if specific not found
                        else:
                            mobula_volume_details['error'] = "Volume data not found in Mobula response."
                    else:
                        mobula_volume_details['error'] = "No Mobula data to extract volume."
                    
                    volume_check_binance_details = {
                        "check_type": "volume_check_binance",
                        "status": "pending",
                        "sources": [mobula_volume_details] # Add Mobula volume info here
                    }
                    
                    binance_volume_str = None
                    if binance_data and isinstance(binance_data.get("quoteVolume"), str): # 'quoteVolume' es el volumen en la moneda de cotización (ej. USDT)
                        binance_volume_str = binance_data["quoteVolume"]

                    binance_volume = None
                    if binance_volume_str:
                        try:
                            binance_volume = float(binance_volume_str)
                        except ValueError:
                             logger.warning(f"No se pudo convertir el volumen de Binance '{binance_volume_str}' a float para {binance_symbol}.")
                    
                    binance_volume_source_entry = {"source": "Binance"}
                    if binance_volume is not None: # Asegurarse de que binance_volume no sea None antes de comparar
                        binance_volume_source_entry['volume'] = binance_volume
                        binance_volume_source_entry['quote_currency'] = binance_quote_currency # From price check
                        if binance_volume < MIN_VOLUME_THRESHOLD_QUOTE:
                            logger.warning(f"Volumen de Binance bajo para {binance_symbol}: {binance_volume} {binance_quote_currency} < {MIN_VOLUME_THRESHOLD_QUOTE} {binance_quote_currency}")
                            volume_check_binance_details["status"] = "failed"
                            volume_check_binance_details["message"] = f"Volumen de trading en Binance ({binance_volume} {binance_quote_currency}) por debajo del umbral mínimo ({MIN_VOLUME_THRESHOLD_QUOTE} {binance_quote_currency})."
                            data_verified_successfully = False # Considerar si esto debe ser un fallo duro
                        else:
                            volume_check_binance_details["status"] = "passed"
                            volume_check_binance_details["message"] = f"Binance volume ({binance_volume} {binance_quote_currency}) meets threshold."
                    else:
                        logger.warning(f"No se pudo obtener el volumen de Binance para {binance_symbol} para verificación.")
                        volume_check_binance_details["status"] = "warning" # Or "failed" if volume is critical
                        volume_check_binance_details["message"] = "No se pudo obtener el volumen de Binance para verificación."
                        binance_volume_source_entry['error'] = "Binance volume data not found or invalid."
                        # data_verified_successfully = False # Decide if this is a hard fail
                    
                    volume_check_binance_details["sources"].append(binance_volume_source_entry)
                    verification_results["checks"].append(volume_check_binance_details)
                    # --- FIN DE LÓGICA PARA SUBTASK 2.3 ---
                    
                    if opportunity.ai_analysis: # Asegurarse de que ai_analysis existe
                        opportunity.ai_analysis.dataVerification = verification_results # Subtask 2.4 (parcial)
                    
                    # El estado final de la oportunidad (analysis_complete o rejected_by_ai)
                    # se determinará en la Task 3 basado en data_verified_successfully.
                    # Por ahora, si llegamos aquí, el análisis de IA fue bueno.
                    # Si la verificación de datos falla (lógica de 2.3), Task 3 lo manejará.

                except MobulaAPIError as e:
                    logger.error(f"Error de API Mobula durante la verificación de datos para {asset_symbol}: {e}")
                    verification_results["mobula_api_error"] = str(e)
                    data_verified_successfully = False
                except BinanceAPIError as e:
                    logger.error(f"Error de API Binance durante la verificación de datos para {asset_symbol}: {e}")
                    verification_results["binance_api_error"] = str(e)
                    data_verified_successfully = False
                except Exception as e:
                    logger.error(f"Error inesperado durante la verificación de datos para {asset_symbol}: {e}", exc_info=True)
                    verification_results["unexpected_error"] = str(e)
                    data_verified_successfully = False
                
                if opportunity.ai_analysis: # Actualizar dataVerification incluso si hay errores
                    opportunity.ai_analysis.dataVerification = verification_results

                if not data_verified_successfully:
                    opportunity.status = OpportunityStatus.REJECTED_BY_AI 
                    opportunity.status_reason = "Falló la verificación de datos de mercado."
            # --- FIN DE MODIFICACIÓN PARA TASK 2.2 (y parte de 2.4) ---

        # --- FIN DE MODIFICACIÓN PARA TASK 2.1 ---

        ai_analysis_json = opportunity.ai_analysis.model_dump_json() if opportunity.ai_analysis else None
        await self.persistence_service.update_opportunity_analysis(
            opportunity_id=opportunity.id,
            status=opportunity.status, # El estado puede haber cambiado
            ai_analysis=ai_analysis_json,
            confidence_score=opportunity.ai_analysis.calculatedConfidence if opportunity.ai_analysis else None,
            suggested_action=opportunity.ai_analysis.suggestedAction if opportunity.ai_analysis else None,
            status_reason=opportunity.status_reason # Pasar el status_reason
        )
        logger.info(f"Análisis de IA y verificación de datos/umbral completados para OID: {opportunity.id}. Estado final: {opportunity.status}")

        # --- INICIO DE MODIFICACIÓN PARA TASK 3.3 ---
        # AC5: Notificar si la oportunidad es validada con alta confianza
        # Una oportunidad está validada si su estado final es AI_ANALYSIS_COMPLETE
        # (lo que implica que la confianza fue suficiente y la verificación de datos, si se hizo, fue exitosa)
        # y la confianza es superior al umbral de Paper Trading.
        if opportunity.status == OpportunityStatus.AI_ANALYSIS_COMPLETE:
            # La comprobación del umbral ya se hizo para decidir si `should_verify_data` o si se rechazaba.
            # Si el estado es AI_ANALYSIS_COMPLETE, significa que pasó ese umbral (o no se requirió verificación y la confianza era buena).
            # Y que la verificación de datos, si se hizo, fue exitosa.
            
            # Re-verificar la confianza contra el umbral para la notificación (AC5 específicamente menciona >80% o umbral)
            confidence_threshold_paper = user_config.aiAnalysisConfidenceThresholds.paperTrading if user_config.aiAnalysisConfidenceThresholds else None
            notify_high_confidence = False
            if confidence_threshold_paper is not None and opportunity.ai_analysis and opportunity.ai_analysis.calculatedConfidence is not None:
                if opportunity.ai_analysis.calculatedConfidence >= confidence_threshold_paper:
                    notify_high_confidence = True
            
            if notify_high_confidence:
                logger.info(f"Enviando notificación de alta confianza para oportunidad validada OID: {opportunity.id}")
                try:
                    title = f"Nueva Oportunidad de Paper Trading Validada: {opportunity.symbol or opportunity.source_name}"
                    message = (
                        f"Oportunidad de trading validada con alta confianza para {opportunity.symbol or opportunity.source_name}.\n"
                        f"Acción Sugerida: {opportunity.ai_analysis.suggestedAction if opportunity.ai_analysis else 'N/A'}\n"
                        f"Confianza IA: {opportunity.ai_analysis.calculatedConfidence*100:.2f}%" if opportunity.ai_analysis and opportunity.ai_analysis.calculatedConfidence is not None else "N/A"
                        # Podríamos añadir más detalles del reasoning_ai o dataVerification si es relevante para la notificación.
                    )
                    
                    # Enviar a UI y Telegram según preferencias del usuario (NotificationService maneja esto internamente)
                    # Por ahora, enviaremos a ambos si están configurados.
                    # El NotificationService debería tener lógica para consultar UserConfiguration.notificationPreferences
                    
                    # Para simplificar aquí, asumimos que NotificationService.send_notification
                    # puede tomar un event_type y luego internamente decide los canales.
                    # NotificationService ahora manejará la lógica de canales internamente
                    # basado en las preferencias del usuario y el event_type.
                    await self.notification_service.send_notification(
                        user_id=opportunity.user_id, # Ya es str
                        title=title,
                        message=message,
                        event_type="OPPORTUNITY_ANALYZED_HIGH_CONFIDENCE_PAPER",
                        opportunity_id=opportunity.id # Pasar opportunity_id
                        # el campo 'channel' ya no se pasa desde aquí
                    )
                except Exception as e:
                    logger.error(f"Error al solicitar el envío de notificación para oportunidad {opportunity.id}: {e}", exc_info=True)
        # --- FIN DE MODIFICACIÓN PARA TASK 3.3 ---

        return opportunity

    def get_available_mcp_tools(self) -> List[BaseMCPTool]:
        """Devuelve la lista de herramientas MCP cargadas y habilitadas."""
        return [tool for tool in self.mcp_tools if tool.is_enabled]
