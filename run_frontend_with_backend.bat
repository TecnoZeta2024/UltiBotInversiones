@echo off
chcp 65001 > nul

echo.
echo =================================================================
echo ==         AVISO IMPORTANTE: SCRIPT OBSOLETO                   ==
echo =================================================================
echo.
echo Este script 'run_frontend_with_backend.bat' esta obsoleto.
echo Ya no debe usarse para lanzar el entorno de desarrollo o produccion.
echo.
echo =================================================================
echo ==         NUEVO METODO DE LANZAMIENTO                         ==
echo =================================================================
echo.
echo Para lanzar el entorno completo (Backend y Frontend) de UltiBot,
echo por favor use Docker Compose desde la raiz del proyecto:
echo.
echo   docker-compose up --build -d
echo.
echo Para detener los servicios:
echo.
echo   docker-compose down
echo.
echo =================================================================
echo.
echo Este mensaje se cerrara en 20 segundos.
TIMEOUT /T 20
