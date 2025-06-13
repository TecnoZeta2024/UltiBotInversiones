import asyncio
import os
import sys
import psycopg
from src.ultibot_backend.dependencies import get_settings # Changed

# Solución para Windows ProactorEventLoop con psycopg/asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_connection():
    """
    Intenta conectarse a la base de datos de Supabase, verifica la conexión
    y comprueba si la tabla 'user_configurations' es accesible.
    """
    settings = get_settings() # Changed
    
    # Construct DSN for psycopg from AppSettings
    db_url = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}" # Changed

    if not all([settings.db_user, settings.db_password, settings.db_host, settings.db_port, settings.db_name]): # Changed
        print("ERROR: Database connection parameters are not fully configured in settings.") # Changed
        return

    print(f"Intentando conectar a la base de datos con DSN: postgresql://{settings.db_user}:***@{settings.db_host}:{settings.db_port}/{settings.db_name}") # Changed

    try:
        # Intenta conectar usando la URL completa
        # Assuming 'supabase/prod-ca-2021.crt' is available in the execution path
        async with await psycopg.AsyncConnection.connect(db_url, sslmode='verify-full', sslrootcert='supabase/prod-ca-2021.crt') as aconn:
            async with aconn.cursor() as acur:
                # 1. Verificar conexión básica
                await acur.execute("SELECT 1;")
                result = await acur.fetchone()
                if not (result and result[0] == 1):
                    print("\n❌ FALLO EN LA CONEXIÓN: La consulta de prueba no devolvió el resultado esperado.")
                    return
                print("\n✅ CONEXIÓN BÁSICA A LA BASE DE DATOS EXITOSA.")

                # 2. Verificar acceso a la tabla 'user_configurations'
                print("\nIntentando leer de la tabla 'user_configurations'...")
                await acur.execute("SELECT * FROM user_configurations LIMIT 1;")
                record = await acur.fetchone()
                if record:
                    print("✅ ACCESO EXITOSO a la tabla 'user_configurations'. Se encontró al menos un registro.")
                else:
                    print("✅ ACCESO EXITOSO a la tabla 'user_configurations', pero está vacía.")
                
                print("\n✅ PRUEBA DE CONEXIÓN Y ACCESO A TABLA COMPLETADA EXITOSAMENTE.")

    except psycopg.errors.UndefinedTable:
        print("\n❌ ERROR: La tabla 'user_configurations' no existe en la base de datos.")
        print("   Por favor, asegúrese de que las migraciones se han ejecutado correctamente.")
    except psycopg.OperationalError as e:
        print(f"\n❌ ERROR DE OPERACIÓN PSICOPG: No se pudo conectar a la base de datos.")
        print(f"   Detalles: {e}")
    except Exception as e:
        print(f"\n❌ OCURRIÓ UN ERROR INESPERADO: {e}")

if __name__ == "__main__":
    # En Windows, es posible que necesitemos ejecutar el loop de esta manera
    if sys.platform == "win32":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_connection())
    else:
        asyncio.run(test_connection())
