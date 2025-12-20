# Maestro Server - Changelog

## Version 2.1.0 - HTTP Streaming UI & Critical Fixes (December 20, 2025)

### 🎧 HTTP Streaming Configuration
- **Admin UI for HTTP Streaming**: Configure MPD HTTP streaming without manual config editing
- **Simple Toggle**: Enable/disable HTTP streaming with one click
- **Advanced Settings**: Full control over port, encoder, bitrate, format, max clients, and bind address
- **Smart Defaults**: Pre-configured with optimal settings (port 8000, LAME encoder, 192kbps)
- **Auto-restart MPD**: Automatic service restart after configuration changes
- **Stream URL Display**: Shows connection URL for clients when streaming is enabled
- **Multi-room Setup**: Complete documentation for Raspberry Pi MPV clients

### 🔒 Critical Fixes
- **Database Backup/Restore**: Fixed missing sudo permissions for MPD database operations
- **Sudoers Configuration**: Added passwordless `cp` commands for backup/restore functionality
- **Update Script Enhancement**: Regenerate sudoers during updates for consistency
- **NFS Mount Recovery**: Documented solution for network share mount failures after reboot

### 🎨 UI/UX Improvements
- **Navigation Rebranding**: Changed "MPD Control" to "Maestro Control" across all admin pages
- **Navigation Consistency**: Removed new window behavior, direct navigation for better UX
- **OS Update Warnings**: Added safety notices with screen/tmux command examples

### 📚 Documentation
- **Ras-Pi-Client.md**: Complete guide for multi-room Raspberry Pi client setup
- **Admin UI Instructions**: Step-by-step streaming configuration via web interface
- **Alternative Methods**: Manual mpd.conf configuration documented as fallback

---

## Version 2.0.0 - Admin API Integration (December 14, 2025)

### 🎉 Major Release - Complete Music Server Solution

### ⚙️ New Admin API (Port 5004)
- **System Administration Dashboard**: Web-based system management interface
- **Library Management**: Configure music library folders and mount network shares
- **Network Mounts**: NFS and SMB/CIFS mount management with friendly names
- **Audio Configuration**: Detect and configure audio devices
- **System Monitoring**: CPU, memory, disk usage, and uptime tracking
- **System Updates**: One-click OS package updates with real-time output
- **Automatic fstab Reading**: Detects existing network mounts from /etc/fstab

### 🚀 Installation & Deployment
- **One-Command Installer**: Universal bash installer for Ubuntu/Debian/Arch
- **Automatic Service Setup**: Creates systemd services for web UI and admin API
- **Dependency Management**: Automatic installation of all required packages
- **Port Configuration**: Web UI on 5003, Admin API on 5004, MPD on 6600
- **No Docker Required**: Native Linux installation with systemd services

### 🔄 Navigation Improvements
- **Bidirectional Links**: Admin button in Web UI, MPD Control button in Admin
- **Smart Navigation**: Admin button navigates directly, MPD Control opens new tab
- **Consistent Branding**: Unified interface design across both applications

### 🧹 Code Cleanup
- **Removed Docker Support**: Streamlined for native Linux server deployment
- **Removed Windows Scripts**: Focused on Linux server environment
- **Removed Non-Functional Features**: Cleaned up mood auto-fill UI
- **Documentation Updates**: Comprehensive v2.0 documentation

### 🎨 User Interface
- **Mood Auto-Fill Removed**: Cleaned up non-functional feature from UI
- **Admin Integration**: Seamless navigation between Web UI and Admin API
- **Responsive Design**: Both interfaces optimized for desktop and mobile

### 🔧 Technical Changes
- **Default Port Change**: Web UI now defaults to 5003 (was 5000)
- **Enhanced fstab Parsing**: Generates friendly mount names from mount points
- **Service Management**: Proper systemd integration for both services
- **Environment Variables**: Configurable via .env or config.env

### 📦 Repository Changes
- **New Repository**: Maestro-Server (separate from Maestro-MPD-Control)
- **Git Tag**: v2.0.0 release tag created
- **GitHub Release**: Complete release with installer and documentation

---

## Version 1.0.0 - Docker Release (November 2025)

### ✨ Features
- **4 Complete Themes**: Dark, Light, High Contrast, Desert
- **Mobile Responsive**: Optimized interface for all screen sizes
- **Radio Stations**: Save and manage genre-based radio stations
- **Smart Auto-Fill**: Intelligent playlist management with Last.fm integration
- **Advanced Search**: Comprehensive music library search
- **Last.fm Integration**: Charts, scrobbling, and music discovery
- **Album Art Support**: Local and web-based album artwork
- **Real-time Updates**: Live playback status via WebSockets

### 🐳 Docker Support
- **Multi-Container Setup**: Separate MPD and web application containers
- **Flexible Deployment**: Support for both containerized and external MPD
- **Environment Configuration**: Complete environment variable support
- **Health Checks**: Built-in service monitoring
- **Data Persistence**: Preserves settings and cache across restarts
- **Security Hardening**: Non-root user execution

### 🎨 User Interface
- **Desert Theme**: New warm brown/tan theme with reddish accents
- **Mobile Footer**: Improved mobile layout with stacked controls
- **Navigation**: Consistent emoji-based navigation across all pages
- **Progress Bars**: Real-time track progress visualization
- **Settings Management**: Persistent theme and configuration storage

### 🔧 Technical Improvements
- **Memory Optimization**: Reduced MPD memory usage (3.2GB → 162MB)
- **Performance**: Optimized background monitoring and caching
- **Error Handling**: Improved error messages and fallback behavior
- **Configuration**: Environment-based configuration for Docker deployment
- **Security**: Removed admin features for public deployment

### 🎵 Music Features
- **Radio Station Mode**: Genre-based automatic playlist generation
- **Consume Mode**: Automatic track removal after playing
- **Shuffle Support**: Random playback with cross-page synchronization
- **Crossfade**: Smooth transitions between tracks
- **Volume Control**: Precise volume management with presets
- **Queue Management**: Advanced playlist manipulation

### 🌐 Integration
- **Last.fm Charts**: Personal music statistics and charts
- **Music Discovery**: Similar artist recommendations
- **External Links**: Wikipedia, AllMusic, MusicBrainz integration
- **API Support**: RESTful API endpoints for automation
- **WebSocket Events**: Real-time status updates

---

## Previous Versions

### Pre-1.0 Development
- Initial Flask application development
- MPD integration and control
- Basic theme system implementation
- Search functionality development
- Album art processing
- Last.fm API integration
- Auto-fill system creation
- Mobile responsiveness improvements

---

*For detailed technical information, see README.md*