@echo off
echo ========================================
echo   INICIANDO BACKEND - EL VESTUARIO
echo ========================================
echo.

cd backend

echo [1/4] Activando entorno virtual...
call venv\Scripts\activate.bat

echo [2/4] Verificando dependencias...
pip install -r requirements.txt --quiet


echo [3/4] (Paso de migraciones omitido - scripts de limpieza ejecutados)

echo [4/4] Iniciando servidor Flask...
echo.
echo ========================================
echo   Servidor corriendo en: http://localhost:5000
echo   Presiona Ctrl+C para detener
echo ========================================
echo.

python run.py

pause
