@echo off
REM Maestro MPD Control - Auto-start script
REM Waits for Docker Desktop to be ready, then starts containers

echo Starting Maestro MPD Control...

REM Wait for Docker to be ready (30 seconds)
timeout /t 30 /nobreak >nul

REM Change to script's directory (portable)
cd /d "%~dp0"

REM Start containers
docker-compose -f docker-compose.native-mpd.yml up -d

echo Maestro containers started!
