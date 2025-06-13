#!/usr/bin/env python3
"""
Script para verificar que el entorno de desarrollo esté configurado correctamente.
"""

import sys
import os
import subprocess
from pathlib import Path

def test_python_version():
    """Verifica la versión de Python"""
    print("🐍 Verificando versión de Python...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Se requiere Python 3.11+")
        return False

def test_poetry_installation():
    """Verifica que Poetry esté instalado"""
    print("📝 Verificando instalación de Poetry...")
    
    try:
        result = subprocess.run(
            ["poetry", "--version"], 
            capture_output=True, 
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
            return True
        else:
            print("❌ Poetry instalado pero no responde correctamente")
            return False
    except FileNotFoundError:
        print("❌ Poetry no encontrado en el PATH")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Poetry timeout")
        return False

def test_project_structure():
    """Verifica la estructura del proyecto"""
    print("📁 Verificando estructura del proyecto...")
    
    required_dirs = [
        "src",
        "src/ultibot_backend", 
        "src/ultibot_ui",
        "tests",
        "scripts",
        "logs",
        "docs"
    ]
    
    required_files = [
        "pyproject.toml",
        "README.md",
        "run.py",
        ".gitignore",
        ".env.example"
    ]
    
    missing_items = []
    
    # Verificar directorios
    for directory in required_dirs:
        if os.path.exists(directory) and os.path.isdir(directory):
            print(f"✅ Directorio {directory}")
        else:
            print(f"❌ Directorio {directory} no encontrado")
            missing_items.append(directory)
    
    # Verificar archivos
    for file_path in required_files:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"✅ Archivo {file_path}")
        else:
            print(f"❌ Archivo {file_path} no encontrado")
            missing_items.append(file_path)
    
    if not missing_items:
        print("✅ Estructura del proyecto completa")
        return True
    else:
        print(f"❌ {len(missing_items)} elementos faltantes en la estructura")
        return False

def test_environment_files():
    """Verifica archivos de configuración de entorno"""
    print("🌍 Verificando archivos de entorno...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_example.exists():
        print("✅ Archivo .env.example encontrado")
        
        # Leer variables esperadas del .env.example
        with open(env_example, 'r') as f:
            example_content = f.read()
        
        important_vars = [
            "DATABASE_URL",
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "BINANCE_API_KEY",
            "BINANCE_SECRET_KEY"
        ]
        
        found_vars = 0
        for var in important_vars:
            if var in example_content:
                print(f"✅ Variable {var} en .env.example")
                found_vars += 1
            else:
                print(f"⚠️ Variable {var} no en .env.example")
        
        example_ok = found_vars > 0
    else:
        print("❌ Archivo .env.example no encontrado")
        example_ok = False
    
    if env_file.exists():
        print("✅ Archivo .env encontrado")
        env_ok = True
    else:
        print("⚠️ Archivo .env no encontrado (copiar desde .env.example)")
        env_ok = False
    
    return example_ok and env_ok

def test_dependencies():
    """Verifica dependencias principales"""
    print("📦 Verificando dependencias principales...")
    
    critical_packages = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "asyncpg",
        "supabase",
        "pytest"
    ]
    
    missing_packages = []
    
    for package in critical_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - No instalado")
            missing_packages.append(package)
    
    if not missing_packages:
        print("✅ Todas las dependencias críticas están disponibles")
        return True
    else:
        print(f"❌ {len(missing_packages)} dependencias faltantes")
        print("   Ejecutar: poetry install")
        return False

def test_optional_dependencies():
    """Verifica dependencias opcionales"""
    print("🎨 Verificando dependencias opcionales...")
    
    optional_packages = [
        ("PyQt5", "Qt5"),
        ("PyQt6", "Qt6"), 
        ("PySide2", "PySide2"),
        ("PySide6", "PySide6"),
        ("matplotlib", "Gráficos"),
        ("pandas", "Análisis de datos")
    ]
    
    available_packages = []
    
    for package, description in optional_packages:
        try:
            __import__(package)
            print(f"✅ {package} ({description})")
            available_packages.append(package)
        except ImportError:
            print(f"⚠️ {package} ({description}) - Opcional, no instalado")
    
    if available_packages:
        print(f"✅ {len(available_packages)} dependencias opcionales disponibles")
    else:
        print("⚠️ No se encontraron dependencias opcionales")
    
    return True  # Las dependencias opcionales no son críticas

