# Setup Script Changes Documentation

## Overview
This document details all changes made to `setup.sh` to fix installation issues and improve user experience for the GitHub release.

## Problems Fixed

### 1. **Corrupted .env File Issue**
- **Problem**: When users chose "Keep existing configuration", the script would skip validation and fail if the .env file had syntax errors (like unquoted paths with spaces)
- **Impact**: Installation failure with cryptic error messages
- **Example**: `RECENT_MUSIC_DIRS=/media/music/down, /media/music/gidney` caused bash execution errors

### 2. **Unnecessary Docker Rebuilds**
- **Problem**: Docker images were always rebuilt even when existing images were available
- **Impact**: Wasted time and bandwidth for users with working installations

### 3. **Missing Recent Music Directories Configuration**
- **Problem**: No way to update just the Recent Music Directories setting without full reconfiguration
- **Impact**: Users had to reconfigure everything to change one setting

### 4. **Poor Error Handling for Existing Installations**
- **Problem**: No validation of existing configurations before attempting to use them
- **Impact**: Silent failures and confusing error messages

## Changes Made

### A. New Functions Added

#### 1. `check_existing_docker_images()` (Lines ~270-350)
```bash
# Function to check for existing Docker images
check_existing_docker_images() {
    local web_image_exists=false
    local containers_running=false
    
    # Check if web image exists
    if docker images maestro-mpd-control-web --format "{{.Repository}}" 2>/dev/null | grep -q "maestro-mpd-control-web"; then
        web_image_exists=true
    fi
    
    # Check if containers are running
    if docker ps --format "{{.Names}}" 2>/dev/null | grep -q "mpd-web-control"; then
        containers_running=true
    fi
    
    if [ "$web_image_exists" = true ]; then
        echo ""
        print_warning "Existing Docker image found: maestro-mpd-control-web"
        
        if [ "$containers_running" = true ]; then
            print_status "Containers are currently running"
        fi
        
        echo ""
        echo "Would you like to:"
        echo "1) Use existing image (skip build)"
        echo "2) Rebuild image (recommended for updates)"
        echo "3) Remove existing image and rebuild"
        echo "4) Exit setup"
        echo ""
        read -p "Choice [1/2/3/4]: " docker_choice
        
        case $docker_choice in
            1)
                print_success "Using existing Docker image"
                SKIP_DOCKER_BUILD=true
                return 0
                ;;
            2)
                print_status "Will rebuild Docker image"
                FORCE_DOCKER_BUILD=true
                return 0
                ;;
            3)
                print_status "Removing existing image and rebuilding..."
                if [ "$containers_running" = true ]; then
                    print_status "Stopping running containers..."
                    docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
                fi
                
                print_status "Removing Docker image..."
                docker rmi maestro-mpd-control-web 2>/dev/null || true
                
                # Also remove related images
                docker images --filter="reference=maestro-mpd-control*" -q | xargs -r docker rmi 2>/dev/null || true
                
                print_success "Existing image removed"
                FORCE_DOCKER_BUILD=true
                return 0
                ;;
            4)
                echo "Setup cancelled."
                exit 0
                ;;
            *)
                print_status "Using existing Docker image (default)"
                SKIP_DOCKER_BUILD=true
                return 0
                ;;
        esac
    else
        # No existing image, need to build
        FORCE_DOCKER_BUILD=true
        return 0
    fi
}
```

**Purpose**: Detects existing Docker images and gives users choice whether to rebuild or reuse them.

#### 2. `validate_env_file()` (Lines ~352-385)
```bash
# Function to validate existing .env file
validate_env_file() {
    local env_file="$1"
    local validation_failed=false
    
    if [ ! -f "$env_file" ]; then
        return 1
    fi
    
    print_status "Validating existing .env configuration..."
    
    # Check for syntax errors by attempting to source it in a subshell
    if ! (set -e; source "$env_file" >/dev/null 2>&1); then
        print_error "Syntax errors found in .env file"
        validation_failed=true
    fi
    
    # Check for common issues
    if grep -q "RECENT_MUSIC_DIRS=.*[^,]\\s" "$env_file" 2>/dev/null; then
        print_error "Unquoted spaces found in RECENT_MUSIC_DIRS"
        validation_failed=true
    fi
    
    # Check for required variables
    local required_vars=("MUSIC_DIRECTORY" "MPD_HOST" "MPD_PORT" "WEB_PORT")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$env_file" 2>/dev/null; then
            print_warning "Missing required variable: $var"
        fi
    done
    
    if [ "$validation_failed" = true ]; then
        return 1
    else
        print_success "Configuration file validation passed"
        return 0
    fi
}
```

**Purpose**: Validates existing .env files for syntax errors and common issues before attempting to use them.

