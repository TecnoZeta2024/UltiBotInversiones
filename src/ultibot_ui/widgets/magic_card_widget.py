"""
Magic Card Widget - Tarjeta interactiva con efecto spotlight
Inspirado en Magic UI - Adapta efectos modernos para PyQt5
"""
import logging
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QLinearGradient, QRadialGradient

logger = logging.getLogger(__name__)

class MagicCardWidget(QFrame):
    """
    Tarjeta interactiva con efectos de spotlight que siguen el mouse.
    Optimizada para mostrar información crítica de trading con efectos visuales modernos.
    """
    
    card_clicked = pyqtSignal(str)  # Emite el tipo de tarjeta clickeada
    
    def __init__(self, 
                 title: str = "Magic Card",
                 subtitle: str = "",
                 card_type: str = "default",
                 enable_spotlight: bool = True,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.title = title
        self.subtitle = subtitle
        self.card_type = card_type  # 'portfolio', 'trading', 'performance', 'default'
        self.enable_spotlight = enable_spotlight
        
        # Estado del spotlight
        self.mouse_x = 0
        self.mouse_y = 0
        self.is_hovered = False
        
        # Inicializar atributo privado ANTES de usar la propiedad
        self._spotlight_opacity = 0.0
        
        # Configuración de animaciones
        self.hover_animation = QPropertyAnimation(self, b"spotlight_opacity")
        self.hover_animation.setDuration(300)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Timer para actualización del spotlight
        self.spotlight_timer = QTimer()
        self.spotlight_timer.timeout.connect(self.update)
        self.spotlight_timer.setInterval(16)  # ~60fps
        
        self._setup_ui()
        self._setup_styling()
        self._setup_animations()
        
    def _setup_ui(self):
        """Configura la estructura de la interfaz de usuario."""
        self.setFixedHeight(160)
        self.setMinimumWidth(280)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(12)
        
        # Header con título y subtítulo
        self.header_layout = QVBoxLayout()
        self.header_layout.setSpacing(4)
        
        # Título principal
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setWordWrap(True)
        
        # Subtítulo
        self.subtitle_label = QLabel(self.subtitle)
        self.subtitle_label.setObjectName("cardSubtitle") 
        self.subtitle_label.setWordWrap(True)
        
        self.header_layout.addWidget(self.title_label)
        if self.subtitle:
            self.header_layout.addWidget(self.subtitle_label)
            
        # Contenido principal (para ser sobrescrito por subclases)
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        
        # Contenedor de métricas/datos
        self.metrics_layout = QHBoxLayout()
        self.metrics_layout.setSpacing(16)
        
        # Agregar layouts al principal
        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addLayout(self.content_layout)
        self.main_layout.addLayout(self.metrics_layout)
        self.main_layout.addStretch()
        
    def _setup_styling(self):
        """Aplica el estilo específico basado en el tipo de tarjeta."""
        base_style = """
            MagicCardWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 41, 59, 0.95),
                    stop:0.5 rgba(51, 65, 85, 0.95),
                    stop:1 rgba(30, 41, 59, 0.95)
                );
                border-radius: 20px;
                border: 1px solid rgba(59, 130, 246, 0.2);
            }
            
            QLabel#cardTitle {
                font-size: 18px;
                font-weight: 700;
                color: #F8FAFC;
                background: transparent;
            }
            
            QLabel#cardSubtitle {
                font-size: 13px;
                font-weight: 500;
                color: #94A3B8;
                background: transparent;
            }
            
            QLabel#metricValue {
                font-size: 24px;
                font-weight: 700;
                background: transparent;
            }
            
            QLabel#metricLabel {
                font-size: 12px;
                font-weight: 500;
                color: #64748B;
                background: transparent;
            }
        """
        
        # Estilos específicos por tipo de tarjeta
        type_styles = {
            'portfolio': """
                MagicCardWidget {
                    border: 1px solid rgba(16, 185, 129, 0.3);
                }
                QLabel#metricValue { color: #10B981; }
            """,
            'trading': """
                MagicCardWidget {
                    border: 1px solid rgba(59, 130, 246, 0.3);
                }
                QLabel#metricValue { color: #3B82F6; }
            """,
            'performance': """
                MagicCardWidget {
                    border: 1px solid rgba(168, 85, 247, 0.3);
                }
                QLabel#metricValue { color: #A855F7; }
            """,
            'alert': """
                MagicCardWidget {
                    border: 1px solid rgba(239, 68, 68, 0.3);
                }
                QLabel#metricValue { color: #EF4444; }
            """
        }
        
        final_style = base_style + type_styles.get(self.card_type, "")
        self.setStyleSheet(final_style)
        
        # Configurar clase CSS para compatibilidad con QSS
        self.setProperty("class", "magic-card")
        
    def _setup_animations(self):
        """Configura las animaciones y efectos."""
        # Efecto de sombra base
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(20)
        self.shadow_effect.setXOffset(0)
        self.shadow_effect.setYOffset(8)
        self.shadow_effect.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(self.shadow_effect)
        
        # Habilitar tracking del mouse si el spotlight está habilitado
        if self.enable_spotlight:
            self.setMouseTracking(True)
            
    def add_metric(self, label: str, value: str, value_type: str = "default"):
        """
        Agrega una métrica a la tarjeta.
        
        Args:
            label: Etiqueta de la métrica
            value: Valor a mostrar
            value_type: Tipo de valor ('positive', 'negative', 'neutral', 'default')
        """
        metric_container = QVBoxLayout()
        metric_container.setSpacing(2)
        metric_container.setAlignment(Qt.AlignCenter)
        
        # Valor principal
        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        value_label.setAlignment(Qt.AlignCenter)
        
        # Aplicar color según el tipo
        if value_type == "positive":
            value_label.setStyleSheet("QLabel#metricValue { color: #10B981; }")
        elif value_type == "negative":
            value_label.setStyleSheet("QLabel#metricValue { color: #EF4444; }")
        elif value_type == "neutral":
            value_label.setStyleSheet("QLabel#metricValue { color: #64748B; }")
            
        # Etiqueta
        label_widget = QLabel(label)
        label_widget.setObjectName("metricLabel")
        label_widget.setAlignment(Qt.AlignCenter)
        
        metric_container.addWidget(value_label)
        metric_container.addWidget(label_widget)
        
        self.metrics_layout.addLayout(metric_container)
        
    def add_content_widget(self, widget: QWidget):
        """Agrega un widget personalizado al área de contenido."""
        self.content_layout.addWidget(widget)
        
    def mousePressEvent(self, event):
        """Maneja clicks en la tarjeta."""
        if event.button() == Qt.LeftButton:
            self.card_clicked.emit(self.card_type)
            logger.debug(f"Magic card clicked: {self.card_type}")
        super().mousePressEvent(event)
        
    def enterEvent(self, event):
        """Maneja entrada del mouse."""
        self.is_hovered = True
        if self.enable_spotlight:
            self.hover_animation.setStartValue(self.spotlight_opacity)
            self.hover_animation.setEndValue(0.15)
            self.hover_animation.start()
            self.spotlight_timer.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Maneja salida del mouse."""
        self.is_hovered = False
        if self.enable_spotlight:
            self.hover_animation.setStartValue(self.spotlight_opacity)
            self.hover_animation.setEndValue(0.0)
            self.hover_animation.start()
            self.spotlight_timer.stop()
        super().leaveEvent(event)
        
    def mouseMoveEvent(self, event):
        """Rastrea la posición del mouse para el efecto spotlight."""
        if self.enable_spotlight and self.is_hovered:
            self.mouse_x = event.x()
            self.mouse_y = event.y()
        super().mouseMoveEvent(event)
        
    def paintEvent(self, event):
        """Renderiza la tarjeta con efectos personalizados."""
        super().paintEvent(event)
        
        if not self.enable_spotlight or not self.is_hovered or self.spotlight_opacity <= 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Crear gradiente radial para el efecto spotlight
        gradient = QRadialGradient(self.mouse_x, self.mouse_y, 150)
        
        # Colores del spotlight basados en el tipo de tarjeta
        spotlight_colors = {
            'portfolio': QColor(16, 185, 129, int(40 * self.spotlight_opacity)),
            'trading': QColor(59, 130, 246, int(40 * self.spotlight_opacity)),
            'performance': QColor(168, 85, 247, int(40 * self.spotlight_opacity)),
            'alert': QColor(239, 68, 68, int(40 * self.spotlight_opacity)),
            'default': QColor(59, 130, 246, int(40 * self.spotlight_opacity))
        }
        
        center_color = spotlight_colors.get(self.card_type, spotlight_colors['default'])
        edge_color = QColor(center_color.red(), center_color.green(), center_color.blue(), 0)
        
        gradient.setColorAt(0.0, center_color)
        gradient.setColorAt(0.7, edge_color)
        gradient.setColorAt(1.0, edge_color)
        
        # Aplicar el gradiente
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        
    def get_spotlight_opacity(self):
        """Getter para la propiedad spotlight_opacity."""
        return self._spotlight_opacity
        
    def set_spotlight_opacity(self, value):
        """Setter para la propiedad spotlight_opacity."""
        self._spotlight_opacity = value
        self.update()
        
    # Propiedad para animaciones
    spotlight_opacity = property(get_spotlight_opacity, set_spotlight_opacity)
    
    def update_content(self, title: str = None, subtitle: str = None):
        """Actualiza el contenido de la tarjeta."""
        if title is not None:
            self.title = title
            self.title_label.setText(title)
            
        if subtitle is not None:
            self.subtitle = subtitle
            self.subtitle_label.setText(subtitle)
            
    def set_card_type(self, card_type: str):
        """Cambia el tipo de tarjeta y actualiza el estilo."""
        self.card_type = card_type
        self._setup_styling()

class PortfolioMagicCard(MagicCardWidget):
    """Magic Card especializada para mostrar información del portafolio."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Portfolio Value",
            subtitle="Total value and performance",
            card_type="portfolio",
            parent=parent
        )
        
        # Métricas específicas del portafolio
        self.add_metric("Total", "$0.00", "neutral")
        self.add_metric("24h Change", "0.00%", "neutral")
        self.add_metric("PnL", "$0.00", "neutral")
        
    def update_portfolio_data(self, total_value: float, change_24h: float, pnl: float):
        """Actualiza los datos del portafolio."""
        # Limpiar métricas existentes
        for i in reversed(range(self.metrics_layout.count())):
            child = self.metrics_layout.itemAt(i)
            if child.layout():
                for j in reversed(range(child.layout().count())):
                    widget = child.layout().itemAt(j).widget()
                    if widget:
                        widget.deleteLater()
                child.layout().deleteLater()
                
        # Agregar métricas actualizadas
        self.add_metric("Total", f"${total_value:,.2f}", "neutral")
        
        change_type = "positive" if change_24h >= 0 else "negative"
        self.add_metric("24h Change", f"{change_24h:+.2f}%", change_type)
        
        pnl_type = "positive" if pnl >= 0 else "negative"
        self.add_metric("PnL", f"${pnl:+,.2f}", pnl_type)

class TradingMagicCard(MagicCardWidget):
    """Magic Card especializada para información de trading."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Trading Status",
            subtitle="Current trading mode and activity",
            card_type="trading",
            parent=parent
        )
        
        self.add_metric("Mode", "Simulado", "neutral")
        self.add_metric("Active", "0", "neutral")
        self.add_metric("Today", "0", "neutral")
        
    def update_trading_data(self, mode: str, active_trades: int, daily_trades: int):
        """Actualiza los datos de trading."""
        # Limpiar métricas existentes
        for i in reversed(range(self.metrics_layout.count())):
            child = self.metrics_layout.itemAt(i)
            if child.layout():
                for j in reversed(range(child.layout().count())):
                    widget = child.layout().itemAt(j).widget()
                    if widget:
                        widget.deleteLater()
                child.layout().deleteLater()
                
        # Agregar métricas actualizadas
        mode_type = "positive" if mode == "Real" else "neutral"
        self.add_metric("Mode", mode, mode_type)
        
        active_type = "positive" if active_trades > 0 else "neutral"
        self.add_metric("Active", str(active_trades), active_type)
        
        daily_type = "positive" if daily_trades > 0 else "neutral"
        self.add_metric("Today", str(daily_trades), daily_type)
