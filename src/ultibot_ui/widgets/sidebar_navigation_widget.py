"""
Enhanced Sidebar Navigation Widget - Navegación moderna con efectos visuales
Versión 2.0 - Incorpora efectos hover avanzados y transiciones suaves
"""
import logging
from typing import Optional, Dict, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, 
    QFrame, QHBoxLayout, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QIcon, QPainter, QColor, QLinearGradient, QBrush, QPen
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer

logger = logging.getLogger(__name__)

class ModernNavButton(QPushButton):
    """
    Botón de navegación con efectos visuales modernos.
    Incluye animaciones de hover, efectos de glow y feedback visual.
    """
    
    def __init__(self, text: str, name: str, icon_name: str = None, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        
        self.button_name = name
        self.icon_name = icon_name
        self.is_hovered = False
        self.is_selected = False
        
        # Inicializar atributos privados ANTES de usar las propiedades
        self._glow_opacity = 0.0
        self._hover_progress = 0.0
        
        # Configuración del botón
        self.setObjectName(f"navButton_{name}")
        self.setCheckable(True)
        self.setFixedHeight(48)
        self.setMinimumWidth(200)
        
        # Animaciones
        self.hover_animation = QPropertyAnimation(self, b"hover_progress")
        self.hover_animation.setDuration(250)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.glow_animation = QPropertyAnimation(self, b"glow_opacity")
        self.glow_animation.setDuration(200)
        self.glow_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Timer para efectos
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.setInterval(16)  # ~60fps
        
        self._setup_styling()
        
    def _setup_styling(self):
        """Configura el estilo base del botón."""
        self.setStyleSheet("""
            ModernNavButton {
                text-align: left;
                padding: 12px 20px;
                border: none;
                border-radius: 12px;
                background-color: transparent;
                color: #94A3B8;
                font-size: 15px;
                font-weight: 500;
            }
            
            ModernNavButton:checked {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B82F6,
                    stop:0.5 #2563EB,
                    stop:1 #1D4ED8
                );
                color: #FFFFFF;
                font-weight: 600;
            }
        """)
        
    def enterEvent(self, event):
        """Maneja la entrada del mouse."""
        self.is_hovered = True
        self.hover_animation.setStartValue(self.hover_progress)
        self.hover_animation.setEndValue(1.0)
        self.hover_animation.start()
        
        if not self.is_selected:
            self.glow_animation.setStartValue(self.glow_opacity)
            self.glow_animation.setEndValue(0.3)
            self.glow_animation.start()
            
        self.update_timer.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Maneja la salida del mouse."""
        self.is_hovered = False
        self.hover_animation.setStartValue(self.hover_progress)
        self.hover_animation.setEndValue(0.0)
        self.hover_animation.start()
        
        if not self.is_selected:
            self.glow_animation.setStartValue(self.glow_opacity)
            self.glow_animation.setEndValue(0.0)
            self.glow_animation.start()
            
        self.update_timer.stop()
        super().leaveEvent(event)
        
    def setChecked(self, checked: bool):
        """Override para manejar el estado seleccionado."""
        self.is_selected = checked
        super().setChecked(checked)
        
        if checked:
            self.glow_animation.setStartValue(self.glow_opacity)
            self.glow_animation.setEndValue(0.6)
            self.glow_animation.start()
        elif not self.is_hovered:
            self.glow_animation.setStartValue(self.glow_opacity)
            self.glow_animation.setEndValue(0.0)
            self.glow_animation.start()
            
    def paintEvent(self, event):
        """Renderiza el botón con efectos personalizados."""
        super().paintEvent(event)
        
        if self.glow_opacity <= 0 and self.hover_progress <= 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Efecto de glow/hover
        if self.hover_progress > 0 or self.glow_opacity > 0:
            # Color base para el hover
            hover_color = QColor(59, 130, 246, int(30 * self.hover_progress))
            if not self.is_selected:
                painter.fillRect(self.rect(), hover_color)
                
            # Borde de glow
            if self.glow_opacity > 0:
                glow_color = QColor(59, 130, 246, int(60 * self.glow_opacity))
                pen = QPen(glow_color)
                pen.setWidth(2)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
                
    def get_hover_progress(self):
        """Getter para hover_progress."""
        return self._hover_progress
        
    def set_hover_progress(self, value):
        """Setter para hover_progress."""
        self._hover_progress = value
        self.update()
        
    def get_glow_opacity(self):
        """Getter para glow_opacity."""
        return self._glow_opacity
        
    def set_glow_opacity(self, value):
        """Setter para glow_opacity."""
        self._glow_opacity = value
        self.update()
        
    # Propiedades para animaciones
    hover_progress = property(get_hover_progress, set_hover_progress)
    glow_opacity = property(get_glow_opacity, set_glow_opacity)

class SidebarNavigationWidget(QWidget):
    """
    Widget de navegación lateral moderno con efectos visuales avanzados.
    Incluye transiciones suaves, efectos de glow y feedback visual mejorado.
    """
    
    navigation_requested = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Estado del sidebar
        self.nav_buttons: Dict[str, ModernNavButton] = {}
        self.current_selection = "dashboard"
        
        # Configuración visual
        self.setFixedWidth(280)
        self.setMinimumHeight(600)
        
        self._setup_ui()
        self._setup_styling()
        
    def _setup_ui(self):
        """Configura la estructura de la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)

        # Header del sidebar con logo/título
        self._create_header(layout)
        
        # Espaciador
        layout.addSpacing(20)
        
        # Botones de navegación principales
        self._create_navigation_buttons(layout)
        
        # Espaciador flexible
        layout.addStretch(1)
        
        # Footer opcional (para información adicional)
        self._create_footer(layout)
        
    def _create_header(self, layout: QVBoxLayout):
        """Crea el header del sidebar con logo y título."""
        header_container = QFrame()
        header_container.setObjectName("sidebarHeader")
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(12, 16, 12, 16)
        header_layout.setSpacing(8)
        
        # Logo/Título principal
        logo_label = QLabel("UltiBot")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setObjectName("logoLabel")
        
        # Subtítulo
        subtitle_label = QLabel("Trading Platform")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setObjectName("subtitleLabel")
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_container)
        
    def _create_navigation_buttons(self, layout: QVBoxLayout):
        """Crea los botones de navegación principales."""
        # Definición de botones de navegación
        nav_items = [
            ("Dashboard", "dashboard", "dashboard"),
            ("Oportunidades", "opportunities", "search"),
            ("Portafolio", "portfolio", "wallet"),
            ("Estrategias", "strategies", "settings"),
            ("Historial", "history", "clock"),
            ("Configuración", "settings", "cog")
        ]
        
        # Container para botones
        nav_container = QFrame()
        nav_container.setObjectName("navContainer")
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(8, 12, 8, 12)
        nav_layout.setSpacing(4)
        
        for text, name, icon in nav_items:
            button = self._create_nav_button(text, name, icon)
            self.nav_buttons[name] = button
            nav_layout.addWidget(button)
            
        layout.addWidget(nav_container)
        
        # Seleccionar dashboard por defecto
        self.nav_buttons["dashboard"].setChecked(True)
        
    def _create_nav_button(self, text: str, name: str, icon_name: str) -> ModernNavButton:
        """Crea un botón de navegación individual."""
        button = ModernNavButton(text, name, icon_name, self)
        button.clicked.connect(lambda: self._on_nav_button_clicked(name))
        return button
        
    def _create_footer(self, layout: QVBoxLayout):
        """Crea el footer del sidebar."""
        footer_container = QFrame()
        footer_container.setObjectName("sidebarFooter")
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(12, 8, 12, 16)
        footer_layout.setSpacing(4)
        
        # Estado de conexión
        status_label = QLabel("● Connected")
        status_label.setObjectName("statusLabel")
        status_label.setAlignment(Qt.AlignCenter)
        
        # Versión
        version_label = QLabel("v2.0.0")
        version_label.setObjectName("versionLabel")
        version_label.setAlignment(Qt.AlignCenter)
        
        footer_layout.addWidget(status_label)
        footer_layout.addWidget(version_label)
        
        layout.addWidget(footer_container)
        
    def _setup_styling(self):
        """Configura el estilo del sidebar."""
        self.setStyleSheet("""
            SidebarNavigationWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0F172A,
                    stop:0.5 #1E293B,
                    stop:1 #0F172A
                );
                border: none;
                border-right: 1px solid rgba(75, 85, 99, 0.2);
            }
            
            QFrame#sidebarHeader {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(59, 130, 246, 0.1),
                    stop:1 rgba(59, 130, 246, 0.05)
                );
                border-radius: 16px;
                border: 1px solid rgba(59, 130, 246, 0.2);
            }
            
            QLabel#logoLabel {
                font-size: 24px;
                font-weight: 700;
                color: #F8FAFC;
                background: transparent;
            }
            
            QLabel#subtitleLabel {
                font-size: 12px;
                font-weight: 500;
                color: #64748B;
                background: transparent;
            }
            
            QFrame#navContainer {
                background: rgba(30, 41, 59, 0.3);
                border-radius: 16px;
                border: 1px solid rgba(75, 85, 99, 0.1);
            }
            
            QFrame#sidebarFooter {
                background: rgba(15, 23, 42, 0.5);
                border-radius: 12px;
                border: 1px solid rgba(75, 85, 99, 0.1);
            }
            
            QLabel#statusLabel {
                font-size: 12px;
                font-weight: 500;
                color: #10B981;
                background: transparent;
            }
            
            QLabel#versionLabel {
                font-size: 11px;
                font-weight: 400;
                color: #64748B;
                background: transparent;
            }
        """)
        
        # Aplicar efecto de sombra al widget principal
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(15)
        shadow_effect.setXOffset(2)
        shadow_effect.setYOffset(0)
        shadow_effect.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow_effect)

    def _on_nav_button_clicked(self, name: str):
        """Maneja el click en un botón de navegación."""
        # Desmarcar todos los botones excepto el actual
        for button_name, button in self.nav_buttons.items():
            if button_name != name:
                button.setChecked(False)
                
        # Marcar el botón actual
        self.nav_buttons[name].setChecked(True)
        self.current_selection = name
        
        # Emitir señal de navegación
        self.navigation_requested.emit(name)
        logger.info(f"Navigation requested: {name}")
        
    def set_active_button(self, name: str):
        """Establece el botón activo programáticamente."""
        if name in self.nav_buttons:
            self._on_nav_button_clicked(name)
            
    def get_active_button(self) -> str:
        """Retorna el nombre del botón actualmente activo."""
        return self.current_selection
        
    def add_notification_badge(self, button_name: str, count: int = None):
        """
        Agrega una insignia de notificación a un botón.
        
        Args:
            button_name: Nombre del botón
            count: Número a mostrar (None para punto simple)
        """
        if button_name in self.nav_buttons:
            button = self.nav_buttons[button_name]
            # Implementar lógica de badges si es necesario
            # Por ahora, solo cambiar el estilo para indicar notificación
            if count and count > 0:
                button.setStyleSheet(button.styleSheet() + """
                    ModernNavButton {
                        border-left: 3px solid #EF4444;
                    }
                """)
                
    def remove_notification_badge(self, button_name: str):
        """Remueve la insignia de notificación de un botón."""
        if button_name in self.nav_buttons:
            button = self.nav_buttons[button_name]
            # Resetear estilo
            button._setup_styling()
            
    def update_connection_status(self, is_connected: bool):
        """Actualiza el estado de conexión en el footer."""
        status_label = self.findChild(QLabel, "statusLabel")
        if status_label:
            if is_connected:
                status_label.setText("● Connected")
                status_label.setStyleSheet("QLabel#statusLabel { color: #10B981; }")
            else:
                status_label.setText("● Disconnected")
                status_label.setStyleSheet("QLabel#statusLabel { color: #EF4444; }")
                
    def enable_button(self, button_name: str, enabled: bool = True):
        """Habilita o deshabilita un botón específico."""
        if button_name in self.nav_buttons:
            self.nav_buttons[button_name].setEnabled(enabled)
