# 🎵 Maestro MPD Control - Modern Music Server Interface

> **Transform your Music Player Daemon into a beautiful, modern web application**

## 🌟 **What is Maestro MPD Control?**

Maestro MPD Control is a sleek, responsive web interface that brings your Music Player Daemon (MPD) into the modern age. Whether you're running a home media server, managing a multi-room audio system, or just want a better way to control your music, this Docker-ready application has you covered.

## 🚀 **Why Choose Maestro MPD Control?**

### ✨ **Beautiful & Intuitive**
- **4 Stunning Themes** - Dark, Light, High Contrast, and Desert
- **Mobile-First Design** - Perfect on phones, tablets, and desktops
- **Real-Time Updates** - Live playback status without page refreshes
- **Album Art Integration** - Gorgeous artwork from your files and Last.fm

### 🎵 **Powerful Music Management**
- **Smart Radio Stations** - Create genre-based auto-playing stations
- **Intelligent Auto-Fill** - Keep your queue full with similar music
- **Advanced Search** - Find any track in seconds across your entire library
- **Last.fm Charts** - Discover your listening habits with beautiful stats

### 🐳 **Docker-Ready Deployment**
- **One-Command Setup** - Get running in under 60 seconds
- **Flexible Architecture** - Use containerized MPD or connect to existing servers
- **Production Ready** - Security hardened with health checks and persistence
- **Multi-Platform** - Works on Linux, macOS, Windows, Raspberry Pi

## 📸 **See It In Action**

### Desktop Experience
![Desktop Interface](screenshots/Screenshot_Main.png)
*Clean, professional interface with large album art and intuitive controls*

### Mobile Experience
<img src="screenshots/mobile3-main.png" alt="Mobile Interface" width="400px">
*Responsive design that works beautifully on any screen size*

| Mobile 1 | Mobile 2 | Mobile 3 |
|------------|-------------|---------------|
| ![Mobile - ](screenshots/mobile1.png) | ![Mobile](screenshots/mobile2.png) | ![Mobile](screenshots/mobile4.png) |


### Theme Variety
| Dark Theme | High Contrast | Desert Theme |
|------------|---------------|--------------|
| ![Dark](screenshots/Screenshot_Main.png) | ![HC](screenshots/Screenshot_High-Contrast-Theme.png) | ![Desert](screenshots/Screenshot_Desert-Theme.png) |


### Advanced Features
![Radio Stations](screenshots/Screenshot_Random-and-Radio.png)
*Create and manage genre-based radio stations for automatic playlist generation*

![Last.fm Charts](screenshots/Screenshot_LAST-FM-Charts.png)
*Beautiful charts showing your personal music statistics*

## 🎯 **Perfect For**

### 🏠 **Home Media Servers**
- NAS-based audio systems
- Dedicated HTPC setups

### 🎧 **Personal Music Libraries**
- Large local music collections
- Audiophile setups with lossless audio
- Music discovery and organization

### 🏢 **Multi-Room Audio**
**[See Ras-Pi-Client](Ras-Pi-Client.md)** for a a very nice streming client.  I use this in my bedroom.  It is not synced very well. You will need to config snapcast for that.
- Restaurant/cafe background music
- Office sound systems  
- Home audio distribution

### 🔧 **Developers & Tinkerers**
- API integration projects
- Custom music solutions
- Learning Docker deployment

## ⚡ **Quick Start** (Under 60 Seconds!)

```bash
# 1. Clone the repository
git clone https://github.com/coacharnold1/maestro-mpd-control.git
cd maestro-mpd-control

# 2. Run the interactive setup
./setup.sh

# 3. Open your browser
# Visit http://localhost:5003
```

That's it! The setup script handles everything:
- Music directory configuration
- Docker container management  
- Theme selection
- Optional Last.fm integration (**Get API key:** https://www.last.fm/api/account/create)

## 🎨 **Feature Highlights**

### Smart Music Discovery
- **Similar Artist Recommendations** powered by Last.fm
- **Automatic Playlist Generation** based on your current music
- **Genre-Based Radio Stations** for mood-based listening

### Professional Interface
- **WebSocket Real-Time Updates** - No page refreshes needed
- **Responsive Design** - Works on any device
- **Accessibility Support** - High contrast theme for better visibility

### Advanced Control
- **Full MPD Feature Support** - Consume mode, crossfade, shuffle
- **Volume Management** with presets and fine control
- **Queue Management** with drag-drop playlist editing

## 🔧 **Technical Excellence**

- **🐳 Docker Best Practices** - Multi-stage builds, non-root execution
- **🔒 Security Hardened** - No admin features, proper isolation  
- **📊 Health Monitoring** - Built-in service health checks
- **💾 Data Persistence** - Settings and cache survive restarts
- **🌐 API Ready** - RESTful endpoints for automation

## 📈 **Growing Community**

Join hundreds of users who have transformed their music servers:

- ⭐ **Star this repo** if you find it useful
- 🐛 **Report issues** to help improve the project
- 💡 **Suggest features** for future releases
- 🤝 **Contribute code** to make it even better

## 📚 **Documentation**

- 📖 **[Complete Setup Guide](QUICK_SETUP.md)** - Get started immediately
- 🐳 **[Docker Documentation](DOCKER_USAGE.md)** - Advanced deployment
- 📋 **[Configuration Reference](README.md)** - All options explained
- 🔄 **[Changelog](CHANGELOG.md)** - Version history and features

---

### 🎵 **Ready to revolutionize your music server?**

[**Get Started Now →**](QUICK_SETUP.md) • [**View Documentation →**](README.md) • [**Report Issues →**](issues)

*Transform your MPD setup into a modern, beautiful music experience in under a minute!*
