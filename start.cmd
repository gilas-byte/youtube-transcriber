@echo off
REM Double-click this file to start YouTube Transcripter and open it.
cd /d "%~dp0"

echo Starting YouTube Transcripter...
echo.

docker compose up -d
if errorlevel 1 (
    echo.
    echo ============================================================
    echo  Could not start.
    echo  Make sure Docker Desktop is installed AND running,
    echo  then try again.
    echo ============================================================
    echo.
    pause
    exit /b 1
)

echo.
echo Waiting for the app to come up...
timeout /t 6 /nobreak >nul

start "" http://localhost:8501

echo.
echo Running at http://localhost:8501
echo To stop it later:  docker compose down
echo.
timeout /t 4 /nobreak >nul
