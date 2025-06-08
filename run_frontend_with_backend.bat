@echo off
chcp 65001 > nul

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

echo Lanzando el backend con Uvicorn...
start "UltiBot Backend" cmd /c "poetry run uvicorn src.ultibot_backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo Dando 25 segundos al backend para que se inicie...
timeout /t 25 /nobreak > nul

echo Lanzando el frontend...
start "UltiBot Frontend" cmd /c "poetry run python src/ultibot_ui/main.py"

echo.
echo UltiBotInversiones: Backend y Frontend lanzados en ventanas separadas.
echo Cierra estas ventanas para detener los servicios.
pause
