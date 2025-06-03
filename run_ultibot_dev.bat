@echo off
REM ============================================================================
REM UltiBot Development Quick Start Script
REM Descripción: Script minimalista para desarrollo rápido
REM Uso: Para desarrollo cuando ya sabes que todo está configurado
REM ============================================================================

echo 🚀 UltiBot Quick Dev Start...

REM Lanzar backend con Poetry
start "Backend" cmd /k "poetry run uvicorn src.ultibot_backend.main:app --reload"

REM Esperar 2 segundos
timeout /t 2 /nobreak >nul

REM Lanzar frontend con Poetry (como módulo para evitar errores de importación relativa)
start "Frontend" cmd /k "poetry run python -m src.ultibot_ui.main"

echo ✅ UltiBot iniciado en modo desarrollo
echo Backend: http://127.0.0.1:8000
echo Frontend: PyQt5 UI
pause