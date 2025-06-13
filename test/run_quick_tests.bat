@echo off
echo ========================================
echo EJECUTANDO PRUEBAS RAPIDAS DE ULTIBOT
echo ========================================

echo.
echo [1/5] Probando componentes del backend...
python test\test_backend_components.py
if %errorlevel% neq 0 (
    echo ❌ Pruebas del backend fallaron
    pause
    exit /b 1
)

echo.
echo [2/5] Probando componentes del frontend...
python test\test_frontend_components.py
if %errorlevel% neq 0 (
    echo ❌ Pruebas del frontend fallaron
    pause
    exit /b 1
)

echo.
echo [3/5] Probando conexion a base de datos...
python test\test_database_connection.py
if %errorlevel% neq 0 (
    echo ❌ Pruebas de base de datos fallaron
    pause
    exit /b 1
)

echo.
echo [4/5] Probando endpoints de API...
python test\test_api_endpoints.py
if %errorlevel% neq 0 (
    echo ❌ Pruebas de API fallaron
    pause
    exit /b 1
)

echo.
echo [5/5] Ejecutando suite completa de pruebas...
python test\run_all_tests.py
if %errorlevel% neq 0 (
    echo ❌ Suite completa de pruebas falló
    pause
    exit /b 1
)

echo.
echo ========================================
echo 🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE
echo ========================================
pause
