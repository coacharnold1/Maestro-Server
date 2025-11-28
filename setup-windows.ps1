#Requires -Version 5.1
# Maestro MPD Control - Windows Setup Script
# Installs native Windows MPD and configures Docker web interface

param(
    [switch]$SkipMPD,
    [switch]$SkipDocker,
    [string]$MusicDirectory
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Message)
    Write-Host "`n================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "================================`n" -ForegroundColor Cyan
}

function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-ChocoPackage {
    param([string]$PackageName)
    
    if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-ColorOutput "Chocolatey not found. Please install it first:" Yellow
        Write-ColorOutput "Run as Administrator: Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" Yellow
        return $false
    }
    
    Write-ColorOutput "Installing $PackageName via Chocolatey..." Cyan
    choco install $PackageName -y
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    return $true
}

function New-MPDConfiguration {
    param(
        [string]$MusicPath,
        [string]$ConfigPath = "$env:APPDATA\mpd\mpd.conf"
    )
    
    # Create directories
    $dirs = @(
        "$env:APPDATA\mpd",
        "$env:APPDATA\mpd\data",
        "$env:APPDATA\mpd\playlists",
        "$env:APPDATA\mpd\logs"
    )
    
    foreach ($dir in $dirs) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    # Convert to forward slashes for MPD
    $musicDir = $MusicPath -replace '\\','/'
    $dataDir = "$env:APPDATA\mpd\data" -replace '\\','/'
    $playlistDir = "$env:APPDATA\mpd\playlists" -replace '\\','/'
    $logDir = "$env:APPDATA\mpd\logs" -replace '\\','/'
    
    # Create config content
    $config = @"
music_directory     "$musicDir"
db_file             "$dataDir/mpd.db"
state_file          "$dataDir/mpdstate"
sticker_file        "$dataDir/sticker.sql"
log_file            "$logDir/mpd.log"
playlist_directory  "$playlistDir"

bind_to_address     "127.0.0.1"
port                "6600"

audio_output {
    type        "wasapi"
    name        "Windows Audio"
    enabled     "yes"
}

audio_output {
    type        "httpd"
    name        "HTTP Stream"
    encoder     "lame"
    port        "8001"
    bitrate     "320"
    format      "44100:16:2"
    always_on   "yes"
    enabled     "yes"
}

auto_update             "yes"
filesystem_charset      "UTF-8"
"@
    
    # Write config
    Set-Content -Path $ConfigPath -Value $config -Encoding UTF8
    Write-ColorOutput "MPD configuration created at: $ConfigPath" Green
    return $ConfigPath
}

function Install-MPDService {
    if (!(Test-AdminPrivileges)) {
        Write-ColorOutput "Skipping service installation (requires Administrator)" Yellow
        Write-ColorOutput "MPD will need to be started manually" Yellow
        return $false
    }
    
    # Check for NSSM
    if (!(Get-Command nssm -ErrorAction SilentlyContinue)) {
        Write-ColorOutput "Installing NSSM (service manager)..." Cyan
        Install-ChocoPackage "nssm"
    }
    
    if (!(Get-Command nssm -ErrorAction SilentlyContinue)) {
        Write-ColorOutput "NSSM not available. Skipping service installation." Yellow
        return $false
    }
    
    # Find MPD executable
    $mpdPath = (Get-Command mpd -ErrorAction SilentlyContinue).Source
    if (!$mpdPath) {
        Write-ColorOutput "MPD executable not found in PATH" Red
        return $false
    }
    
    $configPath = "$env:APPDATA\mpd\mpd.conf"
    
    # Check if service exists
    $service = Get-Service -Name "MPD" -ErrorAction SilentlyContinue
    if ($service) {
        Write-ColorOutput "MPD service already exists. Removing old service..." Yellow
        nssm stop MPD
        nssm remove MPD confirm
        Start-Sleep -Seconds 2
    }
    
    # Install service
    Write-ColorOutput "Installing MPD as Windows service..." Cyan
    nssm install MPD "$mpdPath" "--no-daemon `"$configPath`""
    nssm set MPD DisplayName "Music Player Daemon"
    nssm set MPD Description "MPD server for Maestro Control"
    nssm set MPD Start SERVICE_AUTO_START
    
    # Start service
    nssm start MPD
    Start-Sleep -Seconds 3
    
    $service = Get-Service -Name "MPD" -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq "Running") {
        Write-ColorOutput "MPD service installed and started successfully" Green
        return $true
    }
    else {
        Write-ColorOutput "Service installation completed but status unknown" Yellow
        return $false
    }
}

