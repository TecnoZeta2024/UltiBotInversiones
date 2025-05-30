import asyncio
import platform # Para verificar el sistema operativo
import os

# Configurar la política del bucle de eventos para Windows ANTES de otras importaciones de asyncio o librerías que lo usen.
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.app_config import settings
import uuid
import json

# Cargar variables de entorno desde .env
load_dotenv()
from psycopg.rows import dict_row # Importar dict_row para los cursores si es necesario en este script
import uuid
import json


async def run_tests():
    print("Iniciando pruebas de conexión y persistencia...")
    
    # Asegurarse de que las configuraciones se carguen
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"SUPABASE_URL: {settings.SUPABASE_URL}")
    print(f"SUPABASE_ANON_KEY: {settings.SUPABASE_ANON_KEY}") # Corregido de SUPABASE_KEY
    print(f"SUPABASE_SERVICE_ROLE_KEY: {settings.SUPABASE_SERVICE_ROLE_KEY}")
    print(f"CREDENTIAL_ENCRYPTION_KEY: {settings.CREDENTIAL_ENCRYPTION_KEY}") # Corregido de ENCRYPTION_KEY

    service = SupabasePersistenceService()
    
    # Prueba de conexión
    print("\nRealizando prueba de conexión...")
    if await service.test_connection():
        print("Prueba de conexión exitosa.")
    else:
        print("Prueba de conexión fallida. Revisa tu DATABASE_URL en .env")
        await service.disconnect()
        return

    # Prueba de inserción y lectura en user_configurations
    print("\nRealizando prueba de inserción y lectura en user_configurations...")
    try:
        # Generar un user_id único para la prueba
        test_user_id = str(uuid.uuid4())
        
        # Datos de prueba
        user_config_data = {
            "user_id": test_user_id,
            "selected_theme": "dark",
            "enable_telegram_notifications": True,
            "default_paper_trading_capital": 1000.00,
            "notification_preferences": json.dumps([
                {"eventType": "REAL_TRADE_EXECUTED", "channel": "telegram", "isEnabled": True}
            ])
        }
        
        # Insertar datos
        # Los métodos específicos para test ahora están en SupabasePersistenceService
        # Así que llamaremos a esos métodos.
        
        # Asegurarse de que la conexión esté activa y sea utilizable
        if not service.connection or service.connection.closed:
            await service.connect() # Reconectar si es necesario
        
        # Usar un cursor para las operaciones
        async with service.connection.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                INSERT INTO user_configurations (user_id, selected_theme, enable_telegram_notifications, default_paper_trading_capital, notification_preferences)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                RETURNING id, user_id, selected_theme;
                """,
                (
                    uuid.UUID(user_config_data["user_id"]), # Asegurar que user_id es UUID
                    user_config_data["selected_theme"],
                    user_config_data["enable_telegram_notifications"],
                    user_config_data["default_paper_trading_capital"],
                    user_config_data["notification_preferences"]
                )
            )
            inserted_row = await cur.fetchone()
        
        if inserted_row:
            print(f"Inserción exitosa. ID de configuración: {inserted_row.get('id')}, User ID: {inserted_row.get('user_id')}")
            
            # Leer datos
            async with service.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    "SELECT user_id, selected_theme, default_paper_trading_capital FROM user_configurations WHERE user_id = %s;",
                    (uuid.UUID(test_user_id),)
                )
                fetched_row = await cur.fetchone()
            
            if fetched_row and fetched_row.get('user_id') == uuid.UUID(test_user_id):
                print(f"Lectura exitosa. User ID: {fetched_row.get('user_id')}, Tema: {fetched_row.get('selected_theme')}, Capital: {fetched_row.get('default_paper_trading_capital')}")
                print("Prueba de inserción y lectura en user_configurations exitosa.")
            else:
                print("Error: Los datos leídos no coinciden o no se encontraron.")
                print("Prueba de inserción y lectura en user_configurations fallida.")
        else:
            print("Error: No se pudo insertar la fila.")
            print("Prueba de inserción y lectura en user_configurations fallida.")

    except Exception as e:
        print(f"Error durante la prueba de inserción/lectura: {e}")
        print("Prueba de inserción y lectura en user_configurations fallida.")
    finally:
        # Limpiar: eliminar la fila insertada
        if service.connection and not service.connection.closed:
            try:
                async with service.connection.cursor() as cur:
                    await cur.execute(
                        "DELETE FROM user_configurations WHERE user_id = %s;",
                        (uuid.UUID(test_user_id),)
                    )
                print(f"Fila de prueba para user_id {test_user_id} eliminada.")
            except Exception as e:
                print(f"Error al limpiar la fila de prueba: {e}")
        
        await service.disconnect()

if __name__ == "__main__":
    asyncio.run(run_tests())
