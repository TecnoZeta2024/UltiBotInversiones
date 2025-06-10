@echo off
echo Creando directorio de logs si no existe...
if not exist "logs" mkdir "logs"

echo Limpiando logs anteriores...
if exist "logs\backend.log" del "logs\backend.log"
if exist "logs\frontend.log" del "logs\frontend.log"
if exist "logs\frontend1.log" del "logs\frontend1.log"

echo Intentando detener cualquier proceso anterior en el puerto 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /F /PID %%a
)
echo Procesos anteriores (si los habia) detenidos.

echo Limpiando directorios __pycache__...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d"
    )
)
echo Limpieza de __pycache__ completada.

echo Lanzando el backend...
start "Backend" cmd /c "poetry run uvicorn src.ultibot_backend.main:app --host 0.0.0.0 --port 8000 --reload > logs\backend.log 2>&1"

echo Dando 10 segundos al backend para que se inicie...
timeout /t 10 /nobreak

echo Lanzando el frontend...
start "Frontend" cmd /c "poetry run python src/ultibot_ui/main.py"

echo.
echo UltiBotInversiones: Backend y Frontend lanzados.
echo Monitorea los archivos en la carpeta 'logs' para ver la salida.
echo Cierra las ventanas de los procesos para detener los servicios.

pause