function New-SetupConfiguration {
    param(
        [string]$SetupType,
        [string]$MusicDirectory
    )
    
    $configPath = Join-Path $PSScriptRoot "maestro-setup.conf"
    $configContent = @"
# Maestro Setup Configuration
# This file tracks your setup choices for auto-start scripts
# Created by setup-windows.ps1 on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

SETUP_TYPE=$SetupType
# Options: native, containerized, external
# native = Windows native MPD + Docker web interface  
# containerized = Full Docker stack (MPD + web)
# external = Docker web only, connects to external MPD

SETUP_DATE=$(Get-Date -Format "yyyy-MM-dd")
MUSIC_DIRECTORY=$MusicDirectory
AUTO_START=true
"@
    
    Set-Content -Path $configPath -Value $configContent -Encoding UTF8
    Write-ColorOutput "Setup configuration saved to: $configPath" Green
}

function New-DockerEnvironment {
    param(
        [string]$MusicPath,
        [bool]$UseNativeMPD = $true
    )
    
    $musicDir = $MusicPath -replace '\\','/'
    $secretKey = "maestro-windows-$(Get-Random)-$(Get-Date -Format 'yyyyMMddHHmmss')"
    
    $envContent = @"
# Maestro MPD Control - Windows Configuration
# Generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Music Library (Windows path with forward slashes)
MUSIC_DIRECTORY=$musicDir

# MPD Configuration $(if ($UseNativeMPD) { "(Native Windows MPD)" } else { "(Containerized)" })
MPD_HOST=$(if ($UseNativeMPD) { "host.docker.internal" } else { "mpd" })
MPD_PORT=6600
MPD_TIMEOUT=10

# Web Interface
WEB_PORT=5003
DEFAULT_THEME=dark

# Last.fm Integration (Optional)
LASTFM_API_KEY=
LASTFM_SHARED_SECRET=

# Auto-Fill Settings
AUTO_FILL_ENABLED=true
RECENT_MUSIC_DIRS=

# Security
SECRET_KEY=$secretKey
"@
    
    if (!$UseNativeMPD) {
        $envContent += "`nCOMPOSE_PROFILES=with-mpd"
    }
    
    Set-Content -Path ".env" -Value $envContent -Encoding UTF8
    Write-ColorOutput ".env file created" Green
}

function Start-DockerServices {
    param([bool]$UseNativeMPD)
    
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-ColorOutput "Docker not found. Please install Docker Desktop:" Red
        Write-ColorOutput "https://www.docker.com/products/docker-desktop/" Cyan
        return $false
    }
    
    try {
        docker ps | Out-Null
    }
    catch {
        Write-ColorOutput "Docker is not running. Please start Docker Desktop." Red
        return $false
    }
    
    Write-ColorOutput "Starting Docker containers..." Cyan
    
    try {
        if ($UseNativeMPD) {
            docker-compose -f docker-compose.native-mpd.yml up -d --build
        }
        else {
            docker-compose -f docker-compose.windows.yml --profile with-mpd up -d --build
        }
        Write-ColorOutput "Docker containers started successfully" Green
        
        # Create startup script for auto-start
        Write-ColorOutput "`nSetting up auto-start..." Cyan
        New-StartupScript -UseNativeMPD $UseNativeMPD
        
        return $true
    }
    catch {
        Write-ColorOutput "Failed to start Docker containers: $_" Red
        return $false
    }
}

function Test-Setup {
    param([bool]$UseNativeMPD)
    
    Write-Header "Testing Setup"
    
    $allGood = $true
    
    # Test MPD
    if ($UseNativeMPD) {
        Write-ColorOutput "Testing MPD connection..." Cyan
        $connection = Test-NetConnection -ComputerName localhost -Port 6600 -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($connection) {
            Write-ColorOutput "[OK] MPD is responding on port 6600" Green
        }
        else {
            Write-ColorOutput "[FAIL] MPD not responding on port 6600" Red
            $allGood = $false
        }
    }
    
    # Test Docker
    Write-ColorOutput "Testing Docker containers..." Cyan
    Start-Sleep -Seconds 3
    $containers = docker ps --format "{{.Names}}" 2>$null
    if ($containers -match "mpd-web-control") {
        Write-ColorOutput "[OK] Web container is running" Green
    }
    else {
        Write-ColorOutput "[FAIL] Web container not found" Red
        $allGood = $false
    }
    
    # Test web interface
    Write-ColorOutput "Testing web interface..." Cyan
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5003" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "[OK] Web interface is accessible" Green
        }
    }
    catch {
        Write-ColorOutput "[WARN] Web interface not responding yet (may need more time)" Yellow
    }
    
    return $allGood
}

