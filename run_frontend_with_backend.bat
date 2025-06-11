@echo off
echo Lanzando el orquestador de la aplicacion...
poetry run python scripts/launch_app.py
echo.
echo El script de lanzamiento ha finalizado. Si la aplicacion no se inicio, revise la salida anterior.
pause
