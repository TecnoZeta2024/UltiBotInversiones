import logging
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject, QRunnable, QThreadPool
from PyQt5.QtGui import QFont, QColor

from src.shared.data_types import PortfolioSnapshot, PortfolioSummary, PortfolioAsset
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

class WorkerSignals(QObject):
    """
    Define las señales disponibles de un hilo de trabajo.
    """
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()

class PortfolioUpdateWorker(QRunnable):
    """
    Runnable para ejecutar la actualización del portafolio en un hilo separado.
    """
    def __init__(self, user_id: UUID, portfolio_service: PortfolioService):
        super().__init__()
        self.user_id = user_id
        self.portfolio_service = portfolio_service
        self.signals = WorkerSignals()

    def run(self):
        """
        Ejecuta la tarea de actualización del portafolio.
        """
        try:
            import asyncio
            # Crear un nuevo bucle de eventos para este hilo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            snapshot = loop.run_until_complete(self.portfolio_service.get_portfolio_snapshot(self.user_id))
            self.signals.result.emit(snapshot)
        except Exception as e:
            error_msg = f"Error en el hilo de actualización del portafolio: {e}"
            logger.error(error_msg, exc_info=True)
            self.signals.error.emit(error_msg)
        finally:
            self.signals.finished.emit()

class PortfolioWidget(QWidget):
    """
    Widget para la visualización del estado del portafolio (Paper Trading y Real).
    """
    portfolio_updated = pyqtSignal(PortfolioSnapshot)
    error_occurred = pyqtSignal(str)

    def __init__(self, user_id: UUID, portfolio_service: PortfolioService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.portfolio_service = portfolio_service
        self.current_snapshot: Optional[PortfolioSnapshot] = None
        self.thread_pool = QThreadPool() # Pool de hilos para tareas asíncronas

        self.init_ui()
        self.setup_update_timer()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setSpacing(15)
        self.setLayout(main_layout) # Establecer el layout principal

        title_label = QLabel("Estado del Portafolio")
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Grupo para Paper Trading
        self.paper_trading_group = self._create_portfolio_group("Paper Trading")
        self.paper_balance_label = QLabel("Saldo Disponible: N/A")
        self.paper_total_value_label = QLabel("Valor Total Activos: N/A")
        self.paper_portfolio_value_label = QLabel("Valor Total Portafolio: N/A")
        self.paper_assets_table = self._create_assets_table()
        
        paper_layout = self.paper_trading_group.layout()
        if isinstance(paper_layout, QFormLayout):
            paper_layout.addRow(self.paper_balance_label)
            paper_layout.addRow(self.paper_total_value_label)
            paper_layout.addRow(self.paper_portfolio_value_label)
            paper_layout.addRow(QLabel("Activos Poseídos:"))
            paper_layout.addRow(self.paper_assets_table)
        main_layout.addWidget(self.paper_trading_group)

        # Grupo para Real Trading
        self.real_trading_group = self._create_portfolio_group("Real Trading (Binance)")
        self.real_balance_label = QLabel("Saldo Disponible (USDT): N/A")
        self.real_total_value_label = QLabel("Valor Total Activos: N/A")
        self.real_portfolio_value_label = QLabel("Valor Total Portafolio: N/A")
        self.real_assets_table = self._create_assets_table()
        
        real_layout = self.real_trading_group.layout()
        if isinstance(real_layout, QFormLayout):
            real_layout.addRow(self.real_balance_label)
            real_layout.addRow(self.real_total_value_label)
            real_layout.addRow(self.real_portfolio_value_label)
            real_layout.addRow(QLabel("Activos Poseídos:"))
            real_layout.addRow(self.real_assets_table)
        main_layout.addWidget(self.real_trading_group)

        self.last_updated_label = QLabel("Última actualización: N/A")
        self.last_updated_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.last_updated_label)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.error_label)

    def _create_portfolio_group(self, title: str) -> QGroupBox:
        group_box = QGroupBox(title)
        group_box.setLayout(QFormLayout())
        group_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #333;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                background-color: #222;
                color: #EEE;
            }
            QLabel {
                color: #DDD;
            }
        """)
        return group_box

    def _create_assets_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Símbolo", "Cantidad", "Precio Entrada", "Precio Actual", "Valor USD", "PnL (%)"])
        
        # Asegurarse de que horizontalHeader() y verticalHeader() no sean None
        if table.horizontalHeader() is not None:
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # type: ignore
        if table.verticalHeader() is not None:
            table.verticalHeader().setVisible(False) # type: ignore
            
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2C2C2C;
                alternate-background-color: #3A3A3A;
                color: #EEE;
                border: 1px solid #444;
                gridline-color: #444;
            }
            QHeaderView::section {
                background-color: #444;
                color: #EEE;
                padding: 5px;
                border: 1px solid #555;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        return table

    def setup_update_timer(self):
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(15000) # Actualizar cada 15 segundos
        self.update_timer.timeout.connect(self._start_portfolio_update_worker) # Conectar a un método síncrono
        self.update_timer.start()
        logger.info("Timer de actualización del portafolio iniciado.")

    def _start_portfolio_update_worker(self):
        """
        Inicia un hilo de trabajo para obtener los datos del portafolio.
        """
        worker = PortfolioUpdateWorker(self.user_id, self.portfolio_service)
        worker.signals.result.connect(self.update_ui_with_snapshot)
        worker.signals.error.connect(self._handle_worker_error)
        worker.signals.finished.connect(self._worker_finished)
        self.thread_pool.start(worker)
        logger.info("Tarea de actualización del portafolio enviada al pool de hilos.")

    def _handle_worker_error(self, error_msg: str):
        """
        Maneja los errores reportados por el hilo de trabajo.
        """
        self.error_label.setText(f"Error: {error_msg}")
        self.error_occurred.emit(error_msg)
        logger.error(f"Error en el worker de actualización del portafolio: {error_msg}")

    def _worker_finished(self):
        """
        Señal de que el hilo de trabajo ha terminado.
        """
        logger.info("Worker de actualización del portafolio finalizado.")

    def update_ui_with_snapshot(self, snapshot: PortfolioSnapshot):
        """
        Actualiza la interfaz de usuario con los datos del snapshot del portafolio.
        """
        # Actualizar Paper Trading
        self.paper_balance_label.setText(f"Saldo Disponible: {snapshot.paper_trading.available_balance_usdt:,.2f} USDT")
        self.paper_total_value_label.setText(f"Valor Total Activos: {snapshot.paper_trading.total_assets_value_usd:,.2f} USDT")
        self.paper_portfolio_value_label.setText(f"Valor Total Portafolio: {snapshot.paper_trading.total_portfolio_value_usd:,.2f} USDT")
        self._populate_assets_table(self.paper_assets_table, snapshot.paper_trading.assets)
        if snapshot.paper_trading.error_message:
            self.paper_trading_group.setTitle(f"Paper Trading (Error: {snapshot.paper_trading.error_message})")
            self.paper_trading_group.setStyleSheet("QGroupBox { border: 1px solid red; }")
        else:
            self.paper_trading_group.setTitle("Paper Trading")
            self.paper_trading_group.setStyleSheet("") # Reset style

        # Actualizar Real Trading
        self.real_balance_label.setText(f"Saldo Disponible (USDT): {snapshot.real_trading.available_balance_usdt:,.2f} USDT")
        self.real_total_value_label.setText(f"Valor Total Activos: {snapshot.real_trading.total_assets_value_usd:,.2f} USDT")
        self.real_portfolio_value_label.setText(f"Valor Total Portafolio: {snapshot.real_trading.total_portfolio_value_usd:,.2f} USDT")
        self._populate_assets_table(self.real_assets_table, snapshot.real_trading.assets)
        if snapshot.real_trading.error_message:
            self.real_trading_group.setTitle(f"Real Trading (Binance) (Error: {snapshot.real_trading.error_message})")
            self.real_trading_group.setStyleSheet("QGroupBox { border: 1px solid red; }")
        else:
            self.real_trading_group.setTitle("Real Trading (Binance)")
            self.real_trading_group.setStyleSheet("") # Reset style

        self.last_updated_label.setText(f"Última actualización: {snapshot.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

    def _populate_assets_table(self, table: QTableWidget, assets: List[PortfolioAsset]):
        table.setRowCount(len(assets))
        for row, asset in enumerate(assets):
            table.setItem(row, 0, QTableWidgetItem(asset.symbol))
            table.setItem(row, 1, QTableWidgetItem(f"{asset.quantity:,.8f}"))
            table.setItem(row, 2, QTableWidgetItem(f"{asset.entry_price:,.2f}" if asset.entry_price is not None else "N/A"))
            table.setItem(row, 3, QTableWidgetItem(f"{asset.current_price:,.2f}" if asset.current_price is not None else "N/A"))
            table.setItem(row, 4, QTableWidgetItem(f"{asset.current_value_usd:,.2f}" if asset.current_value_usd is not None else "N/A"))
            
            pnl_item = QTableWidgetItem(f"{asset.unrealized_pnl_percentage:,.2f}%" if asset.unrealized_pnl_percentage is not None else "N/A")
            if asset.unrealized_pnl_percentage is not None:
                if asset.unrealized_pnl_percentage > 0:
                    pnl_item.setForeground(QColor("lightgreen"))
                elif asset.unrealized_pnl_percentage < 0:
                    pnl_item.setForeground(QColor("red"))
            table.setItem(row, 5, pnl_item)

    def start_updates(self):
        """Inicia la primera actualización y el timer."""
        self._start_portfolio_update_worker() # Realizar una actualización inicial
        self.update_timer.start()

    def stop_updates(self):
        """Detiene el timer de actualizaciones."""
        self.update_timer.stop()
        logger.info("Timer de actualización del portafolio detenido.")

# Ejemplo de uso (para pruebas locales)
if __name__ == "__main__":
    import sys
    import asyncio
    import logging
    from datetime import datetime
    from typing import Optional, List, Dict, Any
    from uuid import UUID

    from PyQt5.QtWidgets import QApplication, QMainWindow

    from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
    from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
    from src.ultibot_backend.services.credential_service import CredentialService
    from src.ultibot_backend.services.config_service import ConfigService
    from src.ultibot_backend.services.market_data_service import MarketDataService
    from src.ultibot_backend.services.portfolio_service import PortfolioService
    from src.shared.data_types import AssetBalance, ServiceName, APICredential # Importar tipos necesarios

    # Configurar un logger básico para el ejemplo
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Mockear servicios para pruebas locales sin una BD real o credenciales
    class MockPersistenceService(SupabasePersistenceService):
        async def get_user_configuration(self, user_id: UUID) -> Optional[Dict[str, Any]]:
            # Simular una configuración por defecto
            return {
                "id": str(UUID("00000000-0000-0000-0000-000000000001")),
                "user_id": str(user_id),
                "defaultPaperTradingCapital": 15000.0,
                "selectedTheme": "dark"
            }
        async def upsert_user_configuration(self, user_id: UUID, config_data: Dict[str, Any]):
            logger.info(f"Mock: Guardando configuración para {user_id}: {config_data}")
            pass # No hacer nada real

    class MockBinanceAdapter(BinanceAdapter):
        async def get_spot_balances(self, api_key: str, api_secret: str) -> List[AssetBalance]:
            # Simular balances de Binance
            return [
                AssetBalance(asset="USDT", free=1000.0, locked=0.0, total=1000.0),
                AssetBalance(asset="BTC", free=0.05, locked=0.0, total=0.05),
                AssetBalance(asset="ETH", free=0.1, locked=0.0, total=0.1),
            ]
        async def get_ticker_24hr(self, symbol: str) -> Dict[str, Any]:
            # Simular precios de ticker
            if symbol == "BTCUSDT":
                return {"lastPrice": "60000.0", "priceChangePercent": "1.5", "quoteVolume": "1000000000"}
            elif symbol == "ETHUSDT":
                return {"lastPrice": "3000.0", "priceChangePercent": "2.0", "quoteVolume": "500000000"}
            return {"lastPrice": "1.0", "priceChangePercent": "0.0", "quoteVolume": "0"} # Default para otros

    class MockCredentialService(CredentialService):
        def __init__(self):
            # No necesitamos un persistence_service real para este mock
            pass
        async def get_credential(self, user_id: UUID, service_name: ServiceName, credential_label: str) -> Optional[APICredential]:
            # Simular una credencial válida
            if service_name == ServiceName.BINANCE_SPOT:
                return APICredential(
                    id=UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef"),
                    user_id=user_id,
                    service_name=service_name,
                    credential_label=credential_label,
                    encrypted_api_key="mock_key",
                    encrypted_api_secret="mock_secret",
                    status="active",
                    last_verified_at=datetime.utcnow(),
                    permissions=["SPOT_TRADING"]
                )
            return None
        async def verify_credential(self, credential: APICredential) -> bool:
            return True # Siempre exitoso para el mock

    async def run_widget_test():
        app = QApplication(sys.argv)
        main_window = QMainWindow()
        main_window.setWindowTitle("Test de PortfolioWidget")
        main_window.setGeometry(100, 100, 800, 600)

        # Inicializar servicios mock
        mock_persistence_service = MockPersistenceService()
        mock_binance_adapter = MockBinanceAdapter()
        mock_credential_service = MockCredentialService()

        config_service = ConfigService(mock_persistence_service)
        market_data_service = MarketDataService(mock_credential_service, mock_binance_adapter)
        portfolio_service = PortfolioService(market_data_service, config_service)

        # ID de usuario de prueba
        test_user_id = UUID("00000000-0000-0000-0000-000000000001")

        # Inicializar el servicio de portafolio
        await portfolio_service.initialize_portfolio(test_user_id)

        # Añadir algunos activos de paper trading para probar
        await portfolio_service.add_paper_trading_asset(test_user_id, "ADA", 1000.0, 0.5)
        await portfolio_service.add_paper_trading_asset(test_user_id, "XRP", 500.0, 0.8)
        await portfolio_service.update_paper_trading_balance(test_user_id, -1000) # Simular una compra

        portfolio_widget = PortfolioWidget(test_user_id, portfolio_service)
        main_window.setCentralWidget(portfolio_widget)
        main_window.show()

        # Iniciar la primera actualización del widget
        portfolio_widget.start_updates() # Llamar al método síncrono que inicia el worker

        # Ejecutar la aplicación PyQt
        sys.exit(app.exec_())

    # Ejecutar el test asíncrono
    asyncio.run(run_widget_test())
