# Maestro MPD Control - Advanced Cleanup Script
# Resolves MPD conflicts and cleans up containers

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Maestro Advanced Cleanup" -ForegroundColor Cyan  
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check what's currently running
Write-Host "Checking current status..." -ForegroundColor Yellow

# Check for MPD service
$mpdService = Get-Service "MPD" -ErrorAction SilentlyContinue
if ($mpdService) {
    Write-Host "Native MPD Service Status: $($mpdService.Status)" -ForegroundColor $(if ($mpdService.Status -eq "Running") { "Green" } else { "Yellow" })
} else {
    Write-Host "Native MPD Service: Not installed" -ForegroundColor Gray
}

# Check for Docker containers
Write-Host "Checking Docker containers..." -ForegroundColor Yellow
try {
    $containers = docker ps --format "{{.Names}}" 2>$null
    if ($containers) {
        $mpdContainers = $containers | Where-Object { $_ -match "mpd" }
        $webContainers = $containers | Where-Object { $_ -match "web-control" }
        
        if ($mpdContainers) {
            Write-Host "MPD Containers Running: $($mpdContainers -join ', ')" -ForegroundColor Red
        }
        if ($webContainers) {
            Write-Host "Web Containers Running: $($webContainers -join ', ')" -ForegroundColor Green
        }
    } else {
        Write-Host "No Docker containers currently running" -ForegroundColor Gray
    }
} catch {
    Write-Host "Docker not available or not running" -ForegroundColor Red
}

Write-Host ""

# Check for port conflicts
Write-Host "Checking for port conflicts..." -ForegroundColor Yellow
$port6600 = netstat -an | findstr ":6600"
$port5003 = netstat -an | findstr ":5003"

if ($port6600) {
    Write-Host "Port 6600 (MPD) is in use:" -ForegroundColor Yellow
    Write-Host $port6600 -ForegroundColor Gray
}
if ($port5003) {
    Write-Host "Port 5003 (Web) is in use:" -ForegroundColor Yellow  
    Write-Host $port5003 -ForegroundColor Gray
}

Write-Host ""

# Offer cleanup options
Write-Host "Cleanup Options:" -ForegroundColor Cyan
Write-Host "1) Stop all Docker containers (keep native MPD running)"
Write-Host "2) Stop all Docker containers AND native MPD service"
Write-Host "3) Stop only MPD containers (keep web containers)"
Write-Host "4) Full reset (stop everything, clean Docker)"
Write-Host "5) Just show status and exit"
Write-Host ""

$choice = Read-Host "Choose option [1-5]"

switch ($choice) {
    "1" {
        Write-Host "Stopping all Docker containers..." -ForegroundColor Yellow
        docker-compose -f docker-compose.yml down 2>$null
        docker-compose -f docker-compose.windows.yml down 2>$null
        docker-compose -f docker-compose.native-mpd.yml down 2>$null
        Write-Host "Docker containers stopped. Native MPD service left running." -ForegroundColor Green
    }
    
    "2" {
        Write-Host "Stopping Docker containers..." -ForegroundColor Yellow
        docker-compose -f docker-compose.yml down 2>$null
        docker-compose -f docker-compose.windows.yml down 2>$null  
        docker-compose -f docker-compose.native-mpd.yml down 2>$null
        
        if ($mpdService -and $mpdService.Status -eq "Running") {
            Write-Host "Stopping native MPD service..." -ForegroundColor Yellow
            Stop-Service "MPD" -Force
            Write-Host "All MPD instances stopped." -ForegroundColor Green
        } else {
            Write-Host "Docker containers stopped. No native MPD service found." -ForegroundColor Green
        }
    }
    
    "3" {
        Write-Host "Stopping MPD containers only..." -ForegroundColor Yellow
        docker stop mpd-server 2>$null
        docker rm mpd-server 2>$null
        Write-Host "MPD containers stopped. Web containers left running." -ForegroundColor Green
    }
    
    "4" {
        Write-Host "Full reset - stopping everything..." -ForegroundColor Red
        
        # Stop all compose configurations
        docker-compose -f docker-compose.yml down 2>$null
        docker-compose -f docker-compose.windows.yml down 2>$null
        docker-compose -f docker-compose.native-mpd.yml down 2>$null
        
        # Stop native MPD if running
        if ($mpdService -and $mpdService.Status -eq "Running") {
            Stop-Service "MPD" -Force
        }
        
        # Clean up Docker
        Write-Host "Cleaning up Docker networks and volumes..." -ForegroundColor Yellow
        docker network prune -f 2>$null
        docker volume prune -f 2>$null
        
        Write-Host "Full reset completed." -ForegroundColor Green
    }
    
    "5" {
        Write-Host "Status check completed. No changes made." -ForegroundColor Gray
    }
    
    default {
        Write-Host "Invalid choice. No changes made." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "To restart Maestro after cleanup:" -ForegroundColor Cyan
Write-Host "- Native MPD setup: docker-compose -f docker-compose.native-mpd.yml up -d" -ForegroundColor White
Write-Host "- Containerized setup: docker-compose -f docker-compose.windows.yml --profile with-mpd up -d" -ForegroundColor White
Write-Host "- Or just run: .\start-maestro.ps1" -ForegroundColor White

Write-Host ""
Read-Host "Press Enter to exit"