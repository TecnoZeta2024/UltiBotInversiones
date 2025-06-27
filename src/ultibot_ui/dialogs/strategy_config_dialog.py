# src/ultibot_ui/dialogs/strategy_config_dialog.py
"""
Módulo para el diálogo de configuración de estrategias de trading.
"""
import logging
from typing import Optional, List, Dict, Any # Importar Optional, List, Dict, Any
import re
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QTextEdit, QComboBox, QPushButton, QFormLayout, 
                               QDialogButtonBox, QMessageBox, QStackedWidget, QWidget, QGroupBox, QCheckBox)
from PySide6.QtCore import Qt

# Definir clases placeholder hasta que se muevan a un lugar compartido o se definan correctamente
class BaseStrategyType:
    SCALPING = "Scalping"
    DAY_TRADING = "Day Trading"
    ARBITRAGE_SIMPLE = "Arbitrage Simple"
    
    @classmethod
    def values(cls):
        return [cls.SCALPING, cls.DAY_TRADING, cls.ARBITRAGE_SIMPLE]

class TradingStrategyConfig:
    def __init__(self, id=None, configName="", baseStrategyType=None, isActivePaperMode=False, 
                 isActiveRealMode=False, applicabilityRules=None, lastModified=None, 
                 description="", parameters=None, aiAnalysisProfileId=None, riskParametersOverride=None):
        self.id = id
        self.configName = configName
        self.baseStrategyType = baseStrategyType
        self.isActivePaperMode = isActivePaperMode
        self.isActiveRealMode = isActiveRealMode
        self.applicabilityRules = applicabilityRules or {}
        self.lastModified = lastModified
        self.description = description
        self.parameters = parameters or {}
        self.aiAnalysisProfileId = aiAnalysisProfileId
        self.riskParametersOverride = riskParametersOverride
from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
# from ....shared.data_types import UserConfiguration # Para aiStrategyConfigurations

logger = logging.getLogger(__name__)

