import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UltiBot UI")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QLabel("Bienvenido a UltiBot UI")
        # Para alinear, necesitaría: from PyQt5.QtCore import Qt
        # central_widget.setAlignment(Qt.AlignCenter) 
        self.setCentralWidget(central_widget)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