function New-StartupScript {
    param([bool]$UseNativeMPD)
    
    $scriptPath = Join-Path $PSScriptRoot "start-maestro.bat"
    $psScriptPath = Join-Path $PSScriptRoot "start-maestro.ps1"
    $projectPath = $PSScriptRoot
    
    $composeFile = if ($UseNativeMPD) { "docker-compose.native-mpd.yml" } else { "docker-compose.windows.yml --profile with-mpd" }
    
    # Create PowerShell startup script (more reliable)
    $psContent = @"
# Maestro MPD Control - Smart Auto-start script
# Prevents conflicts between native and containerized MPD

Write-Host "Starting Maestro MPD Control..." -ForegroundColor Cyan

# Read setup configuration to determine what to start
`$configPath = "`$PSScriptRoot\maestro-setup.conf"
`$setupType = "native"  # default fallback

if (Test-Path `$configPath) {
    `$config = Get-Content `$configPath | ForEach-Object {
        if (`$_ -match "SETUP_TYPE=(.*)") {
            `$setupType = `$matches[1]
        }
    }
    Write-Host "Found setup configuration: `$setupType" -ForegroundColor Green
} else {
    Write-Host "No setup config found, assuming native MPD setup" -ForegroundColor Yellow
}

# Stop any existing containers to prevent conflicts
Write-Host "Cleaning up any existing Maestro containers..." -ForegroundColor Yellow
try {
    docker-compose -f docker-compose.yml down 2>`$null | Out-Null
    docker-compose -f docker-compose.windows.yml down 2>`$null | Out-Null  
    docker-compose -f docker-compose.native-mpd.yml down 2>`$null | Out-Null
    Write-Host "Cleanup completed" -ForegroundColor Green
} catch {
    Write-Host "Cleanup skipped (no containers running)" -ForegroundColor Gray
}

# Determine which compose file to use
`$composeFile = ""
switch (`$setupType) {
    "native" { 
        `$composeFile = "docker-compose.native-mpd.yml"
        Write-Host "Native MPD setup: Starting web interface only" -ForegroundColor Cyan
    }
    "containerized" { 
        `$composeFile = "docker-compose.windows.yml --profile with-mpd"
        Write-Host "Containerized setup: Starting MPD + web interface" -ForegroundColor Cyan
    }
    default { 
        `$composeFile = "docker-compose.native-mpd.yml"
        Write-Host "Unknown setup type, defaulting to native" -ForegroundColor Yellow
    }
}

Write-Host "Waiting for Docker Desktop to be ready..." -ForegroundColor Yellow

`$maxAttempts = 18  # 3 minutes
`$attempt = 0
`$dockerReady = `$false

while (`$attempt -lt `$maxAttempts -and -not `$dockerReady) {
    `$attempt++
    Write-Host "Attempt `$attempt/`$maxAttempts: Checking Docker status..." -ForegroundColor Gray
    
    try {
        docker ps | Out-Null
        `$dockerReady = `$true
        Write-Host "Docker Desktop is ready!" -ForegroundColor Green
    }
    catch {
        if (`$attempt -ge `$maxAttempts) {
            Write-Host "ERROR: Docker Desktop did not start within 3 minutes" -ForegroundColor Red
            Write-Host "Please start Docker Desktop manually and run start-maestro.ps1 again" -ForegroundColor Yellow
            Read-Host "Press Enter to exit"
            exit 1
        }
        Start-Sleep -Seconds 10
    }
}

if (`$dockerReady) {
    Write-Host "Changing to project directory..." -ForegroundColor Cyan
    Set-Location "$projectPath"
    
    Write-Host "Starting containers with: `$composeFile" -ForegroundColor Cyan
    try {
        Invoke-Expression "docker-compose -f `$composeFile up -d"
        Write-Host "SUCCESS: Maestro containers started successfully!" -ForegroundColor Green
        Write-Host "Web interface should be available at http://localhost:5003" -ForegroundColor Cyan
        
        if (`$setupType -eq "native") {
            Write-Host "Native Windows MPD should also be running for audio playback" -ForegroundColor Cyan
            # Check if native MPD is running
            `$mpdService = Get-Service "MPD" -ErrorAction SilentlyContinue
            if (`$mpdService -and `$mpdService.Status -eq "Running") {
                Write-Host "✓ Native MPD service is running" -ForegroundColor Green
            } else {
                Write-Host "⚠ Native MPD service not detected - you may need to start it manually" -ForegroundColor Yellow
            }
        }
    }
    catch {
        Write-Host "ERROR: Failed to start containers" -ForegroundColor Red
        Write-Host "Try running the command manually: docker-compose -f `$composeFile up -d" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
    }
}

Write-Host "Auto-start script completed." -ForegroundColor Cyan
"@
    
    Set-Content -Path $psScriptPath -Value $psContent -Encoding UTF8
    Set-Content -Path $scriptPath -Value $batchContent -Encoding ASCII
    
    Write-ColorOutput "PowerShell startup script created at: $psScriptPath" Green
    Write-ColorOutput "Batch wrapper script created at: $scriptPath" Green
    
    # Create batch file wrapper (for compatibility)
    $batchContent = @"
@echo off
REM Maestro MPD Control - Auto-start script wrapper
REM This batch file launches the PowerShell script

echo Starting Maestro MPD Control...
echo Launching PowerShell startup script...

REM Run the PowerShell script with execution policy bypass
powershell.exe -ExecutionPolicy Bypass -WindowStyle Normal -File "$psScriptPath"

if %ERRORLEVEL% NEQ 0 (
    echo PowerShell script failed, falling back to basic batch startup...
    echo Waiting 60 seconds for Docker...
    timeout /t 60 /nobreak >nul
    
    cd /d "$projectPath"
    docker-compose -f $composeFile up -d
    if %ERRORLEVEL% EQU 0 (
        echo Containers started successfully!
    ) else (
        echo Failed to start containers
        pause
    )
)
"@
    
    Set-Content -Path $scriptPath -Value $batchContent -Encoding ASCII
    Write-ColorOutput "Startup script created at: $scriptPath" Green
    
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
        
        Write-ColorOutput "Auto-start shortcut created in Startup folder" Green
        Write-ColorOutput "Containers will start automatically on Windows login" Green
    }
    catch {
        Write-ColorOutput "Could not create startup shortcut: $_" Yellow
        Write-ColorOutput "You can manually add start-maestro.bat to Startup folder" Yellow
    }
}

