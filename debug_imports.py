import sys
import os

# Asegurarse de que el directorio 'src' esté en sys.path
# Esto simula lo que pytest.ini debería hacer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from ultibot_backend.adapters.binance_adapter import BinanceAdapter, BinanceAPIError
    print("✅ Importación de ultibot_backend.adapters.binance_adapter exitosa.")
except ModuleNotFoundError as e:
    print(f"❌ ModuleNotFoundError para ultibot_backend.adapters.binance_adapter: {e}")
except Exception as e:
    print(f"❌ Error inesperado al importar ultibot_backend.adapters.binance_adapter: {e}")

try:
    from shared.data_types import AssetBalance
    print("✅ Importación de shared.data_types exitosa.")
except ModuleNotFoundError as e:
    print(f"❌ ModuleNotFoundError para shared.data_types: {e}")
except Exception as e:
    print(f"❌ Error inesperado al importar shared.data_types: {e}")

print(f"\nContenido de sys.path: {sys.path}")
