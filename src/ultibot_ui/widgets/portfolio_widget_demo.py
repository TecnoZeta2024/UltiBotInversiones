#!/usr/bin/env python3
"""
Demo del PortfolioWidget extendido con funcionalidades de TSL/TP y gestión de capital.

Este archivo demuestra las nuevas funcionalidades implementadas en la Subtask 3 de la Historia 4.4:
- Visualización de operaciones abiertas con TSL/TP activos
- Estado de gestión de capital con límites y alertas
- UI reorganizada en pestañas para mejor usabilidad

Para ejecutar el demo:
python src/ultibot_ui/widgets/portfolio_widget_demo.py
"""

import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# Importar el widget extendido
from portfolio_widget import PortfolioWidget, UltiBotAPIClient

# Importar tipos de datos
from src.shared.data_types import (
    PortfolioSnapshot, PortfolioSummary, PortfolioAsset, 
    AssetBalance, ServiceName, APICredential
)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockAPIClient(UltiBotAPIClient):
    """
    Cliente API simulado para demostrar las funcionalidades sin conexión real al backend.
    """
    
    def __init__(self):
        super().__init__()
        self.demo_trades = self._generate_demo_trades()
        self.demo_capital_status = self._generate_demo_capital_status()
        
    def _generate_demo_trades(self) -> List[Dict[str, Any]]:
        """
        Genera trades de demostración con TSL/TP activos.
        """
        return [
            {
                "id": str(uuid4()),
                "symbol": "BTCUSDT",
                "side": "BUY",
                "mode": "real",
                "positionStatus": "open",
                "entryOrder": {
                    "executedQuantity": 0.001,
                    "executedPrice": 58500.0,
                    "timestamp": datetime.utcnow() - timedelta(hours=2)
                },
                "takeProfitPrice": 61000.0,
                "currentStopPrice_tsl": 57200.0,
                "trailingStopActivationPrice": 59000.0,
                "trailingStopCallbackRate": 0.02,
                "currentPrice": 59800.0,
                "pnl_usd": 1.3,
                "pnl_percentage": 2.22
            },
            {
                "id": str(uuid4()),
                "symbol": "ETHUSDT", 
                "side": "BUY",
                "mode": "real",
                "positionStatus": "open",
                "entryOrder": {
                    "executedQuantity": 0.1,
                    "executedPrice": 3200.0,
                    "timestamp": datetime.utcnow() - timedelta(hours=1)
                },
                "takeProfitPrice": 3350.0,
                "currentStopPrice_tsl": 3150.0,
                "trailingStopActivationPrice": 3250.0,
                "trailingStopCallbackRate": 0.015,
                "currentPrice": 3280.0,
                "pnl_usd": 8.0,
                "pnl_percentage": 2.5
            },
            {
                "id": str(uuid4()),
                "symbol": "ADAUSDT",
                "side": "SELL",
                "mode": "paper",
                "positionStatus": "open",
                "entryOrder": {
                    "executedQuantity": 1000.0,
                    "executedPrice": 0.45,
                    "timestamp": datetime.utcnow() - timedelta(minutes=30)
                },
                "takeProfitPrice": 0.42,
                "currentStopPrice_tsl": 0.465,
                "trailingStopActivationPrice": 0.44,
                "trailingStopCallbackRate": 0.01,
                "currentPrice": 0.435,
                "pnl_usd": 15.0,
                "pnl_percentage": 3.33
            }
        ]
        
    def _generate_demo_capital_status(self) -> Dict[str, Any]:
        """
        Genera estado de gestión de capital de demostración.
        """
        total_capital = 10000.0
        daily_limit = total_capital * 0.5  # 50% límite diario
        committed_today = 3800.0  # 76% del límite usado
        
        return {
            "total_capital_usd": total_capital,
            "daily_capital_limit_usd": daily_limit,
            "daily_capital_committed_usd": committed_today,
            "available_for_new_trades_usd": daily_limit - committed_today,
            "daily_usage_percentage": (committed_today / daily_limit) * 100,
            "high_risk_positions_count": 1,
            "capital_alerts": [
                "Has usado el 76% del límite diario de capital.",
                "Hay 1 operación con riesgo alto. Revise las posiciones abiertas."
            ]
        }
    
    async def get_open_trades(self, mode: str = "all") -> List[Dict[str, Any]]:
        """
        Simula la obtención de trades abiertos.
        """
        await asyncio.sleep(0.5)  # Simular latencia de red
        
        if mode == "all":
            return self.demo_trades
        elif mode == "real":
            return [t for t in self.demo_trades if t["mode"] == "real"]
        elif mode == "paper":
            return [t for t in self.demo_trades if t["mode"] == "paper"]
        return []
    
    async def get_capital_management_status(self) -> Dict[str, Any]:
        """
        Simula la obtención del estado de gestión de capital.
        """
        await asyncio.sleep(0.3)  # Simular latencia de red
        return self.demo_capital_status
    
    async def get_portfolio_snapshot_with_capital_info(self) -> Dict[str, Any]:
        """
        Simula snapshot extendido del portafolio.
        """
        await asyncio.sleep(0.4)  # Simular latencia de red
        return {
            "portfolio_snapshot": self._generate_demo_portfolio_snapshot(),
            "capital_status": self.demo_capital_status
        }
    
    def _generate_demo_portfolio_snapshot(self) -> PortfolioSnapshot:
        """
        Genera un snapshot de demostración del portafolio.
        """
        # Assets de paper trading
        paper_assets = [
            PortfolioAsset(
                symbol="ADA",
                quantity=1000.0,
                entry_price=0.45,
                current_price=0.435,
                current_value_usd=435.0,
                unrealized_pnl_usd=-15.0,
                unrealized_pnl_percentage=-3.33
            ),
            PortfolioAsset(
                symbol="XRP",
                quantity=500.0,
                entry_price=0.8,
                current_price=0.85,
                current_value_usd=425.0,
                unrealized_pnl_usd=25.0,
                unrealized_pnl_percentage=6.25
            )
        ]
        
        # Assets de real trading
        real_assets = [
            PortfolioAsset(
                symbol="BTC",
                quantity=0.001,
                entry_price=58500.0,
                current_price=59800.0,
                current_value_usd=59.8,
                unrealized_pnl_usd=1.3,
                unrealized_pnl_percentage=2.22
            ),
            PortfolioAsset(
                symbol="ETH",
                quantity=0.1,
                entry_price=3200.0,
                current_price=3280.0,
                current_value_usd=328.0,
                unrealized_pnl_usd=8.0,
                unrealized_pnl_percentage=2.5
            )
        ]
        
        # Resumen de paper trading
        paper_summary = PortfolioSummary(
            available_balance_usdt=14140.0,  # Saldo restante después de compras
            total_assets_value_usd=860.0,    # Valor actual de activos
            total_portfolio_value_usd=15000.0 # Balance + valor de activos
        )
        paper_summary.assets = paper_assets
        
        # Resumen de real trading
        real_summary = PortfolioSummary(
            available_balance_usdt=6200.0,   # USDT disponible en Binance
            total_assets_value_usd=387.8,    # Valor actual de activos reales
            total_portfolio_value_usd=6587.8 # Balance + valor de activos
        )
        real_summary.assets = real_assets
        
        return PortfolioSnapshot(
            paper_trading=paper_summary,
            real_trading=real_summary,
            last_updated=datetime.utcnow()
        )

