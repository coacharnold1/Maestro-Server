# 📸 Screenshot Guide for Maestro

This guide will help you capture professional screenshots for the README and documentation.

## 🎯 Required Screenshots

### Priority 1 (Essential)

1. **hero-player.png** - Main player interface
2. **browse-albums.png** - Album grid view
3. **admin-dashboard.png** - System monitoring
4. **themes.png** - Theme showcase composite

### Priority 2 (Recommended)

5. **browse-artists.png** - Artist list with letter navigation
6. **cd-ripper.png** - CD ripper configuration
7. **library-management.png** - NFS mount configuration
8. **recent-albums.png** - Recent albums page

### Priority 3 (Nice to have)

9. **mobile-view.png** - Mobile responsive view
10. **install-success.png** - Installation terminal output
11. **charts.png** - Playback statistics
12. **settings-lastfm.png** - Last.fm setup page

---

## 📐 Screenshot Specifications

### General Guidelines

- **Resolution**: 1920x1080 (16:9) for desktop views
- **Format**: PNG (for transparency and quality)
- **Quality**: High (no compression artifacts)
- **Content**: Show real data (not empty states)
- **Themes**: Use visually appealing themes

### Recommended Themes for Screenshots

- **Dark** - Classic, professional look
- **Desert** - Warm, distinctive appearance
- **Sunset** - Eye-catching colors
- **Forest** - Natural, calming
- **High Contrast** - Accessibility showcase

### What NOT to Capture

- ❌ Empty playlists/queues
- ❌ "No albums found" states
- ❌ Personal information (IP addresses in production)
- ❌ Copyrighted album art (if distributing publicly)
- ❌ Error messages (unless for troubleshooting docs)

---

## 📷 Screenshot Preparation Checklist

### Before Capturing

1. **Clean your library**
   - Remove test/dummy data
   - Ensure album art is present
   - Check metadata is complete

2. **Populate test data**
   ```bash
   # Add some albums to queue
   # Start playback
   # Navigate to page you want to capture
   ```

3. **Set ideal window size**
   - Full screen or 1920x1080
   - Disable browser extensions
   - Hide bookmarks bar
   - Use F11 for fullscreen (exit dev tools)

4. **Check UI state**
   - Something is playing
   - Queue has multiple tracks
   - Volume is set (not 0 or 100)
   - Time shows elapsed progress

---

## 🎬 Screenshot Instructions

### 1. Hero Player Interface (hero-player.png)

**Location**: `http://YOUR_IP:5003` (main page)

**Setup:**
1. Select **Desert**, **Sunset**, or **Forest** theme
2. Play a track with nice album art
3. Add 5-10 tracks to queue
4. Set volume to ~60-70%
5. Let track play to ~30-40% progress

**What to capture:**
- Album art prominently displayed
- Track info (artist, album, title)
- Progress bar showing partial playback
- Volume slider visible
- Play/pause and navigation buttons
- Queue showing multiple tracks
- Footer with buttons visible

**Framing:**
- Full browser window
- Include some UI chrome (minimal)
- Center the player content
- Ensure nothing is cut off

**Tool:**
```bash
# Linux screenshot tool
gnome-screenshot -w -f ~/Maestro-Server/screenshots/hero-player.png
# Or use Spectacle on KDE
spectacle -a -o ~/Maestro-Server/screenshots/hero-player.png
```

---

### 2. Browse Albums (browse-albums.png)

**Location**: `http://YOUR_IP:5003` → Click "Albums"

**Setup:**
1. Use **Dark** or **High Contrast** theme
2. Ensure multiple albums are visible
3. Scroll to show variety of album art

**What to capture:**
- Grid of album covers (at least 12-20 visible)
- Album titles and artists beneath covers
- Clean, organized layout
- Navigation visible at top

**Framing:**
- Full page width
- Show 3-4 rows of albums
- Include page title "Browse Albums"

**Tool:**
```bash
# Full page screenshot
gnome-screenshot -w -f ~/Maestro-Server/screenshots/browse-albums.png
```

---

### 3. Admin Dashboard (admin-dashboard.png)

**Location**: `http://YOUR_IP:5004`

**Setup:**
1. Let system run for a few minutes (get realistic stats)
2. Use **Dark** theme
3. Ensure services are running

**What to capture:**
- CPU usage graph/percentage
- RAM usage with bar
- Disk usage for mount points
- Network traffic stats
- Service status (all green/running)
- System information panel

**Framing:**
- Full dashboard view
- All stat panels visible
- Show real-time data (not zeros)

**Tool:**
```bash
gnome-screenshot -w -f ~/Maestro-Server/screenshots/admin-dashboard.png
```

---

### 4. Theme Showcase (themes.png) - COMPOSITE IMAGE

