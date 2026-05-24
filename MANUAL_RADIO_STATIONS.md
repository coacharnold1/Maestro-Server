# Manual Radio Stations Feature

## Overview
Added the ability to save and manage manually added radio stations in Maestro, completely separate from the auto-updating station database. This prevents loss of custom stations when updating from external sources.

## Implementation

### Backend (app.py)
Added four new functions to manage manual stations:

1. **`load_manual_stations()`** - Loads manually added stations from persistent storage (`manual_radio_stations.json`)
2. **`save_manual_stations(stations)`** - Persists the station list to disk
3. **`add_manual_station(name, url, favicon)`** - Adds a new manual station with validation
   - Prevents duplicate URLs
   - Stores metadata (name, URL, favicon, added_date)
4. **`remove_manual_station(url)`** - Removes a station by URL

### API Endpoints

Three new REST endpoints created:

- **`GET /api/radio/manual/list`** - Returns all saved manual stations
- **`POST /api/radio/manual/save`** - Saves a new manual station
  - Required: `name`, `url`
  - Optional: `favicon`
  - Validates URL format (must be http:// or https://)
- **`POST /api/radio/manual/remove`** - Deletes a station by URL
  - Required: `url`

### Frontend (templates/radio.html)

Enhanced the Manual tab with:

1. **Input Fields**:
   - Station Name
   - Stream URL (http/https)
   - Favicon URL (optional)

2. **Action Buttons**:
   - "Play & Save" - Saves the station and plays it
   - "Play Only" - Plays without saving

3. **Saved Stations List**:
   - Displays all saved manual stations
   - Shows station name, save date, favicon
   - "Play" button to play the station
   - "Delete" button to remove the station

### JavaScript Functions

- **`loadManualStations()`** - Fetches saved stations from server
- **`renderSavedStations()`** - Displays the saved stations list
- **`playAndSaveManualStream()`** - Validates, saves, and plays a station
- **`deleteManualStation(url, name)`** - Removes a station with confirmation
- Tab switching automatically loads manual stations when the Manual tab is clicked

## Data Storage

Manual stations are stored in `manual_radio_stations.json` in the app root directory:

```json
[
  {
    "name": "Station Name",
    "url": "https://stream.url",
    "favicon": "https://favicon.url",
    "added_date": "2026-02-15T10:30:00.000000",
    "manual": true
  }
]
```

## Key Features

✅ **Persistent Storage** - Stations survive app restarts  
✅ **Separate from API** - Won't be overwritten by database updates  
✅ **Duplicate Prevention** - Can't save same URL twice  
✅ **URL Validation** - Ensures proper http/https format  
✅ **Easy Management** - Add/remove with simple UI buttons  
✅ **Metadata Tracking** - Records when station was added  
✅ **Favicon Support** - Optional custom logos for stations  

## Testing

All functionality verified with comprehensive unit tests:
- Empty state handling
- Adding stations
- Duplicate prevention
- Removal functionality
- File persistence
- Error handling

All 10 test scenarios passed successfully.

## Usage

1. Go to the **Radio** page
2. Click the **📝 Manual** tab
3. Enter station details:
   - Station Name (e.g., "My Favorite Jazz")
   - Stream URL (required, must be valid stream)
   - Favicon URL (optional)
4. Click **▶️ Play & Save** to save and play immediately
5. Saved stations appear below and can be played anytime
6. Use **🗑️ Delete** to remove a station

## Notes

- Manual stations are completely independent of the Radio Browser API
- Updating station sources from web databases won't affect your saved stations
- Each station is identified by URL to prevent duplicates
- Optional favicon URLs enhance the user interface
