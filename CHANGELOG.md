# Maestro MPD Control - Changelog

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