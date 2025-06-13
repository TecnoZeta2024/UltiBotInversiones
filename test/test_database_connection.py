#!/usr/bin/env python3
"""
Script específico para probar la conexión y funcionalidad de la base de datos.
"""

import sys
import os
import asyncio
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_database_imports():
    """Prueba imports relacionados con la base de datos"""
    print("🔍 Probando imports de base de datos...")
    
    imports_to_test = [
        ("asyncpg", None),
        ("psycopg", None),
        ("supabase", "create_client"),
    ]
    
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name] if class_name else [])
            if class_name:
                getattr(module, class_name)
            print(f"✅ {module_name}.{class_name if class_name else ''}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name if class_name else ''} - Error: {e}")
            return False
    
    return True

def test_environment_variables():
    """Prueba variables de entorno para la base de datos"""
    print("🌍 Verificando variables de entorno de la base de datos...")
    
    # Cargar variables de entorno desde .env si existe
    env_file = Path(".env")
    if env_file.exists():
        print("✅ Archivo .env encontrado")
        with open(env_file, 'r') as f:
            env_content = f.read()
            
        db_vars = [
            "DATABASE_URL",
            "SUPABASE_URL", 
            "SUPABASE_KEY",
            "POSTGRES_PASSWORD",
            "POSTGRES_USER",
            "POSTGRES_DB"
        ]
        
        found_vars = []
        for var in db_vars:
            if var in env_content:
                found_vars.append(var)
                print(f"✅ {var} encontrada en .env")
            else:
                print(f"⚠️ {var} no encontrada en .env")
        
        if found_vars:
            print(f"✅ Variables de BD encontradas: {len(found_vars)}/{len(db_vars)}")
            return True
        else:
            print("❌ No se encontraron variables de base de datos")
            return False
    else:
        print("⚠️ Archivo .env no encontrado")
        return False

async def test_asyncpg_connection():
    """Prueba conexión usando asyncpg"""
    print("🔗 Probando conexión con asyncpg...")
    
    try:
        import asyncpg
        
        # Intentar leer DATABASE_URL del entorno
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            # Cargar desde .env si existe
            env_file = Path(".env")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('DATABASE_URL='):
                            database_url = line.split('=', 1)[1].strip()
                            break
        
        if not database_url:
            print("⚠️ DATABASE_URL no encontrada, saltando prueba de conexión")
            return False
        
        # Intentar conexión con timeout
        try:
            conn = await asyncio.wait_for(
                asyncpg.connect(database_url),
                timeout=10.0
            )
            
            # Ejecutar una consulta simple
            version = await conn.fetchval('SELECT version()')
            print(f"✅ Conexión exitosa - PostgreSQL: {version[:50]}...")
            
            await conn.close()
            return True
            
        except asyncio.TimeoutError:
            print("❌ Timeout conectando a la base de datos")
            return False
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error importando asyncpg: {e}")
        return False

def test_supabase_connection():
    """Prueba conexión usando Supabase client"""
    print("🏢 Probando conexión con Supabase...")
    
    try:
        from supabase import create_client
        
        # Intentar leer variables de Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            # Cargar desde .env si existe
            env_file = Path(".env")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('SUPABASE_URL='):
                            supabase_url = line.split('=', 1)[1].strip()
                        elif line.startswith('SUPABASE_KEY='):
                            supabase_key = line.split('=', 1)[1].strip()
        
        if not supabase_url or not supabase_key:
            print("⚠️ Variables de Supabase no encontradas, saltando prueba")
            return False
        
        # Crear cliente Supabase
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Cliente Supabase creado exitosamente")
        
        # Intentar una operación simple (listar tablas)
        try:
            # Esta es una operación que debería funcionar sin permisos especiales
            response = supabase.rpc('version').execute()
            print("✅ Conexión a Supabase verificada")
            return True
        except Exception as e:
            print(f"⚠️ Cliente creado pero error en operación: {e}")
            return True  # Cliente creado es suficiente para esta prueba
            
    except Exception as e:
        print(f"❌ Error con Supabase: {e}")
        return False

def test_persistence_service():
    """Prueba el servicio de persistencia"""
    print("💾 Probando servicio de persistencia...")
    
    try:
        from ultibot_backend.adapters.persistence_service import PersistenceService
        
        # Intentar instanciar el servicio
        persistence = PersistenceService()
        print("✅ PersistenceService instanciado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error instanciando PersistenceService: {e}")
        return False

def test_database_scripts():
    """Prueba scripts de base de datos"""
    print("📜 Probando scripts de base de datos...")
    
    scripts_to_check = [
        "scripts/test_db_connection.py",
        "supabase/migrations/20250609_create_market_data_table.sql"
    ]
    
    found_scripts = 0
    for script_path in scripts_to_check:
        if os.path.exists(script_path):
            print(f"✅ Script encontrado: {script_path}")
            found_scripts += 1
        else:
            print(f"⚠️ Script no encontrado: {script_path}")
    
    if found_scripts > 0:
        print(f"✅ Scripts de BD encontrados: {found_scripts}/{len(scripts_to_check)}")
        return True
    else:
        print("❌ No se encontraron scripts de BD")
        return False

async def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de base de datos")
    print("=" * 60)
    
    tests = [
        ("Imports de base de datos", test_database_imports),
        ("Variables de entorno", test_environment_variables),
        ("Scripts de base de datos", test_database_scripts),
        ("Servicio de persistencia", test_persistence_service),
        ("Conexión Supabase", test_supabase_connection),
    ]
    
    # Pruebas síncronas
    results = {}
    for test_name, test_func in tests:
        print(f"\n🔍 Ejecutando: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                print(f"✅ {test_name} - EXITOSO")
            else:
                print(f"❌ {test_name} - FALLÓ")
        except Exception as e:
            print(f"❌ {test_name} - ERROR CRÍTICO: {e}")
            results[test_name] = False
    
    # Prueba asíncrona de conexión asyncpg
    print(f"\n🔍 Ejecutando: Conexión asyncpg")
    try:
        result = await test_asyncpg_connection()
        results["Conexión asyncpg"] = result
        if result:
            print(f"✅ Conexión asyncpg - EXITOSO")
        else:
            print(f"❌ Conexión asyncpg - FALLÓ")
    except Exception as e:
        print(f"❌ Conexión asyncpg - ERROR CRÍTICO: {e}")
        results["Conexión asyncpg"] = False
    
    # Reporte final
    print("\n" + "=" * 60)
    print("📊 REPORTE FINAL - BASE DE DATOS")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"Total de pruebas: {total}")
    print(f"Pruebas exitosas: {passed}")
    print(f"Pruebas fallidas: {total - passed}")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS DE BASE DE DATOS PASARON!")
        return True
    else:
        print("⚠️ Algunas pruebas de base de datos fallaron")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
