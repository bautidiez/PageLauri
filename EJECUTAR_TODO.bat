@echo off
echo ========================================
echo   INICIANDO PROYECTO COMPLETO
echo   EL VESTUARIO
echo ========================================
echo.
echo Este script abrira dos ventanas:
echo 1. Backend (Flask) en http://localhost:5000
echo 2. Frontend (Angular) en http://localhost:4200
echo.
echo Presiona cualquier tecla para continuar...
pause >nul

echo.
echo [1/2] Iniciando Backend...
start "Backend - El Vestuario" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python app.py"

timeout /t 3 /nobreak >nul

echo [2/2] Iniciando Frontend...
start "Frontend - El Vestuario" cmd /k "cd /d %~dp0frontend && call npm start"

echo.
echo ========================================
echo   AMBOS SERVIDORES INICIADOS
echo ========================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:4200
echo Admin:    http://localhost:4200/admin/login
echo.
echo Cierra las ventanas para detener los servidores
echo.
pause
