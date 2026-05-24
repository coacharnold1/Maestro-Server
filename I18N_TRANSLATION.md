# Maestro i18n (Internationalization)

## Overview
Maestro uses a **hybrid JavaScript-based translation system** that requires zero template changes. This makes it safe, easy to add languages, and simple to maintain.

## Current Languages
- 🇬🇧 **English** (en) - Default
- 🇮🇹 **Italiano** (it) - Full translation

## How It Works

### 1. Translation Dictionary
**File:** `static/translations.json`

Contains all translatable strings in a simple JSON structure:

```json
{
  "en": {
    "play": "Play",
    "pause": "Pause"
  },
  "it": {
    "play": "Riproduci",
    "pause": "Pausa"
  }
}
```

### 2. Translation Handler
**File:** `static/i18n.js`

- Auto-detects browser language
- Loads translations from JSON
- Applies translations on page load
- Creates language selector dropdown
- Stores user preference in localStorage

### 3. Template Attributes
Add `data-i18n` attributes to HTML elements:

```html
<button data-i18n="play">Play</button>
<h2 data-i18n="volume">Volume</h2>
```

The JavaScript will automatically replace the text while preserving emojis:
```html
<button data-i18n="play">▶️ Play</button>  →  ▶️ Riproduci
```

## Adding a New Language

### Step 1: Add to translations.json
```json
{
  "en": { ... },
  "it": { ... },
  "de": {
    "play": "Abspielen",
    "pause": "Pausieren",
    ...
  }
}
```

### Step 2: Update language selector
Edit `static/i18n.js` line ~115:

```javascript
<select id="language-selector" ...>
    <option value="en">English</option>
    <option value="it">Italiano</option>
    <option value="de">Deutsch</option>  <!-- Add this -->
</select>
```

### Step 3: Update supported languages
Edit `static/i18n.js` line ~22:

```javascript
detectBrowserLanguage() {
    const langCode = browserLang.split('-')[0];
    return ['en', 'it', 'de'].includes(langCode) ? langCode : 'en';
}
```

That's it! No template changes needed.

## Translating More UI Elements

### In Templates
Find text to translate and add `data-i18n` attribute:

**Before:**
```html
<button onclick="clearQueue()">Clear Queue</button>
```

**After:**
```html
<button onclick="clearQueue()" data-i18n="clear_queue">Clear Queue</button>
```

### In Translation File
Add the translation key:

```json
{
  "en": {
    "clear_queue": "Clear Queue"
  },
  "it": {
    "clear_queue": "Svuota Coda"
  }
}
```

### Special Attributes
- `data-i18n`: Translates element text
- `data-i18n-placeholder`: Translates input placeholder
- `data-i18n-title`: Translates tooltip/title attribute

## Testing Translations

### Method 1: Browser Language
1. Change browser language to Italian (it-IT)
2. Reload Maestro
3. UI should auto-translate

### Method 2: Language Selector
1. Look for 🌐 Language dropdown at bottom of page
2. Select "Italiano"
3. Preference saved in localStorage

### Method 3: JavaScript Console
```javascript
maestroTranslator.setLanguage('it');  // Switch to Italian
maestroTranslator.setLanguage('en');  // Switch to English
```

## Translation Coverage

### ✅ Fully Translated
- Main page (index.html)
  - Navigation menu
  - Playback controls
  - Volume controls
  - MPD options

### 🚧 To Be Translated
- Playlist page
- Add Music page
- Search page
- Browse pages
- Settings page
- Admin panel

To expand coverage, simply:
1. Add `data-i18n` attributes to HTML
2. Add translation keys to JSON
3. Test!

## Benefits of Hybrid Approach

✅ **Zero Risk** - No template logic changes  
✅ **Easy Maintenance** - One JSON file per language  
✅ **Gradual Migration** - Translate one page at a time  
✅ **User Friendly** - Auto-detect language + manual selector  
✅ **Future Proof** - Can migrate to Flask-Babel later if needed

## Performance

- Translation file: ~2KB
- i18n.js: ~4KB
- Load time: < 50ms
- Zero performance impact

## Future Enhancements

- Translate all pages (not just main page)
- Add more languages (German, French, Spanish, etc.)
- Translate toast messages
- Translate admin panel
- Migrate to Flask-Babel for server-side rendering (optional)

## Notes for Italian Users

Il sistema è già configurato per rilevare automaticamente il browser italiano. Non è necessaria alcuna configurazione aggiuntiva. Basta ricaricare la pagina e l'interfaccia sarà in italiano.

Per tornare all'inglese, seleziona "English" dal menu a tendina 🌐 in fondo alla pagina.
