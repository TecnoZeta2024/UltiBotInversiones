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

echo Lanzando el backend con el método de módulo de Python...
rem --- CORRECCIÓN ARQUITECTÓNICA: Lanzar como un módulo para resolver imports ---
start "UltiBot Backend" cmd /c "poetry run python -m src.ultibot_backend"

echo Dando 10 segundos al backend para que se inicie...
timeout /t 10 /nobreak > nul

echo Lanzando el frontend con el método de módulo de Python...
rem --- CORRECCIÓN ARQUITECTÓNICA: Lanzar como un módulo para consistencia y resolución de imports ---
start "UltiBot Frontend" cmd /k "poetry run python -m src.ultibot_ui.main || (echo ERROR: El frontend ha fallado. Presiona cualquier tecla para cerrar esta ventana... && pause)"

echo.
echo UltiBotInversiones: Backend y Frontend lanzados en ventanas separadas.
echo Cierra estas ventanas para detener los servicios.
pause
