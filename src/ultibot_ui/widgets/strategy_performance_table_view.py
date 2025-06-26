"""
Widget para mostrar el desempeño de las estrategias en una tabla.
"""
import logging
from PySide6.QtWidgets import QTableView, QWidget, QVBoxLayout, QHeaderView
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor, QBrush
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class StrategyPerformanceTableModel(QAbstractTableModel):
    """
    Modelo de datos para la tabla de desempeño de estrategias.
    """
    def __init__(self, data: Optional[List[Dict[str, Any]]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = data if data is not None else []
        self._headers = ["Nombre Estrategia", "Modo", "# Operaciones", "P&L Total", "Win Rate (%)"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            item = self._data[row]
            if col == 0:
                return item.get("strategyName", "")
            elif col == 1:
                return item.get("mode", "")
            elif col == 2:
                return str(item.get("totalOperations", 0)) # Convertir a string para display
            elif col == 3:
                pnl = item.get("totalPnl", 0.0)
                return f"{pnl:.2f}" # Formatear P&L a 2 decimales
            elif col == 4:
                win_rate = item.get("winRate", 0.0)
                return f"{win_rate:.2f}" # Formatear Win Rate a 2 decimales
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [2, 3, 4]: # Alineación a la derecha para números
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        
        elif role == Qt.ItemDataRole.BackgroundRole:
            item = self._data[row]
            mode = item.get("mode", "").lower()
            if mode == "paper":
                return QBrush(QColor(230, 240, 255))  # Azul claro para paper
            elif mode == "real":
                return QBrush(QColor(230, 255, 230))  # Verde claro para real
            
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
        return None

    def update_data(self, new_data: List[Dict[str, Any]]):
        """
        Actualiza los datos del modelo y notifica a la vista.
        """
        logger.debug(f"Actualizando modelo de tabla de desempeño con: {new_data}")
        self.beginResetModel()
        self._data = new_data if new_data is not None else []
        self.endResetModel()

class StrategyPerformanceTableView(QWidget):
    """
    Widget que contiene una QTableView para mostrar el desempeño de las estrategias.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Desempeño por Estrategia")
        
        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)
        
        self._table_view = QTableView()
        self._model = StrategyPerformanceTableModel()
        self._table_view.setModel(self._model)
        
        # Ajustar cabeceras
        horizontal_header = self._table_view.horizontalHeader()
        if horizontal_header:
            horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        vertical_header = self._table_view.verticalHeader()
        if vertical_header:
            vertical_header.setVisible(False)
            
        self._table_view.setAlternatingRowColors(True)
        
        self._layout.addWidget(self._table_view)

    def set_data(self, data: List[Dict[str, Any]]):
        """
        Establece los datos para mostrar en la tabla.
        """
        self._model.update_data(data)

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    
    # Datos de ejemplo
    sample_data = [
        {
            "strategyName": "Scalping BTC Intenso",
            "strategyId": "uuid-scalping-btc",
            "mode": "paper",
            "totalOperations": 50,
            "totalPnl": 125.75,
            "winRate": 60.0 
        },
        {
            "strategyName": "Day Trading ETH Conservador",
            "strategyId": "uuid-daytrading-eth",
            "mode": "real",
            "totalOperations": 5,
            "totalPnl": -25.50,
            "winRate": 20.0
        },
        {
            "strategyName": "Swing Trading ADA",
            "strategyId": "uuid-swing-ada",
            "mode": "paper",
            "totalOperations": 15,
            "totalPnl": 78.90,
            "winRate": 75.555
        }
    ]
    
    main_window = StrategyPerformanceTableView()
    main_window.set_data(sample_data)
    main_window.resize(800, 300)
    main_window.show()
    
    sys.exit(app.exec_())
