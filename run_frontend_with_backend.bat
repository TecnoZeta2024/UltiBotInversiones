@echo off
chcp 65001 > nul

echo.
echo =================================================================
echo ==         LANZADOR DEL ENTORNO DE DESARROLLO ULTIBOT          ==
echo =================================================================
echo.
echo Este script lanzara automaticamente el BACKEND y el FRONTEND
echo en ventanas de terminal separadas.
echo.
echo 1. Se abrira una ventana para los logs del BACKEND.
echo 2. Tras una breve pausa, se abrira una para el FRONTEND.
echo.
echo Para detener la aplicacion, simplemente cierra ambas ventanas.
echo =================================================================
echo.

echo Limpiando directorios __pycache__...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        rd /s /q "%%d"
    )
)
echo Limpieza de __pycache__ completada.
echo.

echo Lanzando el backend en una nueva ventana...
START "UltiBot Backend" cmd /c "poetry run uvicorn src.ultibot_backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo Esperando 5 segundos para que el backend se inicialice...
TIMEOUT /T 5 /NOBREAK > nul
echo.

echo Lanzando el frontend en una nueva ventana...
START "UltiBot Frontend" cmd /c "poetry run python src/ultibot_ui/main.py"

echo.
echo Entorno de desarrollo lanzado.
echo Esta ventana se cerrara en 10 segundos.
TIMEOUT /T 10
