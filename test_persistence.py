import asyncio
import os
from dotenv import load_dotenv
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.app_config import settings
import uuid
import json

# Cargar variables de entorno desde .env
load_dotenv()

async def run_tests():
    print("Iniciando pruebas de conexión y persistencia...")
    
    # Asegurarse de que las configuraciones se carguen
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"SUPABASE_URL: {settings.SUPABASE_URL}")
    print(f"SUPABASE_KEY: {settings.SUPABASE_KEY}")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {settings.SUPABASE_SERVICE_ROLE_KEY}")
    print(f"ENCRYPTION_KEY: {settings.ENCRYPTION_KEY}")

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
        insert_query = """
        INSERT INTO user_configurations (user_id, selected_theme, enable_telegram_notifications, default_paper_trading_capital, notification_preferences)
        VALUES ($1, $2, $3, $4, $5::jsonb)
        RETURNING id, user_id, selected_theme;
        """
        inserted_row = await service.connection.fetchrow(
            insert_query,
            user_config_data["user_id"],
            user_config_data["selected_theme"],
            user_config_data["enable_telegram_notifications"],
            user_config_data["default_paper_trading_capital"],
            user_config_data["notification_preferences"]
        )
        
        if inserted_row:
            print(f"Inserción exitosa. ID de configuración: {inserted_row['id']}, User ID: {inserted_row['user_id']}")
            
            # Leer datos
            select_query = "SELECT user_id, selected_theme, default_paper_trading_capital FROM user_configurations WHERE user_id = $1;"
            fetched_row = await service.connection.fetchrow(select_query, test_user_id)
            
            if fetched_row and fetched_row['user_id'] == uuid.UUID(test_user_id):
                print(f"Lectura exitosa. User ID: {fetched_row['user_id']}, Tema: {fetched_row['selected_theme']}, Capital: {fetched_row['default_paper_trading_capital']}")
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
        try:
            delete_query = "DELETE FROM user_configurations WHERE user_id = $1;"
            await service.connection.execute(delete_query, test_user_id)
            print(f"Fila de prueba para user_id {test_user_id} eliminada.")
        except Exception as e:
            print(f"Error al limpiar la fila de prueba: {e}")
        
        await service.disconnect()

if __name__ == "__main__":
    asyncio.run(run_tests())
