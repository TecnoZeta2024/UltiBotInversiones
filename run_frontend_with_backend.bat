@echo off
chcp 65001 > nul

set "PYTHON_EXE=.venv\Scripts\python.exe"
set "UVICORN_EXE=.venv\Scripts\uvicorn.exe"
set "BACKEND_MAIN=src.ultibot_backend.main:app"
set "FRONTEND_SCRIPT=src/ultibot_ui/main.py"
set "LOG_DIR=logs"
set "FRONTEND_LOG_STDOUT=%LOG_DIR%/frontend_stdout.log"
set "FRONTEND_LOG_STDERR=%LOG_DIR%/frontend_stderr.log"

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

REM --- Lanzamiento del Frontend con redirección de errores ---
echo Lanzando el frontend...
start "UltiBot Frontend" cmd /c "%PYTHON_EXE% %FRONTEND_SCRIPT% > %FRONTEND_LOG_STDOUT% 2> %FRONTEND_LOG_STDERR%"

echo.
echo UltiBotInversiones: Backend y Frontend lanzados en ventanas separadas.
echo Cierra estas ventanas para detener los servicios.

pause
