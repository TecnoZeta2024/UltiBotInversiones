@echo off
REM Script para lanzar el backend y el frontend de UltiBotInversiones en Windows

REM 0. Limpiar __pycache__ para asegurar que se usa el código más reciente
echo Limpiando directorios __pycache__...
powershell -Command "Get-ChildItem -Path src -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
echo Limpieza de __pycache__ completada.

REM 1. Lanzar el backend (ajusta el path/comando según tu backend)
start "UltiBot Backend" poetry run python run_backend.py

REM 2. Esperar a que el backend esté listo (bucle de verificación de salud)
echo Esperando a que el backend inicie en http://127.0.0.1:8000...
:wait_for_backend
    powershell -Command "try { Invoke-WebRequest -Uri http://127.0.0.1:8000/health -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }"
    if %errorlevel% equ 0 (
        echo Backend listo.
    ) else (
        echo Backend no disponible, reintentando en 2 segundos...
        ping 127.0.0.1 -n 3 > nul
        goto wait_for_backend
    )

REM 3. Lanzar el frontend
start "UltiBot Frontend" cmd /k "poetry run python -m src.ultibot_ui.main"

REM 4. Mensaje final
@echo UltiBotInversiones: Backend y Frontend lanzados en ventanas separadas.
@echo Cierra estas ventanas para detener los servicios.
