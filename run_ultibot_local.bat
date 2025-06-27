@echo off
chcp 65001 > nul

echo "======================================================"
echo "  Configurando el entorno para UltiBotInversiones"
echo "======================================================"

REM Establece la URL donde el backend estara escuchando
set BACKEND_URL=http://localhost:8000
set BACKEND_LOG_FILE=logs/backend.log
set FRONTEND_LOG_FILE=logs/frontend.log
set DATABASE_URL=sqlite+aiosqlite:///ultibot_local.db

echo "URL del Backend establecida en: %BACKEND_URL%"
echo "El log del Backend se guardara en: %BACKEND_LOG_FILE%"
echo "El log del Frontend se guardara en: %FRONTEND_LOG_FILE%"
echo ""

REM Crear el directorio de logs si no existe
if not exist logs\ (
    mkdir logs
    echo "Directorio 'logs' creado."
)

REM Crear archivos de log vacios para prevenir race conditions
type nul > logs\backend.log
type nul > logs\frontend.log
echo "Archivos de log 'backend.log' y 'frontend.log' asegurados."

echo ""
echo "Iniciando la aplicacion del Backend..."
echo "======================================================"
REM Inicia el backend en segundo plano. El logging es manejado por la aplicacion.
start "UltiBot Backend" cmd /k "poetry run python src\ultibot_backend\main.py"

echo "Backend iniciado. Revisa %BACKEND_LOG_FILE% para ver los detalles."
echo ""
echo "Esperando 10 segundos antes de iniciar el Frontend..."
timeout /t 10 /nobreak

echo ""
echo "Iniciando la aplicacion de la Interfaz de Usuario (Frontend)..."
echo "======================================================"
REM Inicia el frontend en segundo plano. El logging es manejado por la aplicacion.
start "UltiBot Frontend" cmd /k "poetry run python src\ultibot_ui\main.py"

echo "Frontend iniciado. Revisa %FRONTEND_LOG_FILE% para ver los detalles."
echo ""
echo "Ambas aplicaciones estan corriendo en segundo plano."
echo "Para detenerlas, cierra las ventanas de la consola o usa el Administrador de Tareas."
echo "Presiona cualquier tecla para salir de este script..."
pause

REM Opcional: Para detener los procesos al cerrar esta ventana de script, puedes usar taskkill.
REM Sin embargo, 'start' abre nuevas ventanas, por lo que es mejor cerrarlas manualmente.
REM taskkill /IM python.exe /F