class StrategyConfigDialog(QDialog):
    """
    Diálogo modal para crear y editar configuraciones de TradingStrategyConfig.
    """
    def __init__(self, api_client: UltiBotAPIClient, 
                 user_id: UUID, # Añadido user_id
                 strategy_data: Optional[Dict[str, Any]] = None, # Cambiado a dict
                 ai_profiles: Optional[List[dict]] = None,
                 is_duplicating: bool = False,
                 parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.user_id = user_id # Guardar user_id
        self.strategy_data = strategy_data # Ahora es un dict
        self.ai_profiles = ai_profiles # Se inicializará en _init_ui_async
        self.is_duplicating = is_duplicating
        
        self.is_edit_mode = (self.strategy_data is not None) and not self.is_duplicating

        if self.is_edit_mode:
            self.setWindowTitle("Editar Configuración de Estrategia")
        elif self.is_duplicating:
            self.setWindowTitle("Duplicar Configuración de Estrategia (Crear Nueva)")
        else:
            self.setWindowTitle("Crear Nueva Configuración de Estrategia")
        self.setMinimumWidth(600)

        # Iniciar la inicialización asíncrona
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._init_ui_async())
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            loop.create_task(self._init_ui_async())

    async def _init_ui_async(self):
        # Fetch AI profiles if not provided
        if self.ai_profiles is None:
            try:
                user_config = await self.api_client.get_user_configuration()
                self.ai_profiles = user_config.get('ai_strategy_configurations', [])
                logger.info(f"Fetched {len(self.ai_profiles)} AI profiles.")
            except Exception as e:
                logger.error(f"Failed to fetch AI profiles: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"No se pudieron cargar los perfiles de IA: {e}")
                self.reject()
                return

        self._init_ui() # Call the synchronous UI initialization
        
        if self.is_edit_mode or self.is_duplicating:
            self._load_data_for_edit()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.config_name_edit = QLineEdit()
        self.config_name_error_label = QLabel()
        self.config_name_error_label.setStyleSheet("color: red;")
        self.config_name_error_label.setVisible(False)
        form_layout.addRow("Nombre de Configuración:", self.config_name_edit)
        form_layout.addRow("", self.config_name_error_label)

        self.base_strategy_type_combo = QComboBox()
        for strategy_type in BaseStrategyType.__members__.values():
            self.base_strategy_type_combo.addItem(strategy_type, strategy_type)
        self.base_strategy_type_combo.currentIndexChanged.connect(self._on_base_strategy_type_changed)
        form_layout.addRow("Tipo de Estrategia Base:", self.base_strategy_type_combo)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Descripción opcional de la estrategia...")
        self.description_edit.setFixedHeight(80)
        form_layout.addRow("Descripción:", self.description_edit)

        self.parameters_stack = QStackedWidget()
        self._init_parameter_widgets()
        form_layout.addRow("Parámetros Específicos:", self.parameters_stack)
        self._on_base_strategy_type_changed(0)

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

        self.ai_profile_combo = QComboBox()
        self.ai_profile_combo.addItem("Ninguno (Usar Default del Sistema)", None)
        for profile in self.ai_profiles:
            name = profile.get('name') if isinstance(profile, dict) else getattr(profile, 'name', None)
            pid = profile.get('id') if isinstance(profile, dict) else getattr(profile, 'id', None)
            if name and pid:
                self.ai_profile_combo.addItem(name, pid)
        self.ai_profile_combo.setToolTip("Seleccionar un perfil de configuración de IA específico para esta estrategia.")
        form_layout.addRow("Perfil de Análisis IA:", self.ai_profile_combo)
        
        risk_override_group = QGroupBox("Sobrescritura de Parámetros de Riesgo (Opcional)")
        risk_override_layout = QFormLayout(risk_override_group)
        risk_override_group.setCheckable(True)
        risk_override_group.setChecked(False)

        self.risk_daily_capital_edit = QLineEdit()
        self.risk_daily_capital_edit.setPlaceholderText("Ej: 1.5 (% del capital total)")
        self.risk_daily_capital_edit.setToolTip("Porcentaje máximo del capital total a arriesgar en un día.")
        risk_override_layout.addRow("Riesgo Capital Diario (%):", self.risk_daily_capital_edit)

        self.risk_per_trade_edit = QLineEdit()
        self.risk_per_trade_edit.setPlaceholderText("Ej: 0.5 (% del capital de la operación)")
        self.risk_per_trade_edit.setToolTip("Porcentaje máximo del capital asignado a una operación a arriesgar.")
        risk_override_layout.addRow("Riesgo por Operación (%):", self.risk_per_trade_edit)
        
        form_layout.addRow(risk_override_group)

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self._save_config)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def _clear_form_errors(self):
        self.config_name_error_label.setText("")
        self.config_name_error_label.setVisible(False)

    def _init_parameter_widgets(self):
        for strategy_type in BaseStrategyType.values():
            params_widget = QWidget()
            params_layout = QVBoxLayout(params_widget)
            
            group_box = QGroupBox(f"Parámetros para {strategy_type}")
            group_layout = QFormLayout(group_box)
            
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
        self.parameters_stack.setCurrentIndex(index)

    def _load_data_for_edit(self):
        if not self.strategy_data:
            return

        self.config_name_edit.setText(self.strategy_data.get('configName', ''))
        
        base_type_value = self.strategy_data.get('baseStrategyType', None)
        if base_type_value:
            idx = self.base_strategy_type_combo.findData(base_type_value)
            if idx >= 0:
                self.base_strategy_type_combo.setCurrentIndex(idx)
            else: # Si no se encuentra por data, intentar por texto
                for i in range(self.base_strategy_type_combo.count()):
                    if self.base_strategy_type_combo.itemText(i) == base_type_value:
                        self.base_strategy_type_combo.setCurrentIndex(i)
                        break
        
        self.description_edit.setText(self.strategy_data.get('description', ''))
        
        current_params = self.strategy_data.get('parameters', {})
        current_base_type = self.strategy_data.get('baseStrategyType', None)

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

        applicability = self.strategy_data.get('applicabilityRules', {})
        self.applicability_pairs_edit.setText(",".join(applicability.get('explicitPairs', [])))
        if hasattr(self, 'include_all_spot_checkbox'): self.include_all_spot_checkbox.setChecked(applicability.get('includeAllSpot', False))
        if hasattr(self, 'dynamic_filter_watchlist_edit'): self.dynamic_filter_watchlist_edit.setText(",".join(applicability.get('includedWatchlistIds', [])))

        ai_profile_id = self.strategy_data.get('aiAnalysisProfileId', None)
        if ai_profile_id:
            idx = self.ai_profile_combo.findData(ai_profile_id)
            if idx >=0:
                self.ai_profile_combo.setCurrentIndex(idx)

        risk_override_data = self.strategy_data.get('riskParametersOverride', None)
        risk_override_group_widget = self.findChild(QGroupBox, "Sobrescritura de Parámetros de Riesgo (Opcional)")

        if risk_override_data and risk_override_group_widget:
            risk_override_group_widget.setChecked(True)
            if hasattr(self, 'risk_daily_capital_edit'): self.risk_daily_capital_edit.setText(str(risk_override_data.get('dailyCapitalRiskPercentage', '')))
            if hasattr(self, 'risk_per_trade_edit'): self.risk_per_trade_edit.setText(str(risk_override_data.get('perTradeCapitalRiskPercentage', '')))
        elif risk_override_group_widget:
            risk_override_group_widget.setChecked(False)

        if self.is_duplicating:
            # Limpiar el ID y modificar el nombre para indicar que es una copia
            self.strategy_data['id'] = None
            self.config_name_edit.setText(f"{self.config_name_edit.text()} (Copia)")


    def get_strategy_data(self) -> dict: # Renombrado de get_data
        parameters_data = {}
        current_type = self.base_strategy_type_combo.currentData()

        if current_type == BaseStrategyType.SCALPING:
            leverage_text = self.scalping_leverage_edit.text().strip()
            cleaned_leverage_text = re.sub(r'\D', '', leverage_text)
            leverage_value = None
            if cleaned_leverage_text:
                try:
                    leverage_value = int(cleaned_leverage_text)
                except ValueError:
                    logger.warning(f"Valor de apalancamiento inválido '{leverage_text}', se usará None.")
                    self.scalping_leverage_edit.setStyleSheet("border: 1px solid red;")
                    self.scalping_leverage_edit.setToolTip("Valor de apalancamiento inválido. Use solo números.")
            
            parameters_data = {
                "stop_loss_percent": float(self.scalping_sl_edit.text() or 0) if self.scalping_sl_edit.text() else None,
                "take_profit_percent": float(self.scalping_tp_edit.text() or 0) if self.scalping_tp_edit.text() else None,
                "leverage": leverage_value
            }
            parameters_data = {k: v for k, v in parameters_data.items() if v is not None}
        elif current_type == BaseStrategyType.DAY_TRADING:
            parameters_data = {
                "timeframe": self.dt_timeframe_combo.currentText(),
                "indicator": self.dt_indicator_edit.text() or None
            }
            parameters_data = {k: v for k, v in parameters_data.items() if v is not None}
        elif current_type == BaseStrategyType.ARBITRAGE_SIMPLE.value:
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
            if not risk_override_data: risk_override_data = None

        data = {
            "configName": self.config_name_edit.text(),
            "baseStrategyType": current_type, 
            "description": self.description_edit.toPlainText() or None,
            "parameters": parameters_data,
            "applicabilityRules": applicability_rules,
            "aiAnalysisProfileId": self.ai_profile_combo.currentData(),
            "riskParametersOverride": risk_override_data,
        }
        
        if self.is_edit_mode and self.strategy_data and self.strategy_data.get('id'):
            data['id'] = str(self.strategy_data['id'])
            
        if data["description"] is None: del data["description"]
        if data["aiAnalysisProfileId"] is None: del data["aiAnalysisProfileId"]
        if data["riskParametersOverride"] is None: del data["riskParametersOverride"]
        if not data["parameters"]: data["parameters"] = {}
        if not data["applicabilityRules"]: data["applicabilityRules"] = {}

        return data

    async def _save_config_async(self):
        self._clear_form_errors()
        config_data = self.get_strategy_data() # Usar el nuevo nombre del método
        
        try:
            if self.is_edit_mode:
                if not self.strategy_data or not self.strategy_data.get('id'):
                    logger.error("Error: Intentando actualizar estrategia sin ID válido.")
                    QMessageBox.critical(self, "Error", "No se puede actualizar la estrategia: ID faltante.")
                    return
                
                strategy_id = str(self.strategy_data['id'])
                logger.info(f"Actualizando estrategia ID {strategy_id}: {config_data}")
                result = await self.api_client.update_strategy_config(strategy_id, config_data) # Llamada real a la API
                QMessageBox.information(self, "Éxito", f"Estrategia '{result.get('configName')}' actualizada correctamente.")
                self.accept()

            else:
                action_text = "duplicada" if self.is_duplicating else "creada"
                logger.info(f"Creando (como {action_text}) nueva estrategia: {config_data}")
                
                # Asegurarse de que el ID no se envíe si es una duplicación o creación nueva
                if 'id' in config_data:
                    del config_data['id']
                    
                result = await self.api_client.create_strategy_config(config_data) # Llamada real a la API
                QMessageBox.information(self, "Éxito", f"Estrategia '{result.get('configName')}' {action_text} correctamente.")
                self.accept()
        
        except APIError as e:
            logger.error(f"Error de API al guardar configuración de estrategia: {e}")
            handled_specific_error = False
            if e.status_code == 422:
                try:
                    error_details = getattr(e, 'response_json', {}).get('detail', [])
                    if isinstance(error_details, list):
                        for error_item in error_details:
                            loc = error_item.get('loc', [])
                            msg = error_item.get('msg', 'Error de validación.')
                            
                            if loc and isinstance(loc, list) and len(loc) > 0:
                                field_name = loc[-1] if loc else "" 

                                if field_name == 'configName':
                                    self.config_name_error_label.setText(msg)
                                    self.config_name_error_label.setVisible(True)
                                    handled_specific_error = True
                        
                        if not handled_specific_error and error_details:
                             error_summary = "; ".join([f"{err.get('loc')}: {err.get('msg')}" for err in error_details if err.get('msg')])
                             QMessageBox.critical(self, "Error de Validación", f"Errores de validación: {error_summary if error_summary else 'Detalles no disponibles'}")
                             handled_specific_error = True
                        elif not error_details:
                             QMessageBox.critical(self, "Error de Validación", f"Error de validación con formato inesperado (detalle vacío o no es lista).")
                             handled_specific_error = True

                    else:
                        QMessageBox.critical(self, "Error de Validación", f"Error de validación con formato de detalle inesperado.")
                        handled_specific_error = True
                except Exception as parse_exc:
                    logger.error(f"Error al procesar detalle de error 422: {parse_exc}")
                    QMessageBox.critical(self, "Error de API", f"No se pudo procesar el error de validación (422): {str(e)}")
                    handled_specific_error = True
            
            if not handled_specific_error:
                QMessageBox.critical(self, "Error de API", f"No se pudo guardar la estrategia: {e.message}")

        except Exception as e:
            logger.error(f"Error inesperado al guardar configuración de estrategia: {e}", exc_info=True)
            QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error: {e}")

    def _save_config(self):
        self._clear_form_errors()

        if not self.config_name_edit.text().strip():
            self.config_name_error_label.setText("El nombre de la configuración es obligatorio.")
            self.config_name_error_label.setVisible(True)
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
    from PySide6.QtWidgets import QApplication
    from datetime import datetime
    from ultibot_ui.services.api_client import UltiBotAPIClient

    class MockApiClient(UltiBotAPIClient):
        def __init__(self):
            pass 
        async def create_strategy_config(self, config_data): # Renombrado
            print(f"Mock API: create_strategy_config called with {config_data}")
            return {"configName": config_data.get("configName", "Mock Strategy"), "id": "mock-new-id"}
        async def update_strategy_config(self, strategy_id, config_data): # Renombrado
            print(f"Mock API: update_strategy_config called for {strategy_id} with {config_data}")
            return {"configName": config_data.get("configName", "Mock Strategy"), "id": strategy_id}
        async def get_user_configuration(self) -> Dict[str, Any]:
            return {
                "ai_strategy_configurations": [
                    {"id": "ai-profile-1", "name": "Perfil IA de Prueba 1"},
                    {"id": "ai-profile-2", "name": "Perfil IA de Prueba 2"},
                ]
            }

    app = QApplication(sys.argv)
    
    mock_api_client = MockApiClient()

    mock_config_to_edit = { # Ahora es un dict
        "id": "test-id-123",
        "configName": "Mi Estrategia de Scalping",
        "baseStrategyType": BaseStrategyType.SCALPING,
        "isActivePaperMode": True,
        "isActiveRealMode": False,
        "applicabilityRules": {"explicitPairs": ["BTC/USDT", "ETH/USDT"]},
        "lastModified": datetime.now().isoformat(), # Convertir a string
        "description": "Una descripción de prueba.",
        "parameters": {"stop_loss_percent": 0.015, "take_profit_percent": 0.03, "leverage": 10},
        "aiAnalysisProfileId": "profile-uuid-here",
        "riskParametersOverride": {"dailyCapitalRiskPercentage": 1.5, "perTradeCapitalRiskPercentage": 0.5}
    }

    # Para ejecutar el diálogo en un entorno de prueba, necesitamos un bucle de eventos.
    # Esto es solo para el bloque `if __name__ == '__main__':`
    async def run_dialog():
        dialog_edit = StrategyConfigDialog(api_client=mock_api_client, user_id=UUID('00000000-0000-0000-0000-000000000001'), strategy_data=mock_config_to_edit)
        if dialog_edit.exec_():
            print("Edición aceptada:", dialog_edit.get_strategy_data())
        else:
            print("Edición cancelada")
        app.quit() # Asegurarse de que la aplicación Qt se cierre

    asyncio.run(run_dialog())
    sys.exit(app.exec_())
