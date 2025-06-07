@echo off
REM Script para lanzar el backend y el frontend de UltiBotInversiones en Windows

REM 0. Limpiar __pycache__ para asegurar que se usa el código más reciente
echo Limpiando directorios __pycache__...
powershell -Command "Get-ChildItem -Path src -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
echo Limpieza de __pycache__ completada.

REM 1. Lanzar el backend con Uvicorn y redirigir su salida a un archivo de log
echo Lanzando el backend con Uvicorn y capturando su salida en logs/backend_stdout.log...
REM Se usa cmd /c para asegurar que la salida se redirige correctamente.
start "UltiBot Backend" cmd /c "poetry run uvicorn src.ultibot_backend.main:app --host 0.0.0.0 --port 8000 > logs/backend_stdout.log 2>&1"

REM 2. Pausa extendida para dar tiempo al backend a inicializarse completamente.
echo Dando 15 segundos al backend para que se inicie...
ping 127.0.0.1 -n 16 > nul

REM 3. Lanzar el frontend
echo Lanzando el frontend...
start "UltiBot Frontend" cmd /k "poetry run python -m src.ultibot_ui.main & PAUSE"

REM 4. Mensaje final
@echo UltiBotInversiones: Backend y Frontend lanzados en ventanas separadas.
@echo Cierra estas ventanas para detener los servicios.
