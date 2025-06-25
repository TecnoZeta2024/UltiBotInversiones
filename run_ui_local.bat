@echo off
chcp 65001 > nul

echo "======================================================"
echo "  Configurando el entorno para la UI local"
echo "======================================================"

REM Establece la URL donde el backend estara escuchando
set BACKEND_URL=http://localhost:8000
set LOG_FILE=logs/ui_local_run.log

echo "URL del Backend establecida en: %BACKEND_URL%"
echo "El log de esta ejecucion se guardara en: %LOG_FILE%"
echo ""

REM Crear el directorio de logs si no existe
if not exist logs\ (
    mkdir logs
    echo "Directorio 'logs' creado."
)

echo ""
echo "Iniciando la aplicacion de la Interfaz de Usuario..."
echo "======================================================"

REM Ejecuta la aplicacion de la UI usando poetry y redirige toda la salida al archivo de log
poetry run python -m src.ultibot_ui.main > %LOG_FILE% 2>&1

echo "La aplicacion de la UI ha finalizado. Revisa %LOG_FILE% para ver los detalles."
pause
