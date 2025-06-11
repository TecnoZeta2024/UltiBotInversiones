# src/ultibot_ui/dialogs/strategy_config_dialog.py
"""
Módulo para el diálogo de configuración de estrategias de trading.
"""
import logging
from typing import Optional, List # Importar Optional y List
import re # Añadido para limpiar la entrada de apalancamiento
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QTextEdit, QComboBox, QPushButton, QFormLayout, 
                             QDialogButtonBox, QMessageBox, QStackedWidget, QWidget, QGroupBox, QCheckBox) # Añadido QCheckBox
from PyQt5.QtCore import Qt

# Provisional: Importar desde la vista hasta que se muevan a un lugar compartido o se definan correctamente
from ..views.strategy_management_view import BaseStrategyType, TradingStrategyConfig 
from ..services.api_client import UltiBotAPIClient, APIError
# from ....shared.data_types import UserConfiguration # Para aiStrategyConfigurations

logger = logging.getLogger(__name__)

class StrategyConfigDialog(QDialog):
    """
    Diálogo modal para crear y editar configuraciones de TradingStrategyConfig.
    """
    def __init__(self, api_client: UltiBotAPIClient, 
                 strategy_config: Optional[TradingStrategyConfig] = None, 
                 ai_profiles: Optional[List[dict]] = None, # Asumiendo que ai_profiles son dicts o Pydantic models
                 is_duplicating: bool = False, # Nuevo parámetro
                 parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.strategy_config = strategy_config # Si is_duplicating, esto es una plantilla
        self.ai_profiles = ai_profiles or []
        self.is_duplicating = is_duplicating
        
        # Si estamos duplicando, no estamos en modo edición (se creará una nueva estrategia)
        self.is_edit_mode = (self.strategy_config is not None) and not self.is_duplicating

        if self.is_edit_mode:
            self.setWindowTitle("Editar Configuración de Estrategia")
        elif self.is_duplicating:
            self.setWindowTitle("Duplicar Configuración de Estrategia (Crear Nueva)")
        else:
            self.setWindowTitle("Crear Nueva Configuración de Estrategia")
        self.setMinimumWidth(600) # Ajustar según sea necesario

        self._init_ui()
        if self.is_edit_mode or self.is_duplicating: # Cargar datos si es edición o duplicación
            self._load_data_for_edit() # _load_data_for_edit debe manejar el caso de duplicación (ej. limpiar ID)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # configName
        self.config_name_edit = QLineEdit()
        self.config_name_error_label = QLabel()
        self.config_name_error_label.setStyleSheet("color: red;")
        self.config_name_error_label.setVisible(False)
        form_layout.addRow("Nombre de Configuración:", self.config_name_edit)
        form_layout.addRow("", self.config_name_error_label)


        # baseStrategyType
        self.base_strategy_type_combo = QComboBox()
        for strategy_type in BaseStrategyType:
            self.base_strategy_type_combo.addItem(strategy_type.value, strategy_type)
        self.base_strategy_type_combo.currentIndexChanged.connect(self._on_base_strategy_type_changed)
        form_layout.addRow("Tipo de Estrategia Base:", self.base_strategy_type_combo)

        # description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Descripción opcional de la estrategia...")
        self.description_edit.setFixedHeight(80)
        form_layout.addRow("Descripción:", self.description_edit)

        # Parameters (Dynamic Section)
        self.parameters_stack = QStackedWidget()
        self._init_parameter_widgets() # Crear widgets para cada tipo de parámetro
        form_layout.addRow("Parámetros Específicos:", self.parameters_stack)
        self._on_base_strategy_type_changed(0) # Mostrar parámetros para el tipo inicial

        # --- Applicability Rules ---
        applicability_group = QGroupBox("Reglas de Aplicabilidad")
        applicability_layout = QFormLayout(applicability_group)
        
        self.applicability_pairs_edit = QLineEdit()
        self.applicability_pairs_edit.setPlaceholderText("Ej: BTC/USDT,ETH/USDT")
        self.applicability_pairs_edit.setToolTip("Lista de pares de trading explícitos, separados por comas.")
        applicability_layout.addRow("Pares Explícitos:", self.applicability_pairs_edit)

        self.include_all_spot_checkbox = QCheckBox("Incluir todos los pares SPOT disponibles")
        self.include_all_spot_checkbox.setToolTip("Si se marca, la estrategia se aplicará a todos los pares SPOT, ignorando Pares Explícitos y Filtro Dinámico para SPOT.")
        applicability_layout.addRow(self.include_all_spot_checkbox)
        
        self.dynamic_filter_watchlist_edit = QLineEdit()
        self.dynamic_filter_watchlist_edit.setPlaceholderText("Ej: watchlist_id_1,watchlist_id_2")
        self.dynamic_filter_watchlist_edit.setToolTip("IDs de watchlists (separados por coma) para filtrar dinámicamente los pares.")
        applicability_layout.addRow("IDs de Watchlist (Filtro Dinámico):", self.dynamic_filter_watchlist_edit)
        
        form_layout.addRow(applicability_group)

        # --- AI Analysis Profile ---
        self.ai_profile_combo = QComboBox()
        self.ai_profile_combo.addItem("Ninguno (Usar Default del Sistema)", None)
        # TODO: Cargar perfiles de IA desde self.ai_profiles
        # for profile in self.ai_profiles:
        #     self.ai_profile_combo.addItem(profile.name, profile.id) 
        self.ai_profile_combo.setToolTip("Seleccionar un perfil de configuración de IA específico para esta estrategia.")
        form_layout.addRow("Perfil de Análisis IA:", self.ai_profile_combo)
        
        # --- Risk Parameters Override ---
        risk_override_group = QGroupBox("Sobrescritura de Parámetros de Riesgo (Opcional)")
        risk_override_layout = QFormLayout(risk_override_group)
        risk_override_group.setCheckable(True) # Permitir habilitar/deshabilitar el grupo
        risk_override_group.setChecked(False) # Deshabilitado por defecto

        # Ejemplo de campos de riesgo (estos deberían venir de RiskProfileSettings)
        self.risk_daily_capital_edit = QLineEdit()
        self.risk_daily_capital_edit.setPlaceholderText("Ej: 1.5 (% del capital total)")
        self.risk_daily_capital_edit.setToolTip("Porcentaje máximo del capital total a arriesgar en un día.")
        risk_override_layout.addRow("Riesgo Capital Diario (%):", self.risk_daily_capital_edit)

        self.risk_per_trade_edit = QLineEdit()
        self.risk_per_trade_edit.setPlaceholderText("Ej: 0.5 (% del capital de la operación)")
        self.risk_per_trade_edit.setToolTip("Porcentaje máximo del capital asignado a una operación a arriesgar.")
        risk_override_layout.addRow("Riesgo por Operación (%):", self.risk_per_trade_edit)
        
        # Se podrían añadir más campos aquí (TP, SL, etc.)
        form_layout.addRow(risk_override_group)

        main_layout.addLayout(form_layout)

        # Botones
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._save_config)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def _clear_form_errors(self):
        """Limpia todos los mensajes de error del formulario."""
        self.config_name_error_label.setText("")
        self.config_name_error_label.setVisible(False)
        # TODO: Limpiar errores de otros campos cuando se añadan sus QLabels

    def _init_parameter_widgets(self):
        """
        Inicializa los QStackedWidget para los parámetros de cada tipo de estrategia.
        Esto es un placeholder y necesitará implementación real.
        """
        # Placeholder: Crear un QWidget simple para cada tipo de estrategia
        # En una implementación real, estos serían QGroupBox con QFormLayouts específicos.
        for strategy_type in BaseStrategyType:
            # TODO: Crear widgets específicos para ScalpingParameters, DayTradingParameters, etc.
            # Por ahora, un QLabel como placeholder.
            params_widget = QWidget()
            params_layout = QVBoxLayout(params_widget)
            
            group_box = QGroupBox(f"Parámetros para {strategy_type.value}")
            group_layout = QFormLayout(group_box)
            
            # Crear campos de ejemplo para cada tipo de estrategia
            # Estos deberían ser reemplazados por los campos reales de ScalpingParameters, DayTradingParameters, etc.
            if strategy_type == BaseStrategyType.SCALPING:
                self.scalping_sl_edit = QLineEdit()
                self.scalping_sl_edit.setPlaceholderText("Ej: 0.5 (porcentaje)")
                self.scalping_sl_edit.setToolTip("Stop Loss para Scalping en porcentaje (ej. 0.5 para 0.5%).")
                group_layout.addRow("Stop Loss (%):", self.scalping_sl_edit)
                
                self.scalping_tp_edit = QLineEdit()
                self.scalping_tp_edit.setPlaceholderText("Ej: 1.0 (porcentaje)")
                self.scalping_tp_edit.setToolTip("Take Profit para Scalping en porcentaje (ej. 1.0 para 1%).")
                group_layout.addRow("Take Profit (%):", self.scalping_tp_edit)
                
                self.scalping_leverage_edit = QLineEdit()
                self.scalping_leverage_edit.setPlaceholderText("Ej: 10 (para 10x)")
                self.scalping_leverage_edit.setToolTip("Apalancamiento a usar (si aplica).")
                group_layout.addRow("Apalancamiento:", self.scalping_leverage_edit)

            elif strategy_type == BaseStrategyType.DAY_TRADING:
                self.dt_timeframe_combo = QComboBox()
                self.dt_timeframe_combo.addItems(["1m", "5m", "15m", "30m", "1h", "4h"])
                self.dt_timeframe_combo.setToolTip("Timeframe principal para la estrategia de Day Trading.")
                group_layout.addRow("Timeframe:", self.dt_timeframe_combo)

                self.dt_indicator_edit = QLineEdit()
                self.dt_indicator_edit.setPlaceholderText("Ej: RSI(14)")
                self.dt_indicator_edit.setToolTip("Indicador principal y sus parámetros.")
                group_layout.addRow("Indicador Principal:", self.dt_indicator_edit)

            elif strategy_type == BaseStrategyType.ARBITRAGE_SIMPLE:
                self.arb_min_spread_edit = QLineEdit()
                self.arb_min_spread_edit.setPlaceholderText("Ej: 0.2 (porcentaje)")
                self.arb_min_spread_edit.setToolTip("Spread mínimo requerido para considerar una oportunidad de arbitraje (%).")
                group_layout.addRow("Spread Mínimo (%):", self.arb_min_spread_edit)

                self.arb_exchanges_edit = QLineEdit()
                self.arb_exchanges_edit.setPlaceholderText("Ej: binance,kraken (separados por coma)")
                self.arb_exchanges_edit.setToolTip("Exchanges a considerar para el arbitraje.")
                group_layout.addRow("Exchanges:", self.arb_exchanges_edit)
            
            params_layout.addWidget(group_box)
            params_widget.setLayout(params_layout)
            self.parameters_stack.addWidget(params_widget)

    def _on_base_strategy_type_changed(self, index):
        """
        Cambia el widget de parámetros visible en el QStackedWidget.
        """
        # El índice del ComboBox debería corresponder al índice del QStackedWidget
        # si se añadieron en el mismo orden.
        self.parameters_stack.setCurrentIndex(index)

    def _load_data_for_edit(self):
        """
        Carga los datos de self.strategy_config en los campos del formulario.
        """
        if not self.strategy_config:
            return

        self.config_name_edit.setText(getattr(self.strategy_config, 'configName', ''))
        
        base_type_value = getattr(self.strategy_config, 'baseStrategyType', None)
        if base_type_value:
            if isinstance(base_type_value, BaseStrategyType):
                idx = self.base_strategy_type_combo.findData(base_type_value)
                if idx >= 0:
                    self.base_strategy_type_combo.setCurrentIndex(idx)
            elif isinstance(base_type_value, str): # Si es un string, intentar encontrar por valor
                for i in range(self.base_strategy_type_combo.count()):
                    if self.base_strategy_type_combo.itemText(i) == base_type_value:
                        self.base_strategy_type_combo.setCurrentIndex(i)
                        break
        
        self.description_edit.setText(getattr(self.strategy_config, 'description', ''))
        
        # Cargar parámetros específicos (requiere lógica más compleja)
        # Esto dependerá de cómo se almacenen y recuperen los parámetros.
        # Por ahora, se asume que los widgets en _init_parameter_widgets()
        # se llenarán manualmente o mediante un método dedicado.
        # Ejemplo:
        current_params = getattr(self.strategy_config, 'parameters', {})
        current_base_type = getattr(self.strategy_config, 'baseStrategyType', None)

        if current_base_type == BaseStrategyType.SCALPING:
            if hasattr(self, 'scalping_sl_edit'): self.scalping_sl_edit.setText(str(current_params.get('stop_loss_percent', '')))
            if hasattr(self, 'scalping_tp_edit'): self.scalping_tp_edit.setText(str(current_params.get('take_profit_percent', '')))
            if hasattr(self, 'scalping_leverage_edit'): self.scalping_leverage_edit.setText(str(current_params.get('leverage', '')))
        elif current_base_type == BaseStrategyType.DAY_TRADING:
            if hasattr(self, 'dt_timeframe_combo'): 
                idx = self.dt_timeframe_combo.findText(str(current_params.get('timeframe', '')))
                if idx >=0: self.dt_timeframe_combo.setCurrentIndex(idx)
            if hasattr(self, 'dt_indicator_edit'): self.dt_indicator_edit.setText(str(current_params.get('indicator', '')))
        elif current_base_type == BaseStrategyType.ARBITRAGE_SIMPLE:
            if hasattr(self, 'arb_min_spread_edit'): self.arb_min_spread_edit.setText(str(current_params.get('min_spread_percent', '')))
            if hasattr(self, 'arb_exchanges_edit'): self.arb_exchanges_edit.setText(",".join(current_params.get('exchanges', [])))


        applicability = getattr(self.strategy_config, 'applicabilityRules', {})
        self.applicability_pairs_edit.setText(",".join(applicability.get('explicitPairs', [])))
        if hasattr(self, 'include_all_spot_checkbox'): self.include_all_spot_checkbox.setChecked(applicability.get('includeAllSpot', False))
        if hasattr(self, 'dynamic_filter_watchlist_edit'): self.dynamic_filter_watchlist_edit.setText(",".join(applicability.get('includedWatchlistIds', [])))


        # Cargar aiAnalysisProfileId
        # ai_profile_id = getattr(self.strategy_config, 'aiAnalysisProfileId', None)
        # if ai_profile_id:
        #     idx = self.ai_profile_combo.findData(ai_profile_id) # Suponiendo que el ID se guardó como data
        #     if idx >=0:
        #         self.ai_profile_combo.setCurrentIndex(idx)

        # Cargar riskParametersOverride
        risk_override_data = getattr(self.strategy_config, 'riskParametersOverride', None)
        risk_override_group_widget = self.findChild(QGroupBox, "Sobrescritura de Parámetros de Riesgo (Opcional)")

        if risk_override_data and risk_override_group_widget:
            risk_override_group_widget.setChecked(True)
            if hasattr(self, 'risk_daily_capital_edit'): self.risk_daily_capital_edit.setText(str(risk_override_data.get('dailyCapitalRiskPercentage', '')))
            if hasattr(self, 'risk_per_trade_edit'): self.risk_per_trade_edit.setText(str(risk_override_data.get('perTradeCapitalRiskPercentage', '')))
        elif risk_override_group_widget:
            risk_override_group_widget.setChecked(False)


    def get_data(self) -> dict:
        """
        Recoge los datos del formulario y los devuelve como un diccionario.
        Este diccionario debe ser compatible con lo que espera el backend.
        """
        # TODO: Implementar la recolección de datos de los parámetros dinámicos
        # y de las reglas de aplicabilidad y riesgo más complejas.
        
        # Placeholder para parámetros dinámicos
        parameters_data = {}
        current_type_enum = self.base_strategy_type_combo.currentData()

        if current_type_enum == BaseStrategyType.SCALPING:
            leverage_text = self.scalping_leverage_edit.text().strip()
            cleaned_leverage_text = re.sub(r'\D', '', leverage_text) # Eliminar no dígitos
            leverage_value = None
            if cleaned_leverage_text:
                try:
                    leverage_value = int(cleaned_leverage_text)
                except ValueError:
                    logger.warning(f"Valor de apalancamiento inválido '{leverage_text}', se usará None.")
                    # Podríamos mostrar un error en la UI aquí si quisiéramos
            
            parameters_data = {
                "stop_loss_percent": float(self.scalping_sl_edit.text() or 0) if self.scalping_sl_edit.text() else None,
                "take_profit_percent": float(self.scalping_tp_edit.text() or 0) if self.scalping_tp_edit.text() else None,
                "leverage": leverage_value
            }
            parameters_data = {k: v for k, v in parameters_data.items() if v is not None} # Limpiar Nones
        elif current_type_enum == BaseStrategyType.DAY_TRADING:
            parameters_data = {
                "timeframe": self.dt_timeframe_combo.currentText(),
                "indicator": self.dt_indicator_edit.text() or None
            }
            parameters_data = {k: v for k, v in parameters_data.items() if v is not None}
        elif current_type_enum == BaseStrategyType.ARBITRAGE_SIMPLE:
            parameters_data = {
                "min_spread_percent": float(self.arb_min_spread_edit.text() or 0) if self.arb_min_spread_edit.text() else None,
                "exchanges": [ex.strip() for ex in self.arb_exchanges_edit.text().split(',') if ex.strip()] or None
            }
            parameters_data = {k: v for k, v in parameters_data.items() if v is not None}
        
        applicability_rules = {
            "explicitPairs": [pair.strip() for pair in self.applicability_pairs_edit.text().split(',') if pair.strip()],
            "includeAllSpot": self.include_all_spot_checkbox.isChecked(),
            "includedWatchlistIds": [wid.strip() for wid in self.dynamic_filter_watchlist_edit.text().split(',') if wid.strip()]
        }
        # Limpiar listas vacías para que no se envíen si no hay contenido
        if not applicability_rules["explicitPairs"]: del applicability_rules["explicitPairs"]
        if not applicability_rules["includedWatchlistIds"]: del applicability_rules["includedWatchlistIds"]


        risk_override_data = None
        risk_override_group_widget = self.findChild(QGroupBox, "Sobrescritura de Parámetros de Riesgo (Opcional)")
        if risk_override_group_widget and risk_override_group_widget.isChecked():
            risk_override_data = {
                "dailyCapitalRiskPercentage": float(self.risk_daily_capital_edit.text() or 0) if self.risk_daily_capital_edit.text() else None,
                "perTradeCapitalRiskPercentage": float(self.risk_per_trade_edit.text() or 0) if self.risk_per_trade_edit.text() else None
            }
            risk_override_data = {k: v for k, v in risk_override_data.items() if v is not None}
            if not risk_override_data: risk_override_data = None # Si queda vacío, es None


        data = {
            "configName": self.config_name_edit.text(),
            "baseStrategyType": current_type_enum.name, 
            "description": self.description_edit.toPlainText() or None,
            "parameters": parameters_data,
            "applicabilityRules": applicability_rules,
            "aiAnalysisProfileId": self.ai_profile_combo.currentData(), # Envía el ID (UUID o str) o None
            "riskParametersOverride": risk_override_data,
        }
        
        if self.is_edit_mode and self.strategy_config and hasattr(self.strategy_config, 'id') and self.strategy_config.id:
            data['id'] = str(self.strategy_config.id) # Asegurar que el ID es string para JSON
        # Si es is_duplicating, no se debe enviar el 'id' original.
        # El id ya se puso a None en la vista al crear config_for_dialog, o no se incluye si no está en data.
            
        # Eliminar claves con valor None para que no se envíen al backend si no son necesarios
        # (depende de cómo el backend maneje los campos opcionales)
        # data = {k: v for k, v in data.items() if v is not None} 
        # Esta línea anterior es muy agresiva, mejor ser selectivo:
        if data["description"] is None: del data["description"]
        if data["aiAnalysisProfileId"] is None: del data["aiAnalysisProfileId"]
        if data["riskParametersOverride"] is None: del data["riskParametersOverride"]
        if not data["parameters"]: data["parameters"] = {} # Enviar objeto vacío si no hay params
        if not data["applicabilityRules"]: data["applicabilityRules"] = {}


        return data

    async def _save_config_async(self):
        """
        Lógica asíncrona para guardar la configuración.
        """
        self._clear_form_errors()
        config_data = self.get_data()
        
        try:
            if self.is_edit_mode: # Solo modo edición real actualiza
                if not self.strategy_config or not hasattr(self.strategy_config, 'id') or not self.strategy_config.id:
                    logger.error("Error: Intentando actualizar estrategia sin ID válido.")
                    QMessageBox.critical(self, "Error", "No se puede actualizar la estrategia: ID faltante.")
                    return
                
                strategy_id = str(self.strategy_config.id)
                logger.info(f"Actualizando estrategia ID {strategy_id}: {config_data}")
                await self.api_client.update_strategy(strategy_id, config_data)
                QMessageBox.information(self, "Éxito", f"Estrategia '{config_data.get('configName')}' actualizada correctamente.")
                self.accept()

            else: # Creación (esto incluye el caso de is_duplicating)
                action_text = "duplicada" if self.is_duplicating else "creada"
                logger.info(f"Creando (como {action_text}) nueva estrategia: {config_data}")
                # Asegurarse de que el ID no se envíe si es una duplicación o creación nueva
                if 'id' in config_data and (self.is_duplicating or not self.is_edit_mode):
                    del config_data['id']
                    
                created_strategy = await self.api_client.create_strategy(config_data)
                QMessageBox.information(self, "Éxito", f"Estrategia '{created_strategy.get('configName')}' {action_text} correctamente.")
                self.accept()
        
        except APIError as e:
            logger.error(f"Error de API al guardar configuración de estrategia: {e}")
            handled_specific_error = False
            if e.status_code == 422 and e.response_json:
                try:
                    error_details = e.response_json.get('detail', [])
                    if isinstance(error_details, list):
                        for error_item in error_details:
                            loc = error_item.get('loc', [])
                            msg = error_item.get('msg', 'Error de validación.')
                            
                            # FastAPI anida el nombre del campo bajo 'body' o 'query', etc.
                            # Por ejemplo: ['body', 'configName']
                            if loc and isinstance(loc, list) and len(loc) > 0:
                                # Intentar obtener el nombre del campo de manera más robusta
                                # Podría ser loc[1] si es ['body', 'fieldName'] o loc[0] si es solo ['fieldName']
                                field_name = loc[-1] if loc else "" 

                                if field_name == 'configName':
                                    self.config_name_error_label.setText(msg)
                                    self.config_name_error_label.setVisible(True)
                                    handled_specific_error = True
                                # TODO: Añadir manejo para otros campos aquí
                                # elif field_name == 'description':
                                #     self.description_error_label.setText(msg) # Suponiendo que existe
                                #     self.description_error_label.setVisible(True)
                                #     handled_specific_error = True
                                # ... y así para otros campos ...
                        
                        if not handled_specific_error and error_details:
                             # Si hubo errores 422 pero no se mapearon a campos específicos conocidos
                             # mostrar un mensaje más general con los detalles.
                             error_summary = "; ".join([f"{err.get('loc')}: {err.get('msg')}" for err in error_details if err.get('msg')])
                             QMessageBox.critical(self, "Error de Validación", f"Errores de validación: {error_summary if error_summary else str(e.response_json)}")
                             handled_specific_error = True # Se mostró un mensaje, aunque sea general de validación
                        elif not error_details: # error_details está vacío o no es una lista
                             QMessageBox.critical(self, "Error de Validación", f"Error de validación con formato inesperado (detalle vacío o no es lista): {str(e.response_json)}")
                             handled_specific_error = True


                    else: # Si 'detail' no es una lista (inesperado para FastAPI 422)
                        QMessageBox.critical(self, "Error de Validación", f"Error de validación con formato de detalle inesperado: {str(e.response_json)}")
                        handled_specific_error = True
                except Exception as parse_exc: # Error al procesar e.response_json o sus detalles
                    logger.error(f"Error al procesar detalle de error 422: {parse_exc}")
                    QMessageBox.critical(self, "Error de API", f"No se pudo procesar el error de validación (422): {str(e)}")
                    handled_specific_error = True # Se mostró un mensaje
            
            if not handled_specific_error:
                # Si no fue un error 422 o no se pudo manejar específicamente, mostrar mensaje genérico de APIError
                QMessageBox.critical(self, "Error de API", f"No se pudo guardar la estrategia: {e.message}")

        except Exception as e:
            logger.error(f"Error inesperado al guardar configuración de estrategia: {e}", exc_info=True)
            QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error: {e}")


    def _save_config(self):
        """
        Slot para el botón Guardar. Programa la tarea asíncrona de guardado.
        """
        self._clear_form_errors() # Limpiar errores previos

        # Validación básica en el frontend antes de enviar
        if not self.config_name_edit.text().strip():
            self.config_name_error_label.setText("El nombre de la configuración es obligatorio.")
            self.config_name_error_label.setVisible(True)
            # QMessageBox.warning(self, "Campo Requerido", "El nombre de la configuración es obligatorio.")
            return

        import asyncio
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._save_config_async())
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            loop.create_task(self._save_config_async())
        except Exception as e:
            QMessageBox.critical(self, "Error de Programación", f"No se pudo iniciar el guardado: {e}")


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication # Importar QApplication
    from datetime import datetime # Importar datetime
    from ..services.api_client import UltiBotAPIClient # Importar la clase real

    # Mock simple para UltiBotAPIClient
    class MockApiClient(UltiBotAPIClient): # Heredar de la clase real
        def __init__(self):
            # No llamar a super().__init__ si no se necesita la inicialización real
            pass 
        async def create_strategy(self, config_data):
            print(f"Mock API: create_strategy called with {config_data}")
            return {"configName": config_data.get("configName", "Mock Strategy")}
        async def update_strategy(self, strategy_id, config_data):
            print(f"Mock API: update_strategy called for {strategy_id} with {config_data}")
            return {"configName": config_data.get("configName", "Mock Strategy")}
        # Añadir otros métodos mock si son necesarios para las pruebas
        # Asegurarse de que todos los métodos abstractos o requeridos por UltiBotAPIClient estén implementados
        # o que el mock sea lo suficientemente completo para el contexto de la prueba.
        # Para este caso, solo se usan create_strategy y update_strategy.
        # Si UltiBotAPIClient tiene un __init__ que requiere argumentos, el mock también debería aceptarlos.
        # Si UltiBotAPIClient tiene métodos abstractos, MockApiClient debe implementarlos.
        # Por simplicidad, asumiré que los métodos usados son suficientes para el mock.

    app = QApplication(sys.argv)
    
    mock_api_client = MockApiClient() # Instancia del mock

    # Para probar el modo creación
    # dialog_create = StrategyConfigDialog(api_client=mock_api_client) # Pasar el mock
    # if dialog_create.exec_():
    #     print("Creación aceptada:", dialog_create.get_data())
    # else:
    #     print("Creación cancelada")

    # Para probar el modo edición
    mock_config_to_edit = TradingStrategyConfig(
        id="test-id-123",
        configName="Mi Estrategia de Scalping",
        baseStrategyType=BaseStrategyType.SCALPING,
        isActivePaperMode=True,
        isActiveRealMode=False,
        applicabilityRules={"explicitPairs": ["BTC/USDT", "ETH/USDT"]},
        lastModified=datetime.now(),
        # description="Una descripción de prueba.",
        # parameters={"stop_loss_percent": 0.015, "take_profit_percent": 0.03} 
        # aiAnalysisProfileId="profile-uuid-here",
        # riskParametersOverride={"max_drawdown": 0.1}
    )
    # mock_ai_profiles = [ # Ejemplo de UserConfiguration.aiStrategyConfigurations
    #     type('MockProfile', (), {'id': 'profile-uuid-here', 'name': 'Perfil IA Agresivo'})(),
    #     type('MockProfile', (), {'id': 'profile-uuid-other', 'name': 'Perfil IA Conservador'})()
    # ]

    dialog_edit = StrategyConfigDialog(api_client=mock_api_client, strategy_config=mock_config_to_edit) # Pasar el mock
    if dialog_edit.exec_():
        print("Edición aceptada:", dialog_edit.get_data())
    else:
        print("Edición cancelada")
    
    sys.exit(app.exec_())
