import json
import logging
import json
import logging
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

    async def async_init(self, user_id: Optional[Any] = None): # UUID type hint later
        """Método de inicialización asíncrono para cargar configuraciones y herramientas."""
        # Si ConfigService requiere un user_id para su primera carga, debe proporcionarse.
        # O ConfigService podría tener un user_id por defecto o un método para establecerlo.
        await self._load_mcp_tools(user_id=user_id)


    async def _load_mcp_tools(self, user_id: Optional[Any] = None): # UUID type hint later
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
        current_user_config = await self.config_service.get_user_configuration(user_id=user_id)

        if current_user_config and current_user_config.mcpServerPreferences: # Corregido a mcpServerPreferences
            for mcp_pref in current_user_config.mcpServerPreferences: # Corregido a mcpServerPreferences
                if mcp_pref.isEnabled: # Corregido a isEnabled
                    try:
                        # Lógica para seleccionar y crear la instancia de herramienta MCP adecuada
                        # basada en mcp_pref.type o mcp_pref.id
                        tool_instance: Optional[BaseMCPTool] = None
                        if mcp_pref.type == "mock_signal_provider": # Ejemplo
                            logger.info(f"Cargando MockMCPTool para MCP ID: {mcp_pref.id}")
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


    async def process_mcp_signal(self, user_id: Any, mcp_id: str, signal_data: Dict[str, Any]) -> Optional[Opportunity]: # UUID type hint later
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
                    logger.error(f"Error al parsear source_data de la oportunidad {opportunity.id}: {e}", exc_info=True)
                    raise AIAnalysisError("Datos de origen de la oportunidad inválidos.")
            
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
                reasoning_ai = parsed_output.get("reasoning", raw_output)
            except json.JSONDecodeError:
                logger.warning(f"La salida de Gemini no es un JSON válido para la oportunidad {opportunity.id}. Procesando como texto plano.")
                # Si no es JSON, intentar extraer con regex o simplemente usar el texto completo
                # Para este ejemplo, si no es JSON, la confianza y acción serán None a menos que se implemente un parser de texto.
                # Podríamos usar otro LLM para extraer esto de texto libre si es necesario.
                pass # Mantener los valores None o usar el raw_output como razonamiento

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
            logger.error(f"Error de configuración o análisis de IA para la oportunidad {opportunity.id}: {e}", exc_info=True)
            opportunity.status = OpportunityStatus.AI_ANALYSIS_FAILED
            opportunity.ai_analysis = AIAnalysis(
                calculatedConfidence=None,
                suggestedAction=None,
                rawAiOutput=None,
                dataVerification=None,
                reasoning_ai=f"Error de análisis: {str(e)}",
                ai_model_used=gemini_model_name # Incluir el modelo incluso en caso de error
            )
        except Exception as e:
            logger.error(f"Error inesperado durante el análisis de IA para la oportunidad {opportunity.id}: {e}", exc_info=True)
            opportunity.status = OpportunityStatus.AI_ANALYSIS_FAILED
            opportunity.ai_analysis = AIAnalysis(
                calculatedConfidence=None,
                suggestedAction=None,
                rawAiOutput=None,
                dataVerification=None,
                reasoning_ai=f"Error inesperado: {str(e)}",
                ai_model_used=gemini_model_name # Incluir el modelo incluso en caso de error
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
            asset_symbol = opportunity.symbol # Asumir que el símbolo está en opportunity.symbol
            if not asset_symbol:
                # Intentar obtener el símbolo de source_data si no está en opportunity.symbol
                if opportunity.source_data:
                    try:
                        source_data_dict = json.loads(opportunity.source_data)
                        asset_symbol = source_data_dict.get("symbol") or source_data_dict.get("asset") # Comunes nombres de campo
                    except json.JSONDecodeError:
                        logger.error(f"No se pudo parsear source_data para OID {opportunity.id} para obtener el símbolo.")
                
                if not asset_symbol:
                    logger.error(f"No se pudo determinar el símbolo del activo para la verificación de datos para OID {opportunity.id}.")
                    opportunity.status = OpportunityStatus.AI_ANALYSIS_FAILED # O un nuevo estado como DATA_VERIFICATION_FAILED
                    opportunity.status_reason = "No se pudo determinar el símbolo del activo para la verificación de datos."
                    # No continuar con la verificación si no hay símbolo
                    should_verify_data = False # Prevenir la ejecución de la lógica de verificación de datos más abajo

            if should_verify_data and asset_symbol: # Volver a comprobar should_verify_data por si cambió
                logger.info(f"Iniciando verificación de datos para el activo {asset_symbol} (OID: {opportunity.id}).")
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
                    mobula_price = None
                    if mobula_data and isinstance(mobula_data.get("price"), (int, float)):
                        mobula_price = float(mobula_data["price"])
                    
                    binance_price_str = None
                    if binance_data and isinstance(binance_data.get("lastPrice"), str):
                        binance_price_str = binance_data["lastPrice"]
                    
                    binance_price = None
                    if binance_price_str:
                        try:
                            binance_price = float(binance_price_str)
                        except ValueError:
                            logger.warning(f"No se pudo convertir el precio de Binance '{binance_price_str}' a float para {binance_symbol}.")
                    
                    # 1. Verificación de Precio
                    mobula_price = None
                    if mobula_data and isinstance(mobula_data.get("price"), (int, float)):
                        mobula_price = float(mobula_data["price"])
                    
                    binance_price_str = None
                    if binance_data and isinstance(binance_data.get("lastPrice"), str):
                        binance_price_str = binance_data["lastPrice"]
                    
                    binance_price = None
                    if binance_price_str:
                        try:
                            binance_price = float(binance_price_str)
                        except ValueError:
                            logger.warning(f"No se pudo convertir el precio de Binance '{binance_price_str}' a float para {binance_symbol}.")
                    
                    if mobula_price is not None and binance_price is not None:
                        price_diff_percent = 0.0 # Inicializar como float
                        if binance_price > 0: # Evitar división por cero
                            price_diff_percent = (abs(mobula_price - binance_price) / binance_price) * 100
                        
                        if price_diff_percent > PRICE_DISCREPANCY_THRESHOLD_PERCENT:
                            logger.warning(f"Discrepancia de precio significativa para {asset_symbol}: Mobula={mobula_price}, Binance={binance_price} ({price_diff_percent:.2f}% > {PRICE_DISCREPANCY_THRESHOLD_PERCENT}%)")
                            verification_results["checks"].append({
                                "check_type": "price_comparison",
                                "status": "failed",
                                "mobula_price": mobula_price,
                                "binance_price": binance_price,
                                "difference_percent": round(price_diff_percent, 2),
                                "threshold_percent": PRICE_DISCREPANCY_THRESHOLD_PERCENT,
                                "message": "Discrepancia de precio significativa entre Mobula y Binance."
                            })
                            data_verified_successfully = False
                        else:
                            verification_results["checks"].append({
                                "check_type": "price_comparison",
                                "status": "passed",
                                "mobula_price": mobula_price,
                                "binance_price": binance_price,
                                "difference_percent": round(price_diff_percent, 2)
                            })
                    else: # Si uno o ambos precios son None
                        logger.warning(f"No se pudieron obtener precios de Mobula o de Binance para {asset_symbol} para comparación.")
                        verification_results["checks"].append({
                            "check_type": "price_comparison",
                            "status": "warning",
                            "message": "No se pudieron obtener precios de Mobula o Binance para comparación."
                        })
                        # data_verified_successfully = False # Podría ser un fallo si la comparación de precios es crítica
                    
                    # 2. Verificación de Volumen (usando Binance como referencia principal para el par de trading)
                    binance_volume_str = None
                    if binance_data and isinstance(binance_data.get("quoteVolume"), str): # 'quoteVolume' es el volumen en la moneda de cotización (ej. USDT)
                        binance_volume_str = binance_data["quoteVolume"]

                    binance_volume = None
                    if binance_volume_str:
                        try:
                            binance_volume = float(binance_volume_str)
                        except ValueError:
                             logger.warning(f"No se pudo convertir el volumen de Binance '{binance_volume_str}' a float para {binance_symbol}.")
                    
                    if binance_volume is not None: # Asegurarse de que binance_volume no sea None antes de comparar
                        if binance_volume < MIN_VOLUME_THRESHOLD_QUOTE:
                            logger.warning(f"Volumen de Binance bajo para {binance_symbol}: {binance_volume} < {MIN_VOLUME_THRESHOLD_QUOTE}")
                            verification_results["checks"].append({
                                "check_type": "volume_check_binance",
                                "status": "failed",
                                "quote_volume": binance_volume,
                                "threshold_quote": MIN_VOLUME_THRESHOLD_QUOTE,
                                "message": "Volumen de trading en Binance por debajo del umbral mínimo."
                            })
                            data_verified_successfully = False # Considerar si esto debe ser un fallo duro
                        else:
                            verification_results["checks"].append({
                                "check_type": "volume_check_binance",
                                "status": "passed",
                                "quote_volume": binance_volume
                            })
                    else:
                        logger.warning(f"No se pudo obtener el volumen de Binance para {binance_symbol} para verificación.")
                        # Podría ser un fallo si el volumen es crítico
                        # data_verified_successfully = False 
                        verification_results["checks"].append({
                            "check_type": "volume_check_binance",
                            "status": "warning",
                            "message": "No se pudo obtener el volumen de Binance para verificación."
                        })
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
                    # O podemos llamar a send_notification por cada canal deseado.
                    
                    # Ejemplo de envío a Telegram (asumiendo que el usuario tiene Telegram configurado)
                    if user_config.enableTelegramNotifications and user_config.telegramChatId:
                         await self.notification_service.send_notification(
                            user_id=opportunity.user_id,
                            title=title,
                            message=message,
                            channel="telegram", # Especificar canal
                            event_type="OPPORTUNITY_ANALYZED_HIGH_CONFIDENCE_PAPER" # EventType sugerido
                        )
                    
                    # Ejemplo de envío a UI (esto sería más complejo, podría ser un evento WebSocket)
                    # Por ahora, NotificationService podría loguearlo o emitir un evento interno.
                    await self.notification_service.send_notification(
                        user_id=opportunity.user_id,
                        title=title,
                        message=message,
                        channel="ui", # Especificar canal
                        event_type="OPPORTUNITY_ANALYZED_HIGH_CONFIDENCE_PAPER"
                    )

                except Exception as e:
                    logger.error(f"Error al enviar notificación para oportunidad {opportunity.id}: {e}", exc_info=True)
        # --- FIN DE MODIFICACIÓN PARA TASK 3.3 ---

        return opportunity

    def get_available_mcp_tools(self) -> List[BaseMCPTool]:
        """Devuelve la lista de herramientas MCP cargadas y habilitadas."""
        return [tool for tool in self.mcp_tools if tool.is_enabled]