This is a special composite image showing multiple themes.

**Method 1: Manual Composite**

1. Capture same page in 4 different themes:
   - Dark
   - High Contrast
   - Desert
   - Sunset

2. Use image editor to create 2x2 grid:
   ```bash
   # Using ImageMagick
   convert \
     dark.png highcontrast.png desert.png sunset.png \
     -resize 960x540 \
     +append -append \
     ~/Maestro-Server/screenshots/themes.png
   ```

**Method 2: Side-by-Side**

1. Capture Browse Albums page in 4 themes
2. Arrange in 1x4 horizontal strip
3. Add small labels to each

**What to show:**
- Same page (Browse Albums works well)
- Clear color differences
- Visual variety
- All themes look good

---

### 5. Browse Artists with Letter Nav (browse-artists.png)

**Location**: `http://YOUR_IP:5003` → Click "Artists"

**Setup:**
1. Ensure you have >50 artists (letter nav appears)
2. Use **Desert** or **Forest** theme
3. Click on a letter (e.g., "S") to show highlight

**What to capture:**
- Letter navigation bar (A-Z buttons)
- One letter highlighted (to show active state)
- Artist list below
- Artist names with track counts

**Framing:**
- Include letter nav at top
- Show several artists below
- Capture highlighted letter button

**Tool:**
```bash
gnome-screenshot -w -f ~/Maestro-Server/screenshots/browse-artists.png
```

---

### 6. CD Ripper Config (cd-ripper.png)

**Location**: `http://YOUR_IP:5004` → "CD Ripper"

**Setup:**
1. Use **Dark** theme
2. Show configuration form filled out

**What to capture:**
- Format selection (FLAC, MP3, etc.)
- Quality settings
- Output directory
- Auto-eject checkbox
- Save button

**Framing:**
- Full configuration panel
- Show all options clearly

**Tool:**
```bash
gnome-screenshot -w -f ~/Maestro-Server/screenshots/cd-ripper.png
```

---

### 7. Library Management (library-management.png)

**Location**: `http://YOUR_IP:5004` → "Library Management"

**Setup:**
1. Show NFS mount form or existing mounts
2. Display "Add Mount" interface

**What to capture:**
- Mount point input fields
- Server/path configuration
- Mount status indicators
- Update Library button

**Tool:**
```bash
gnome-screenshot -w -f ~/Maestro-Server/screenshots/library-management.png
```

---

### 8. Recent Albums (recent-albums.png)

**Location**: `http://YOUR_IP:5003` → "Recent"

**Setup:**
1. Use **Sunset** or **Forest** theme
2. Ensure recent_albums_dir has albums
3. Show grid of recent albums

**What to capture:**
- Grid of recently added albums
- Album art, artist, album name
- Clean layout
- "Recent Albums" title

**Tool:**
```bash
gnome-screenshot -w -f ~/Maestro-Server/screenshots/recent-albums.png
```

---

### 9. Mobile View (mobile-view.png)

**Method: Browser DevTools**

1. Open Chrome/Firefox DevTools (F12)
2. Click device toolbar icon
3. Select "iPhone 12 Pro" or similar
4. Navigate to main player page
5. Use "Capture screenshot" in DevTools

**What to capture:**
- Mobile responsive layout
- Touch-friendly buttons
- Compact queue view
- Hamburger menu (if applicable)

**Resolution**: 390x844 (iPhone) or 360x740 (Android)

**Tool:**
```
Use browser DevTools screenshot feature
Save as: mobile-view.png
```

---

### 10. Installation Success (install-success.png)

**Method: Terminal Screenshot**

1. Run installation in terminal
2. Wait for completion
3. Capture final success message

**What to capture:**
```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║             UPDATE COMPLETED SUCCESSFULLY!                 ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

Service Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Web UI:    ✓ Running
Admin API: ✓ Running
```

**Tool:**
```bash
# Terminal screenshot
gnome-screenshot -w -f ~/Maestro-Server/screenshots/install-success.png
```

---

### 11. Charts Page (charts.png)

**Location**: `http://YOUR_IP:5003` → Click "Charts"

**Setup:**
1. Play some music to generate stats
2. Use **Dark** theme
3. Show graphs/charts

**What to capture:**
- Top artists/albums/tracks
- Bar charts or graphs
- Playback statistics
- Time period selector

---

### 12. Last.fm Settings (settings-lastfm.png)

**Location**: `http://YOUR_IP:5003/settings`

**Setup:**
1. Show Last.fm section
2. Display numbered button flow (Test, Connect, Finalize)
3. Use **Dark** theme

**What to capture:**
- API Key/Secret fields
- Three numbered buttons
- Step-by-step instructions
- Save Settings button

