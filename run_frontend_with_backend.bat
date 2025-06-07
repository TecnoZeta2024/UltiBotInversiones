@echo off
chcp 65001 > nul

set "PYTHON_EXE=poetry run python"
set "UVICORN_EXE=poetry run uvicorn"
set "BACKEND_MAIN=src.ultibot_backend.main:app"
set "FRONTEND_MAIN=src.ultibot_ui.main"
set "LOG_DIR=logs"
set "BACKEND_LOG_STDOUT=%LOG_DIR%/backend_stdout.log"
set "FRONTEND_LOG=%LOG_DIR%/frontend.log"

REM --- Limpieza y Preparación ---
echo Intentando detener cualquier proceso anterior en el puerto 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000"') do (
    taskkill /F /PID %%a 2>nul
)
echo Procesos anteriores (si los habia) detenidos.

echo Limpiando directorios __pycache__...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        rd /s /q "%%d"
    )
)
echo Limpieza de __pycache__ completada.

REM --- Lanzamiento del Backend ---
echo Lanzando el backend con Uvicorn...
start "UltiBot Backend" cmd /c "%UVICORN_EXE% %BACKEND_MAIN% --host 0.0.0.0 --port 8000 --reload"

echo Dando 15 segundos al backend para que se inicie...
timeout /t 15 /nobreak > nul

REM --- Lanzamiento del Frontend ---
echo Lanzando el frontend...
start "UltiBot Frontend" cmd /c "%PYTHON_EXE% -m %FRONTEND_MAIN%"

echo.
echo UltiBotInversiones: Backend y Frontend lanzados en ventanas separadas.
echo Cierra estas ventanas para detener los servicios.

pause