#### 3. `configure_recent_dirs()` (Lines ~455-470)
```bash
# Function to configure Recent Music Directories
configure_recent_dirs() {
    echo ""
    echo -e "${CYAN}⚡ Recent Albums Performance${NC}"
    echo "=============================="
    echo ""
    echo "For faster 'Recent Albums' loading, you can specify directories"
    echo "within your music library that contain your newest music."
    echo ""
    echo "Examples:"
    echo "  • New Releases,2024,2025"
    echo "  • Latest Albums,Downloads"  
    echo "  • Recent,New Music"
    echo ""
    echo "Leave empty to scan entire library (slower but comprehensive)"
    echo ""
    read -p "Recent music directories (comma-separated) []: " RECENT_DIRS
}
```

**Purpose**: Dedicated function for Recent Music Directories configuration that can be called independently.

### B. Enhanced Configuration Handling (Lines ~490-540)

#### Before:
```bash
# Check if .env already exists
if [ -f .env ]; then
    echo ""
    print_warning "Existing .env configuration found"
    echo ""
    echo "Would you like to:"
    echo "1) Keep existing configuration"
    echo "2) Reconfigure from scratch"
    echo "3) Exit setup"
    echo ""
    read -p "Choice [1/2/3]: " env_choice
    
    case $env_choice in
        2) rm -f .env && print_status "Removed existing configuration" ;;
        3) echo "Setup cancelled." && exit 0 ;;
        *) print_status "Using existing configuration" && SKIP_CONFIG=true ;;
    esac
fi
```

#### After:
```bash
# Check if .env already exists
if [ -f .env ]; then
    echo ""
    print_warning "Existing .env configuration found"
    
    # Validate the existing .env file
    if validate_env_file ".env"; then
        echo ""
        echo "Would you like to:"
        echo "1) Keep existing configuration"
        echo "2) Update Recent Music Directories only"
        echo "3) Reconfigure from scratch"
        echo "4) Exit setup"
        echo ""
        read -p "Choice [1/2/3/4]: " env_choice
        
        case $env_choice in
            1) 
                print_status "Using existing configuration"
                SKIP_CONFIG=true
                ;;
            2)
                print_status "Updating Recent Music Directories configuration"
                SKIP_CONFIG=true
                UPDATE_RECENT_DIRS=true
                ;;
            3) 
                rm -f .env && print_status "Removed existing configuration" 
                ;;
            4) 
                echo "Setup cancelled." && exit 0 
                ;;
            *) 
                print_status "Using existing configuration"
                SKIP_CONFIG=true
                ;;
        esac
    else
        echo ""
        print_error "Configuration file has errors and cannot be used safely"
        echo "Would you like to:"
        echo "1) Reconfigure from scratch (recommended)"
        echo "2) Exit setup"
        echo ""
        read -p "Choice [1/2]: " repair_choice
        
        case $repair_choice in
            1) 
                rm -f .env && print_status "Removed corrupted configuration" 
                ;;
            *) 
                echo "Setup cancelled." && exit 0 
                ;;
        esac
    fi
fi
```

**Changes**:
- Added validation step before offering choices
- Added option 2 for updating just Recent Music Directories  
- Added option 4 for exit
- Added corrupted file handling with forced reconfiguration or exit

### C. Added Recent Directories Update Logic (Lines ~545-575)

```bash
# Handle Recent Directories update for existing configs
if [ "$UPDATE_RECENT_DIRS" = "true" ]; then
    echo ""
    print_status "Updating Recent Music Directories configuration..."
    
    # Source existing .env to get current values
    source .env 2>/dev/null || true
    
    configure_recent_dirs
    
    # Update just the RECENT_MUSIC_DIRS in existing .env
    if [ -n "$RECENT_DIRS" ]; then
        # Properly quote the value to handle spaces and commas
        escaped_dirs=$(printf '%s' "$RECENT_DIRS" | sed 's/"/\\"/g')
        if grep -q "^RECENT_MUSIC_DIRS=" .env; then
            sed -i "s/^RECENT_MUSIC_DIRS=.*/RECENT_MUSIC_DIRS=\"$escaped_dirs\"/" .env
        else
            echo "RECENT_MUSIC_DIRS=\"$escaped_dirs\"" >> .env
        fi
    else
        if grep -q "^RECENT_MUSIC_DIRS=" .env; then
            sed -i "s/^RECENT_MUSIC_DIRS=.*/RECENT_MUSIC_DIRS=/" .env
        else
            echo "RECENT_MUSIC_DIRS=" >> .env
        fi
    fi
    
    print_success "Recent Music Directories updated in .env"
fi
```

**Purpose**: Allows users to update just the Recent Music Directories setting without full reconfiguration.

### D. Updated Configuration Wizard (Lines ~715-720)

#### Before:
```bash
    # Recent Albums performance configuration
    echo ""
    echo -e "${CYAN}⚡ Recent Albums Performance${NC}"
    echo "=============================="
    echo ""
    echo "For faster 'Recent Albums' loading, you can specify directories"
    echo "within your music library that contain your newest music."
    echo ""
    echo "Examples:"
    echo "  • New Releases,2024,2025"
    echo "  • Latest Albums,Downloads"  
    echo "  • Recent,New Music"
    echo ""
    echo "Leave empty to scan entire library (slower but comprehensive)"
    echo ""
    read -p "Recent music directories (comma-separated) []: " RECENT_DIRS
```