def test_git_repository():
    """Verifica configuración de Git"""
    print("🔄 Verificando repositorio Git...")
    
    if os.path.exists(".git"):
        print("✅ Repositorio Git inicializado")
        
        try:
            # Verificar estado del repositorio
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print("✅ Git funcional")
                return True
            else:
                print("⚠️ Git inicializado pero con problemas")
                return True  # No es crítico
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠️ Git no disponible en PATH")
            return True  # No es crítico
    else:
        print("⚠️ No es un repositorio Git")
        return True  # No es crítico

def test_logs_directory():
    """Verifica directorio de logs"""
    print("📊 Verificando directorio de logs...")
    
    logs_dir = Path("logs")
    if logs_dir.exists():
        print("✅ Directorio logs existe")
        
        # Verificar permisos de escritura
        test_file = logs_dir / "test_write.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()
            print("✅ Permisos de escritura en logs")
            return True
        except Exception as e:
            print(f"❌ Sin permisos de escritura en logs: {e}")
            return False
    else:
        print("❌ Directorio logs no existe")
        try:
            logs_dir.mkdir()
            print("✅ Directorio logs creado")
            return True
        except Exception as e:
            print(f"❌ No se pudo crear directorio logs: {e}")
            return False

def main():
    """Función principal"""
    print("🚀 Verificando configuración del entorno de desarrollo")
    print("=" * 70)
    
    tests = [
        ("Versión de Python", test_python_version),
        ("Instalación de Poetry", test_poetry_installation),
        ("Estructura del proyecto", test_project_structure),
        ("Archivos de entorno", test_environment_files),
        ("Dependencias críticas", test_dependencies),
        ("Dependencias opcionales", test_optional_dependencies),
        ("Repositorio Git", test_git_repository),
        ("Directorio de logs", test_logs_directory),
    ]
    
    results = {}
    critical_tests = [
        "Versión de Python",
        "Instalación de Poetry", 
        "Estructura del proyecto",
        "Dependencias críticas",
        "Directorio de logs"
    ]
    
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
    
    # Reporte final
    print("\n" + "=" * 70)
    print("📊 REPORTE FINAL - CONFIGURACIÓN DEL ENTORNO")
    print("=" * 70)
    
    total = len(results)
    passed = sum(results.values())
    critical_passed = sum(1 for test_name in critical_tests if results.get(test_name, False))
    critical_total = len(critical_tests)
    
    print(f"Total de pruebas: {total}")
    print(f"Pruebas exitosas: {passed}")
    print(f"Pruebas fallidas: {total - passed}")
    print(f"Pruebas críticas exitosas: {critical_passed}/{critical_total}")
    
    # Determinar si el entorno está listo
    if critical_passed == critical_total:
        print("🎉 ¡ENTORNO LISTO PARA DESARROLLO!")
        
        if passed == total:
            print("✨ Configuración perfecta - todos los componentes disponibles")
        else:
            print("⚠️ Algunos componentes opcionales faltantes pero funcional")
        
        # Mostrar siguientes pasos
        print("\n📋 SIGUIENTES PASOS RECOMENDADOS:")
        if not results.get("Archivos de entorno", True):
            print("  1. Copiar .env.example a .env y configurar variables")
        print("  2. Ejecutar: poetry install")
        print("  3. Ejecutar: python test/run_quick_tests.bat")
        
        return True
    else:
        print("❌ ENTORNO NO LISTO - Corregir errores críticos")
        
        print("\n🔧 ACCIONES REQUERIDAS:")
        for test_name in critical_tests:
            if not results.get(test_name, False):
                print(f"  - Corregir: {test_name}")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
