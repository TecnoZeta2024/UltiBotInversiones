import os
os.environ['QT_API'] = 'pyside6'

from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno antes de ejecutar cualquier prueba
dotenv_path = Path(__file__).parent.parent / ".env.test"
load_dotenv(dotenv_path=dotenv_path, override=True)