class MockPortfolioService:
    """
    Servicio de portafolio simulado para la demostración.
    """
    
    def __init__(self):
        self.api_client = MockAPIClient()
        
    async def get_portfolio_snapshot(self, user_id: UUID) -> PortfolioSnapshot:
        """
        Obtiene snapshot del portafolio para la demo.
        """
        await asyncio.sleep(0.6)  # Simular procesamiento
        return self.api_client._generate_demo_portfolio_snapshot()

class PortfolioDemo(QMainWindow):
    """
    Ventana principal de demostración del PortfolioWidget extendido.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo: PortfolioWidget Extendido - Historia 4.4")
        self.setGeometry(100, 100, 1200, 800)
        
        # Configurar widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Servicios simulados
        self.user_id = UUID("11111111-2222-3333-4444-555555555555")
        self.portfolio_service = MockPortfolioService()
        self.api_client = MockAPIClient()
        
        # Crear el PortfolioWidget extendido
        self.portfolio_widget = PortfolioWidget(
            user_id=self.user_id,
            portfolio_service=self.portfolio_service,
            api_client=self.api_client
        )
        
        layout.addWidget(self.portfolio_widget)
        
        # Aplicar tema oscuro
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: "Segoe UI", sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #555;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                border-color: #007bff;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
        """)
        
    def closeEvent(self, event):
        """
        Limpia recursos al cerrar la ventana.
        """
        self.portfolio_widget.stop_updates()
        event.accept()

async def run_demo():
    """
    Ejecuta la demostración de forma asíncrona.
    """
    app = QApplication(sys.argv)
    
    # Crear y mostrar la ventana de demo
    demo_window = PortfolioDemo()
    demo_window.show()
    
    # Iniciar las actualizaciones del widget
    demo_window.portfolio_widget.start_updates()
    
    # Información sobre el demo
    logger.info("=== DEMO: PortfolioWidget Extendido - Historia 4.4 ===")
    logger.info("Funcionalidades demostradas:")
    logger.info("1. Pestaña 'Portafolio': Resumen tradicional de paper/real trading")
    logger.info("2. Pestaña 'Operaciones Abiertas': TSL/TP activos, precios en tiempo real")
    logger.info("3. Pestaña 'Gestión de Capital': Límites, alertas, uso del capital diario")
    logger.info("4. Actualización asíncrona cada 15 segundos")
    logger.info("5. Sistema de alertas visuales para límites de capital")
    logger.info("=====================================")
    
    # Ejecutar la aplicación
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Ejecutar el demo
    asyncio.run(run_demo())
