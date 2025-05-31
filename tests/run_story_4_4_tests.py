#!/usr/bin/env python3
"""
Script para ejecutar los tests de la Historia 4.4 - Gestión de Capital y TSL/TP para Operaciones Reales.

Este script ejecuta específicamente los tests relacionados con la Historia 4.4 para verificar:
- Gestión de capital para operaciones reales
- Lógica de TSL/TP para operaciones reales  
- Flujo completo de integración
- Casos edge y condiciones límite

Uso:
    python tests/run_story_4_4_tests.py
    
    # Para ejecutar solo tests unitarios:
    python tests/run_story_4_4_tests.py --unit-only
    
    # Para ejecutar solo tests de integración:
    python tests/run_story_4_4_tests.py --integration-only
    
    # Para ejecutar con output detallado:
    python tests/run_story_4_4_tests.py --verbose
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_tests(test_pattern: str, verbose: bool = False) -> int:
    """
    Ejecuta tests usando pytest con el patrón especificado.
    
    Args:
        test_pattern: Patrón de archivos de test a ejecutar
        verbose: Si mostrar output detallado
        
    Returns:
        Código de salida del proceso pytest
    """
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-v")
    
    # Añadir patrón de archivos
    cmd.append(test_pattern)
    
    # Configuraciones adicionales
    cmd.extend([
        "--tb=short",  # Traceback corto para mejor legibilidad
        "--strict-markers",  # Requerir markers definidos
        "--disable-warnings",  # Suprimir warnings menores
    ])
    
    print(f"Ejecutando: {' '.join(cmd)}")
    print("=" * 80)
    
    result = subprocess.run(cmd, cwd=Path.cwd())
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Ejecutar tests de la Historia 4.4 - Gestión de Capital y TSL/TP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s                     # Ejecutar todos los tests de la historia 4.4
  %(prog)s --unit-only         # Solo tests unitarios
  %(prog)s --integration-only  # Solo tests de integración
  %(prog)s --verbose           # Output detallado
        """
    )
    
    parser.add_argument(
        "--unit-only", 
        action="store_true",
        help="Ejecutar solo tests unitarios relacionados con gestión de capital y TSL/TP"
    )
    
    parser.add_argument(
        "--integration-only",
        action="store_true", 
        help="Ejecutar solo tests de integración del flujo completo de trading real"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar output detallado de los tests"
    )
    
    args = parser.parse_args()
    
    # Validar argumentos mutuamente excluyentes
    if args.unit_only and args.integration_only:
        print("Error: --unit-only y --integration-only son mutuamente excluyentes")
        return 1
    
    print("🚀 Ejecutando Tests de Historia 4.4: Gestión de Capital y TSL/TP para Operaciones Reales")
    print("=" * 90)
    
    total_exit_code = 0
    
    if args.unit_only:
        print("\n📋 EJECUTANDO TESTS UNITARIOS")
        print("-" * 50)
        
        # Tests unitarios existentes de TradingEngineService
        print("\n1️⃣ Tests unitarios existentes de TradingEngineService (TSL/TP)")
        exit_code = run_tests("tests/unit/services/test_trading_engine_service.py", args.verbose)
        if exit_code != 0:
            total_exit_code = exit_code
        
        # Tests unitarios específicos de gestión de capital
        print("\n2️⃣ Tests unitarios específicos de gestión de capital")
        exit_code = run_tests("tests/unit/services/test_trading_engine_capital_management.py", args.verbose)
        if exit_code != 0:
            total_exit_code = exit_code
            
    elif args.integration_only:
        print("\n🔗 EJECUTANDO TESTS DE INTEGRACIÓN")
        print("-" * 50)
        
        # Tests de integración del flujo completo
        print("\n3️⃣ Tests de integración del flujo completo de trading real")
        exit_code = run_tests("tests/integration/api/v1/test_real_trading_flow.py", args.verbose)
        if exit_code != 0:
            total_exit_code = exit_code
            
    else:
        # Ejecutar todos los tests relacionados con la historia 4.4
        print("\n📋 EJECUTANDO TODOS LOS TESTS DE LA HISTORIA 4.4")
        print("-" * 50)
        
        test_files = [
            ("Tests unitarios de TradingEngineService (TSL/TP)", "tests/unit/services/test_trading_engine_service.py"),
            ("Tests unitarios de gestión de capital", "tests/unit/services/test_trading_engine_capital_management.py"),
            ("Tests de integración del flujo completo", "tests/integration/api/v1/test_real_trading_flow.py")
        ]
        
        for i, (description, test_file) in enumerate(test_files, 1):
            print(f"\n{i}️⃣ {description}")
            exit_code = run_tests(test_file, args.verbose)
            if exit_code != 0:
                total_exit_code = exit_code
    
    # Resumen final
    print("\n" + "=" * 90)
    if total_exit_code == 0:
        print("✅ TODOS LOS TESTS DE LA HISTORIA 4.4 PASARON EXITOSAMENTE")
        print("\n🎯 Funcionalidades verificadas:")
        print("   • Gestión de capital con límites diarios y por operación")
        print("   • Cálculo correcto de tamaños de posición")
        print("   • Reinicio automático de contadores diarios")
        print("   • Lógica de TSL/TP para operaciones reales")
        print("   • Monitoreo de órdenes OCO en Binance")
        print("   • Flujo completo end-to-end de trading real")
        print("   • Manejo de casos edge y condiciones límite")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print(f"   Código de salida: {total_exit_code}")
        print("\n🔍 Revise el output anterior para detalles de los fallos")
    
    print("\n📚 Para más información sobre la Historia 4.4:")
    print("   docs/stories/4.4.story.md")
    
    return total_exit_code


if __name__ == "__main__":
    sys.exit(main())
