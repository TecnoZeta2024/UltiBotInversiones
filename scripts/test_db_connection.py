import asyncio
import os
import sys
import psycopg
from dotenv import load_dotenv

# Solución para Windows ProactorEventLoop con psycopg/asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_connection():
    """
    Intenta conectarse a la base de datos de Supabase usando la URL del .env
    e imprime un mensaje de éxito o error.
    """
    load_dotenv(dotenv_path='.env', override=True)
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("ERROR: La variable de entorno DATABASE_URL no está definida en el archivo .env.")
        return

    print(f"Intentando conectar a la base de datos con la URL: {db_url[:50]}...")

    try:
        # Intenta conectar usando la URL completa
        async with await psycopg.AsyncConnection.connect(db_url, sslmode='verify-full', sslrootcert='supabase/prod-ca-2021.crt') as aconn:
            async with aconn.cursor() as acur:
                await acur.execute("SELECT 1;")
                result = await acur.fetchone()
                if result and result[0] == 1:
                    print("\n✅ CONEXIÓN EXITOSA A LA BASE DE DATOS DE SUPABASE.")
                else:
                    print("\n❌ FALLO EN LA CONEXIÓN: La consulta de prueba no devolvió el resultado esperado.")
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
