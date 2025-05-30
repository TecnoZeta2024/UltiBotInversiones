import asyncio
import asyncpg
import os
import sys
from dotenv import load_dotenv
import ssl # Importar el módulo ssl

# Configurar la codificación para Windows
if sys.platform == 'win32':
    # sys.stdout.reconfigure(encoding='utf-8') # Comentado para solucionar error de Pylance
    pass

# Ruta al certificado SSL
SSL_CERT_PATH = 'C:/Users/zamor/UltiBotInversiones/supabase/prod-ca-2021.crt'

# Crear un contexto SSL
ssl_context = ssl.create_default_context(cafile=SSL_CERT_PATH)
ssl_context.check_hostname = True # Habilitar la verificación de hostname
ssl_context.verify_mode = ssl.CERT_REQUIRED # Requerir verificación del certificado
# ADVERTENCIA: ssl.CERT_NONE deshabilitaba la verificación del certificado y era INSEGURO para producción.

def load_supabase_credentials(file_path):
    """Carga las credenciales de Supabase desde el archivo API_Keys.txt."""
    credentials = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Parsear las credenciales de Supabase
            supabase_section = content.split('---')[0]
            for line in supabase_section.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    credentials[key.strip()] = value.strip()
        return credentials
    except FileNotFoundError:
        print(f"[ERROR] Archivo de credenciales no encontrado: {file_path}")
        return None
    except Exception as e:
        print(f"[ERROR] Error al cargar credenciales: {e}")
        return None

# Cargar credenciales al inicio del script
API_KEYS_PATH = 'C:/Users/zamor/UltiBotInversiones/API_Keys.txt'
supabase_creds = load_supabase_credentials(API_KEYS_PATH)

if supabase_creds:
    import urllib.parse # Importar el módulo urllib.parse
    from urllib.parse import urlparse

    PROJECT_IDE = supabase_creds.get("PROJECT_IDE")
    full_url_from_file = supabase_creds.get("URL", "")
    parsed_url = urlparse(full_url_from_file)
    
    # Extraer la contraseña de forma más robusta
    # El formato es postgresql://user:password@host:port/database
    # El password está entre el primer ':' y el '@' en la parte de netloc
    if parsed_url.netloc and '@' in parsed_url.netloc:
        user_pass_part = parsed_url.netloc.split('@')[0]
        if ':' in user_pass_part:
            PASSWORD = urllib.parse.quote_plus(user_pass_part.split(':', 1)[1])
        else:
            PASSWORD = None # No se encontró contraseña en el formato esperado
    else:
        PASSWORD = None # No se encontró netloc o '@'

    # Depuración: Imprimir los componentes de la URL parseada
    print(f"DEBUG: URL completa de API_Keys.txt: {full_url_from_file}")
    print(f"DEBUG: Esquema: {parsed_url.scheme}")
    print(f"DEBUG: Netloc: {parsed_url.netloc}")
    print(f"DEBUG: Usuario parseado: {parsed_url.username}")
    print(f"DEBUG: Contraseña parseada (directa): {parsed_url.password}") # Esto debería ser None
    print(f"DEBUG: Contraseña extraída manualmente: {PASSWORD}")
    print(f"DEBUG: PROJECT_IDE: {PROJECT_IDE}")
    
    # La contraseña está en texto plano en API_Keys.txt. Esto es un riesgo de seguridad.
    # Idealmente, debería estar encriptada y desencriptada en tiempo de ejecución.
else:
    PROJECT_IDE = None
    PASSWORD = None
    print("[ERROR] No se pudieron cargar las credenciales de Supabase. Asegúrate de que 'API_Keys.txt' existe y tiene el formato correcto.")

async def test_direct_connection():
    """Prueba la conexión directa a la base de datos"""
    print("=== Probando conexion directa ===")
    if not PROJECT_IDE or not PASSWORD:
        print("[ERROR] Credenciales de Supabase no disponibles para conexión directa.")
        return False
    try:
        # Parámetros de conexión directa
        db_host = f"db.{PROJECT_IDE}.supabase.co"
        db_user = "postgres"
        db_password = PASSWORD
        db_name = "postgres"
        db_port = 5432

        conn = await asyncpg.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port,
            ssl=ssl_context # Pasar la instancia de SSLContext
        )
        print("[OK] Conexion directa exitosa")
        result = await conn.fetchval("SELECT 1")
        print(f"[OK] Query de prueba: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Error en conexion directa: {e}")
        return False