#### After:
```bash
    # Recent Albums performance configuration
    configure_recent_dirs
```

**Purpose**: Reuses the dedicated function for consistency.

### E. Fixed .env File Generation (Line ~780)

#### Before:
```bash
# Recent Albums Performance
RECENT_MUSIC_DIRS=$RECENT_DIRS
```

#### After:
```bash
# Recent Albums Performance
RECENT_MUSIC_DIRS="$RECENT_DIRS"
```

**Purpose**: Properly quotes the variable to handle spaces and special characters.

### F. Enhanced Docker Deployment Logic (Lines ~820-870)

#### Before:
```bash
print_status "$DOCKER Starting Docker deployment..."

# Always build Docker images (even when keeping existing config)
print_status "Building/rebuilding Docker containers..."

# Build and start services
if [ -f .env ]; then
    source .env
fi

# Start services
print_status "Building and starting containers..."

if $COMPOSE_CMD $PROFILE_ARG up -d --build; then
    print_success "Services started successfully"
else
    print_error "Failed to start services"
    echo ""
    echo "Check logs with: $COMPOSE_CMD logs"
    exit 1
fi
```

#### After:
```bash
print_status "$DOCKER Starting Docker deployment..."

# Check for existing Docker images
check_existing_docker_images

# Build and start services
if [ -f .env ]; then
    source .env
fi

# Start services
if [ "$SKIP_DOCKER_BUILD" = "true" ]; then
    print_status "Starting services with existing Docker image..."
    if $COMPOSE_CMD $PROFILE_ARG up -d; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services with existing image"
        echo ""
        echo "The existing image may be incompatible. Try rebuilding:"
        echo "  $COMPOSE_CMD $PROFILE_ARG up -d --build"
        exit 1
    fi
else
    print_status "Building and starting containers..."
    if $COMPOSE_CMD $PROFILE_ARG up -d --build; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        echo ""
        echo "Check logs with: $COMPOSE_CMD logs"
        exit 1
    fi
fi
```

**Changes**:
- Added Docker image detection before deployment
- Conditional building based on `SKIP_DOCKER_BUILD` flag
- Better error messages for image compatibility issues
- Separate handling for existing vs new images

## New User Experience Flow

### Fresh Installation:
1. No .env file exists → Full configuration wizard
2. No Docker images exist → Build required
3. Complete setup with all prompts

### Existing Valid Configuration:
1. .env file found → Validation passes
2. 4 options offered:
   - Keep existing config
   - Update Recent Dirs only  
   - Reconfigure from scratch
   - Exit
3. Docker image detection → User choice to rebuild or reuse
4. Conditional Docker operations

### Existing Corrupted Configuration:  
1. .env file found → Validation fails
2. Error messages explain issues
3. Forced choice: Reconfigure or Exit
4. No option to proceed with broken config

### Existing Installation Update:
1. Keep existing config
2. Choose to use existing Docker image (fast)
3. Or choose to rebuild (for updates)
4. Or choose to clean rebuild (remove + rebuild)

## Benefits

### 1. **Reliability**
- ✅ Validates configurations before use
- ✅ Prevents failures from corrupted .env files  
- ✅ Clear error messages for common issues
- ✅ Graceful handling of edge cases

### 2. **Performance**
- ✅ Skip unnecessary Docker builds
- ✅ Reuse existing working images
- ✅ Partial updates for single settings
- ✅ Faster repeated installations

### 3. **User Experience**
- ✅ Clear choices at each step
- ✅ Informative status messages
- ✅ Recovery options for problems
- ✅ No more cryptic bash errors

### 4. **Maintainability**
- ✅ Modular functions for specific tasks
- ✅ Consistent error handling
- ✅ Reusable configuration components
- ✅ Better code organization

## Testing Scenarios

### To test these changes:

1. **Fresh install**: Remove .env and Docker images, run setup
2. **Existing valid config**: Run setup with valid .env, test all 4 options
3. **Corrupted config**: Create .env with unquoted spaces, verify validation catches it
4. **Docker image reuse**: Run setup with existing images, test skip build option
5. **Partial update**: Use option 2 to update just Recent Directories
6. **Image rebuild**: Test options 2 and 3 in Docker image menu
7. **Container running**: Test with containers already running

## Files Modified

- `setup.sh` - Primary installation script (all changes above)

## Backward Compatibility

- ✅ All existing functionality preserved
- ✅ Fresh installations work exactly as before  
- ✅ No breaking changes to .env file format
- ✅ Docker deployment process unchanged (when rebuilding)
- ✅ All command-line options still work

## Version Compatibility

These changes are compatible with:
- Docker 20.10+
- Docker Compose v2+
- Bash 4.0+
- All existing .env configurations (if syntactically valid)

---

*Generated on: November 29, 2025*  
*Author: AI Assistant*  
*Purpose: GitHub Release v1.4 Preparation*