import sys
import logging

# Configuración básica de logging para ver si se alcanza este punto
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/pyqt_test.log", mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("Iniciando prueba de PyQt5...")

try:
    from PyQt5.QtWidgets import QApplication, QLabel
    logging.info("Importación de QApplication y QLabel exitosa.")
except Exception as e:
    logging.critical(f"Fallo al importar de PyQt5.QtWidgets: {e}", exc_info=True)
    sys.exit(1)

try:
    app = QApplication(sys.argv)
    logging.info("Instancia de QApplication creada exitosamente.")
    
    label = QLabel("¡PyQt5 funciona!")
    label.show()
    logging.info("QLabel mostrada. Entrando al bucle de eventos.")
    
    sys.exit(app.exec_())
except Exception as e:
    logging.critical(f"Fallo durante la ejecución de la aplicación PyQt5: {e}", exc_info=True)
    sys.exit(1)