async def test_pooler_connection(region, port):
    """Prueba la conexión usando el pooler de Supabase con un puerto específico"""
    print(f"\n=== Probando pooler en region {region} (Puerto: {port}) ===")
    if not PROJECT_IDE or not PASSWORD:
        print(f"[ERROR] Credenciales de Supabase no disponibles para conexión al pooler ({region}).")
        return False
    try:
        # URL del pooler construida con credenciales cargadas
        # url = f"postgresql://postgres.{PROJECT_IDE}:{PASSWORD}@aws-0-{region}.pooler.supabase.com:{port}/postgres"
        
        # URL del pooler construida con credenciales cargadas
        url = f"postgresql://postgres.{PROJECT_IDE}:{PASSWORD}@aws-0-{region}.pooler.supabase.com:{port}/postgres"
        print(f"DEBUG: URL de pooler construida: {url}") # Mantener la depuración de la URL construida

        db_host = f"aws-0-{region}.pooler.supabase.com"
        db_user = f"postgres.{PROJECT_IDE}"
        db_password = PASSWORD
        db_name = "postgres"
        db_port = port

        conn = await asyncpg.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port,
            ssl=False # Deshabilitar SSL temporalmente para depuración
        )
        print(f"[OK] Conexion al pooler ({region}) exitosa")
        result = await conn.fetchval("SELECT 1")
        print(f"[OK] Query de prueba: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Error en conexion al pooler ({region}): {e}")
        return False

async def test_env_connection():
    """Prueba la conexión usando la URL del archivo .env"""
    print("\n=== Probando conexion desde .env ===")
    load_dotenv(override=True)
    
    # Verificar si la variable existe
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[ERROR] DATABASE_URL no encontrada en .env")
        return False
    
    print(f"DATABASE_URL: {db_url[:50]}...")  # Mostrar solo los primeros 50 caracteres
    
    try:
        # Conexión desde .env con SSL
        conn = await asyncpg.connect(
            db_url,
            ssl=False # Deshabilitar SSL temporalmente para depuración
        )
        print("[OK] Conexion desde .env exitosa")
        result = await conn.fetchval("SELECT 1")
        print(f"[OK] Query de prueba: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Error en conexion desde .env: {e}")
        return False

async def check_dns_resolution():
    """Verifica si se pueden resolver los hosts"""
    print("\n=== Verificando resolucion DNS ===")
    import socket
    
    if not PROJECT_IDE:
        print("[ADVERTENCIA] PROJECT_IDE no disponible para verificar resolución DNS de hosts de Supabase.")
        return

    hosts = [
        f"db.{PROJECT_IDE}.supabase.co",
        f"aws-0-us-east-1.pooler.supabase.com",
        f"{PROJECT_IDE}.supabase.co"
    ]
    
    for host in hosts:
        try:
            ip = socket.gethostbyname(host)
            print(f"[OK] {host} -> {ip}")
        except socket.gaierror:
            print(f"[ERROR] No se puede resolver: {host}")

async def main():
    print("=== Test de conexiones Supabase ===\n")
    
    # Verificar DNS primero
    await check_dns_resolution()
    
    # Probar conexión directa
    direct_ok = await test_direct_connection()
    
    # Probar conexiones al pooler (Transaction y Session)
    pooler_ok = False

    # Transaction Pooler (Puerto 6543)
    if await test_pooler_connection("sa-east-1", 6543):
        pooler_ok = True
        print(f"\n[OK] Conexión Transaction Pooler (sa-east-1:6543) exitosa.")
        if PROJECT_IDE and PASSWORD:
            print(f"Actualiza tu .env con: DATABASE_URL=postgresql://postgres.{PROJECT_IDE}:{PASSWORD}@aws-0-sa-east-1.pooler.supabase.com:6543/postgres")
    
    # Session Pooler (Puerto 5432)
    if await test_pooler_connection("sa-east-1", 5432):
        pooler_ok = True
        print(f"\n[OK] Conexión Session Pooler (sa-east-1:5432) exitosa.")
        if PROJECT_IDE and PASSWORD:
            print(f"Actualiza tu .env con: DATABASE_URL=postgresql://postgres.{PROJECT_IDE}:{PASSWORD}@aws-0-sa-east-1.pooler.supabase.com:5432/postgres")
    
    # Probar conexión desde .env
    env_ok = await test_env_connection()
    
    print("\n=== Resumen ===")
    print(f"Conexion directa: {'[OK]' if direct_ok else '[ERROR]'}")
    print(f"Conexion pooler: {'[OK]' if pooler_ok else '[ERROR]'}")
    print(f"Conexion .env: {'[OK]' if env_ok else '[ERROR]'}")
    
    if not direct_ok and not pooler_ok:
        print("\n[ADVERTENCIA] Ninguna conexion funciono. Posibles causas:")
        print("1. Las credenciales pueden ser incorrectas")
        print("2. La IP de tu maquina puede no estar autorizada")
        print("3. El proyecto de Supabase puede estar pausado")
        print("4. Problemas de red o firewall")
        print("5. Error en el nombre del proyecto (verificar el project ID)")
    
    print("\n[ADVERTENCIA DE SEGURIDAD] La verificación del certificado SSL está deshabilitada (ssl.CERT_NONE). Esto es INSEGURO para producción.")
    print("[ADVERTENCIA DE SEGURIDAD] La contraseña se lee en texto plano de 'API_Keys.txt'. Debería estar encriptada.")

if __name__ == "__main__":
    asyncio.run(main())
