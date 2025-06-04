@echo off
REM Script para lanzar el backend y el frontend de UltiBotInversiones en Windows

REM 1. Lanzar el backend (ajusta el path/comando según tu backend)
start "UltiBot Backend" cmd /k "poetry run uvicorn src.ultibot_backend.main:app --reload --host 0.0.0.0 --port 8000"

REM 2. Esperar unos segundos para asegurar que el backend arranca
ping 127.0.0.1 -n 5 > nul

REM 3. Lanzar el frontend
start "UltiBot Frontend" cmd /k "poetry run python -m src.ultibot_ui.main"

REM 4. Mensaje final
@echo UltiBotInversiones: Backend y Frontend lanzados en ventanas separadas.
@echo Cierra estas ventanas para detener los servicios.
