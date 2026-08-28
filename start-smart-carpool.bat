@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo O ambiente do Smart Carpool ainda nao foi configurado.
    echo Consulte o README.md para instalar as dependencias.
    pause
    exit /b 1
)

echo Iniciando o Smart Carpool...
echo Para encerrar, feche esta janela.

".venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 (
    echo.
    echo Nao foi possivel preparar o banco de dados.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m app.seed
if errorlevel 1 (
    echo.
    echo Nao foi possivel preparar os dados de demonstracao.
    pause
    exit /b 1
)

start "" powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000'"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

if errorlevel 1 (
    echo.
    echo Nao foi possivel iniciar o Smart Carpool.
    pause
)

endlocal
