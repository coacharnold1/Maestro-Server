@echo off
REM Maestro MPD Control - Cleanup Script
REM Stops all Maestro containers and cleans up conflicts

echo ================================
echo   Maestro Cleanup Script
echo ================================
echo.

echo Stopping all Maestro containers...

REM Stop all possible container configurations
echo Stopping native MPD setup containers...
docker-compose -f docker-compose.native-mpd.yml down 2>nul

echo Stopping Windows containerized setup...
docker-compose -f docker-compose.windows.yml down 2>nul

echo Stopping Linux/default setup...
docker-compose -f docker-compose.yml down 2>nul

echo.
echo Checking for running MPD containers...
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | findstr mpd

echo.
echo Cleanup completed!
echo.
echo To restart Maestro:
echo - For native MPD: docker-compose -f docker-compose.native-mpd.yml up -d
echo - For containerized: docker-compose -f docker-compose.windows.yml --profile with-mpd up -d
echo.
pause