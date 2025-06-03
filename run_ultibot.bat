@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM UltiBot Deployment Script - Versión Mejorada y Compatible Windows
REM Descripción: Lanza Backend (FastAPI) y Frontend (PyQt5) en ventanas separadas
REM ============================================================================

echo ========================================
echo UltiBot Deployment Script
echo ========================================
echo.

REM Verificar que estamos en el directorio correcto del proyecto
if not exist "pyproject.toml" (
    echo ERROR: No se encontro pyproject.toml
    echo Ejecuta este script desde la raiz del proyecto UltiBotInversiones
    echo Directorio actual: %CD%
    pause
    exit /b 1
)

if not exist "src\ultibot_backend\main.py" (
    echo ERROR: No se encontro el backend en src\ultibot_backend\main.py
    pause
    exit /b 1
)

if not exist "src\ultibot_ui\main.py" (
    echo ERROR: No se encontro el frontend en src\ultibot_ui\main.py
    pause
    exit /b 1
)

echo Proyecto verificado correctamente.
echo.

REM Verificar que Poetry esta instalado
poetry --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Poetry no esta instalado o no esta en el PATH
    echo Instala Poetry desde: https://python-poetry.org/docs/#installation
    pause
    exit /b 1
)

echo Poetry encontrado:
poetry --version

echo.
REM Verificar dependencias
poetry check >nul 2>&1
if errorlevel 1 (
    echo ADVERTENCIA: Problemas detectados con dependencias. Ejecutando poetry install...
    poetry install
    if errorlevel 1 (
        echo ERROR: Fallo la instalacion de dependencias
        pause
        exit /b 1
    )
) else (
    echo Dependencias verificadas correctamente.
)
echo.

REM Verificar entorno virtual
poetry env info --path >nul 2>&1
if errorlevel 1 (
    echo ERROR: No se pudo acceder al entorno virtual de Poetry
    echo Ejecuta: poetry install
    pause
    exit /b 1
)

echo Entorno virtual de Poetry disponible.
echo.

echo Iniciando UltiBot...
echo.

REM Crear directorio para logs si no existe
if not exist "logs" mkdir logs

REM Lanzar backend (FastAPI/Uvicorn) usando Poetry
REM Redireccionar salida a logs/backend.log y mantener ventana abierta
start "UltiBot Backend" cmd /k "poetry run uvicorn src.ultibot_backend.main:app --reload --host 127.0.0.1 --port 8000 > logs\backend.log 2>&1"

REM Esperar un momento para que el backend inicie
timeout /t 3 /nobreak >nul

REM Lanzar frontend (PyQt5 UI) usando Poetry
REM Ejecutar como módulo para evitar errores de import relativo
start "UltiBot UI" cmd /k "poetry run python -m src.ultibot_ui.main"

echo.
echo UltiBot iniciado exitosamente!
echo.
echo Estado de los servicios:
echo    - Backend: http://127.0.0.1:8000
echo    - Frontend: Ventana PyQt5 independiente
echo    - Logs: Disponibles en la carpeta 'logs'
echo.
echo Comandos utiles:
echo    - Backend API Docs: http://127.0.0.1:8000/docs
echo    - Health Check: http://127.0.0.1:8000/health
echo.
echo Para detener los servicios, cierra las ventanas correspondientes
echo    o presiona Ctrl+C en cada terminal
pause