function Show-Summary {
    param([bool]$UseNativeMPD)
    
    Write-Host "`n`n"
    Write-Host "================================" -ForegroundColor Green
    Write-Host "  Setup Complete!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Web Interface:" -ForegroundColor Cyan
    Write-Host "  http://localhost:5003" -ForegroundColor White
    Write-Host ""
    
    if ($UseNativeMPD) {
        Write-Host "Audio Output:" -ForegroundColor Cyan
        Write-Host "  Native Windows audio (WASAPI)" -ForegroundColor Green
        Write-Host "  Music plays through your speakers!" -ForegroundColor Green
        Write-Host ""
        Write-Host "MPD Service:" -ForegroundColor Cyan
        Write-Host "  Check status:  Get-Service MPD" -ForegroundColor White
        Write-Host "  Restart:       Restart-Service MPD" -ForegroundColor White
        Write-Host "  Stop:          Stop-Service MPD" -ForegroundColor White
    }
    else {
        Write-Host "Audio Output:" -ForegroundColor Cyan
        Write-Host "  HTTP Stream: http://localhost:8001" -ForegroundColor White
        Write-Host "  (Open in VLC or browser)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Auto-Start:" -ForegroundColor Cyan
    Write-Host "  MPD starts automatically (Windows service)" -ForegroundColor Green
    Write-Host "  Docker containers start on login" -ForegroundColor Green
    Write-Host ""
    Write-Host "Docker Management:" -ForegroundColor Cyan
    if ($UseNativeMPD) {
        Write-Host "  View logs:  docker-compose -f docker-compose.native-mpd.yml logs -f" -ForegroundColor White
        Write-Host "  Restart:    docker-compose -f docker-compose.native-mpd.yml restart" -ForegroundColor White
        Write-Host "  Stop:       docker-compose -f docker-compose.native-mpd.yml down" -ForegroundColor White
    }
    else {
        Write-Host "  View logs:  docker-compose -f docker-compose.windows.yml logs -f" -ForegroundColor White
        Write-Host "  Restart:    docker-compose -f docker-compose.windows.yml restart" -ForegroundColor White
        Write-Host "  Stop:       docker-compose -f docker-compose.windows.yml down" -ForegroundColor White
    }
    Write-Host ""
}

#############################################################################
# MAIN EXECUTION
#############################################################################

Clear-Host
Write-Host ""
Write-Host "================================" -ForegroundColor Magenta
Write-Host "  Maestro MPD Control" -ForegroundColor Magenta
Write-Host "  Windows Setup" -ForegroundColor Magenta
Write-Host "================================" -ForegroundColor Magenta
Write-Host ""

# Check admin for service install
if (!(Test-AdminPrivileges)) {
    Write-ColorOutput "WARNING: Not running as Administrator!" Yellow
    Write-ColorOutput "Service installation requires admin privileges." Yellow
    Write-Host ""
    $relaunch = Read-Host "Restart this script as Administrator? (Y/N)"
    if ($relaunch -eq 'Y' -or $relaunch -eq 'y') {
        $scriptPath = $MyInvocation.MyCommand.Path
        Start-Process powershell -Verb RunAs -ArgumentList "-NoExit", "-File", "`"$scriptPath`""
        exit
    }
    Write-ColorOutput "Continuing without admin. Service will not be installed." Yellow
    Write-Host ""
}

# Setup type selection
if (!$SkipMPD) {
    Write-Host "Setup Options:" -ForegroundColor Cyan
    Write-Host "1) Native Windows MPD (Recommended - true system audio)"
    Write-Host "2) Containerized MPD (HTTP streaming only)"
    Write-Host ""
    $choice = Read-Host "Choose setup type [1/2]"
    
    $useNative = ($choice -eq "1")
}
else {
    $useNative = $false
}

# Get music directory
if (!$MusicDirectory) {
    $defaultMusic = [Environment]::GetFolderPath('MyMusic')
    $MusicDirectory = Read-Host "Music directory [$defaultMusic]"
    if ([string]::IsNullOrWhiteSpace($MusicDirectory)) {
        $MusicDirectory = $defaultMusic
    }
}

if (!(Test-Path $MusicDirectory)) {
    Write-ColorOutput "Error: Music directory not found: $MusicDirectory" Red
    exit 1
}

Write-ColorOutput "Music directory: $MusicDirectory" Green

# Create setup configuration file
$setupTypeString = if ($useNative) { "native" } else { "containerized" }
New-SetupConfiguration -SetupType $setupTypeString -MusicDirectory $MusicDirectory

# Install MPD (if native)
if ($useNative -and !$SkipMPD) {
    Write-Header "Installing Native Windows MPD"
    
    # Check if already installed
    if (!(Get-Command mpd -ErrorAction SilentlyContinue)) {
        if (!(Install-ChocoPackage "mpd")) {
            Write-ColorOutput "Failed to install MPD. Exiting." Red
            exit 1
        }
        # Refresh PATH again
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    }
    else {
        Write-ColorOutput "MPD is already installed" Green
    }
    
    # Create configuration
    $configPath = New-MPDConfiguration -MusicPath $MusicDirectory
    
    # Install service
    $serviceInstalled = Install-MPDService
    
    if (!$serviceInstalled) {
        Write-ColorOutput "Starting MPD manually..." Cyan
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        Start-Process mpd -ArgumentList "--no-daemon `"$configPath`"" -WindowStyle Hidden
        Start-Sleep -Seconds 3
    }
}

# Create Docker environment
if (!$SkipDocker) {
    Write-Header "Configuring Docker Environment"
    New-DockerEnvironment -MusicPath $MusicDirectory -UseNativeMPD $useNative
    
    # Start Docker services
    Write-Header "Starting Docker Services"
    if (!(Start-DockerServices -UseNativeMPD $useNative)) {
        Write-ColorOutput "Failed to start Docker services" Red
        exit 1
    }
}

# Test everything
$success = Test-Setup -UseNativeMPD $useNative

# Show summary
Show-Summary -UseNativeMPD $useNative

if ($success) {
    Write-ColorOutput "Opening web interface..." Cyan
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:5003"
}
else {
    Write-Host ""
    Write-ColorOutput "Setup completed with some issues. Check the messages above." Yellow
    Write-ColorOutput "Try: docker-compose logs -f" Yellow
}

Write-Host ""