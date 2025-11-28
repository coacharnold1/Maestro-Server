# Maestro MPD Control - Auto-start Setup
# Creates startup script and shortcut for Docker containers

$ErrorActionPreference = "Stop"

Write-Host "Setting up Maestro auto-start..." -ForegroundColor Cyan

# Create batch script
$scriptPath = Join-Path $PSScriptRoot "start-maestro.bat"
$projectPath = $PSScriptRoot

$batchContent = @"
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
"@

Set-Content -Path $scriptPath -Value $batchContent -Encoding ASCII
Write-Host "Created: $scriptPath" -ForegroundColor Green

# Create startup shortcut
$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder "Maestro.lnk"

try {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $scriptPath
    $shortcut.WorkingDirectory = $projectPath
    $shortcut.WindowStyle = 7  # Minimized
    $shortcut.Description = "Start Maestro MPD Control containers"
    $shortcut.Save()
    
    Write-Host "Created shortcut: $shortcutPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "Auto-start configured successfully!" -ForegroundColor Green
    Write-Host "Containers will start automatically on Windows login" -ForegroundColor Green
}
catch {
    Write-Host "Could not create startup shortcut: $_" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Manual setup:" -ForegroundColor Cyan
    Write-Host "1. Press Win+R" -ForegroundColor White
    Write-Host "2. Type: shell:startup" -ForegroundColor White
    Write-Host "3. Create shortcut to: $scriptPath" -ForegroundColor White
}
