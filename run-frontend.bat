@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM UltiBot Frontend Runner - Para uso con backend containerizado
REM ============================================================================

echo ========================================
echo UltiBot Frontend Runner
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

echo Iniciando UltiBot Frontend...
echo.

REM Crear directorio para logs si no existe
if not exist "logs" mkdir logs

REM Lanzar frontend (PyQt5 UI) usando Poetry
poetry run python -m src.ultibot_ui.main > logs\frontend.log 2>&1

echo.
echo UltiBot Frontend finalizado.
echo.
pause