---

## 🛠️ Tools & Tips

### Screenshot Tools

**Linux:**
```bash
# GNOME
gnome-screenshot -w -f output.png

# KDE
spectacle -a -o output.png

# Command line (full screen)
import -window root screenshot.png

# Command line (active window)
import -window $(xdotool getactivewindow) screenshot.png
```

**Browser Extensions:**
- **Full Page Screenshot** - Captures entire page with scrolling
- **Awesome Screenshot** - Annotations and editing
- **Nimbus Screenshot** - Video capture support

### Image Editing

**Create composite images:**
```bash
# Install ImageMagick
sudo apt install imagemagick

# 2x2 grid
montage image1.png image2.png image3.png image4.png \
  -tile 2x2 -geometry +5+5 output.png

# Horizontal strip
convert image1.png image2.png image3.png image4.png \
  +append output.png

# Add border
convert input.png -border 10x10 -bordercolor "#333" output.png
```

**Resize for web:**
```bash
# Resize to 1920 width (maintain aspect)
convert input.png -resize 1920x output.png

# Optimize PNG
optipng output.png
```

### Video Capture (Optional)

For animated GIFs showing features:

```bash
# Record screen
peek  # GUI tool for GIF recording

# Or use FFmpeg
ffmpeg -f x11grab -s 1920x1080 -i :0.0 -vcodec libx264 output.mp4

# Convert to GIF
ffmpeg -i output.mp4 -vf "fps=10,scale=800:-1:flags=lanczos" output.gif
```

---

## 📦 Organizing Screenshots

### Directory Structure
```
screenshots/
├── hero-player.png          (1.2 MB)
├── browse-albums.png        (890 KB)
├── browse-artists.png       (720 KB)
├── admin-dashboard.png      (650 KB)
├── themes.png               (1.8 MB)
├── cd-ripper.png            (450 KB)
├── library-management.png   (520 KB)
├── recent-albums.png        (880 KB)
├── mobile-view.png          (320 KB)
├── install-success.png      (180 KB)
├── charts.png               (590 KB)
└── settings-lastfm.png      (410 KB)
```

### Git LFS (Optional)

For large screenshot files:

```bash
# Install Git LFS
sudo apt install git-lfs
git lfs install

# Track PNG files
git lfs track "screenshots/*.png"

# Add and commit
git add .gitattributes
git add screenshots/
git commit -m "Add screenshots"
```

---

## ✅ Quality Checklist

Before submitting screenshots:

- [ ] Resolution is 1920x1080 (desktop) or appropriate for mobile
- [ ] Images are sharp and clear (no blur)
- [ ] UI elements are fully visible (not cut off)
- [ ] Data is realistic (not empty or test data)
- [ ] Theme is visually appealing
- [ ] No personal information visible
- [ ] File size is reasonable (<2MB each)
- [ ] Filenames match documentation
- [ ] All required screenshots captured

---

## 🚀 Quick Start

**Minimal set (10 minutes):**
1. hero-player.png (main interface)
2. browse-albums.png (album grid)
3. admin-dashboard.png (system stats)

**Complete set (30 minutes):**
- All 12 screenshots above

**Professional set (1 hour):**
- All screenshots + theme composites + mobile views

---

## 📝 Adding to README

Once screenshots are captured:

1. **Create directory:**
   ```bash
   mkdir -p screenshots
   ```

2. **Add screenshots:**
   ```bash
   cp /path/to/screenshots/* screenshots/
   ```

3. **Update README.md:**
   Replace placeholder comments with:
   ```markdown
   ![Maestro Player](screenshots/hero-player.png)
   ```

4. **Commit to git:**
   ```bash
   git add screenshots/
   git commit -m "Add screenshots to documentation"
   git push
   ```

5. **Verify on GitHub:**
   - Check that images display properly
   - Ensure file sizes are reasonable
   - Test on mobile GitHub view

---

## 🎨 Pro Tips

1. **Use consistent theme** - Same theme across related screenshots
2. **Show activity** - Always show something playing
3. **Clean data** - Remove test/dummy entries
4. **Good lighting** - Themes show better with consistent display settings
5. **Crop carefully** - Remove unnecessary browser chrome
6. **Optimize files** - Use `optipng` or `pngquant` to reduce size
7. **Version control** - Keep source (unedited) screenshots separate

---

## 🔄 Updating Screenshots

When updating screenshots after changes:

1. Identify which screenshots need updating
2. Follow setup instructions above
3. Overwrite old files with same names
4. Commit with clear message:
   ```bash
   git add screenshots/hero-player.png
   git commit -m "Update hero screenshot with v2.2 UI changes"
   ```

---

**Questions?** Open an issue with tag `documentation`.
