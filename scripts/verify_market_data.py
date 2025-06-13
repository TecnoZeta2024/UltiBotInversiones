import os
import sys
import psycopg
# from dotenv import load_dotenv # REMOVED
from src.ultibot_backend.dependencies import get_settings # ADDED

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def verify_data():
    """
    Connects to the database and checks if the market_data table has any records.
    """
    settings = get_settings() # ADDED

    # Construct DSN for psycopg from AppSettings
    db_dsn = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}" # ADDED

    if not all([settings.db_user, settings.db_password, settings.db_host, settings.db_port, settings.db_name]): # ADDED
        print("❌ ERROR: Database connection parameters are not fully configured in settings.") # ADDED
        return

    print(f"Intentando conectar a la base de datos (postgresql://{settings.db_user}:***@{settings.db_host}:{settings.db_port}/{settings.db_name})...") # ADDED
    
    try:
        with psycopg.connect(db_dsn) as conn: # MODIFIED to use db_dsn
            print("✅ Conexión a la base de datos exitosa.")
            with conn.cursor() as cur:
                print("Consultando la tabla 'market_data'...")
                cur.execute("SELECT COUNT(*) FROM market_data;")
                count = cur.fetchone()[0]
                
                if count > 0:
                    print(f"✅ ÉXITO: La tabla 'market_data' contiene {count} registros.")
                else:
                    print("⚠️ ATENCIÓN: La tabla 'market_data' existe pero está vacía.")
                    print("   Esto sugiere que los datos de la API de Binance no se están persistiendo.")

    except psycopg.errors.UndefinedTable:
        print("❌ ERROR: La tabla 'market_data' no existe en la base de datos.")
        print("   Asegúrate de que la migración '20250609_create_market_data_table.sql' se ha ejecutado.")
    except Exception as e:
        print(f"❌ ERROR INESPERADO: Ocurrió un error al conectar o consultar la base de datos: {e}")

if __name__ == "__main__":
    verify_data()
