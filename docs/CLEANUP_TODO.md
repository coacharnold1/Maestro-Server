# Cleanup and polish todos (Charts + app)

Use this checklist to quickly clean up debug bits and small polish items when ready.

## Charts page (templates/charts.html)
- [ ] Remove or gate temporary [DEBUG] console logs under a `const DEBUG = false;` flag.
- [ ] Standardize success/error handling: ensure every fetch expects `{ status, message }` and shows a toast.
- [ ] Add a small dropdown to Albums with:
  - [ ] "➕ Add Album" (existing)
  - [ ] "⏯️ Clear & Play Album" → POST /clear_and_add_album with `{ artist, album }` JSON.
- [ ] Persist the selected period (7day/1month/…) to `localStorage` and restore on load.
- [ ] Optional: show a subtle confirmation badge on the album row after success.

## Backend (app.py)
- [ ] Ensure /add_album_to_playlist always returns JSON for JSON requests. Current behavior is correct; double-check edge paths.
- [ ] Consider unifying JSON response shape across endpoints to `{ status: 'success'|'error', message, data? }`.
- [ ] Keep the robust album matching fallbacks, but add a simple debug toggle to reduce log noise outside debugging.
- [ ] Deduplicate multiple SocketIO `@socketio.on('connect')` handlers (there are duplicates) to a single function.
- [ ] Optional: extract Last.fm helpers into a small module (keep APIs the same) for readability.

## Theming and CSS
- [ ] Move repeated inline styles from templates into shared CSS (playback controls, dropdowns).
- [ ] Verify light/high-contrast overrides cover dropdowns and messages consistently.

## Reliability / tests (lightweight)
- [ ] Add a tiny test harness or script to call `add_album_to_playlist` against a few tricky cases (albumartist vs artist, punctuation, regional editions).
- [ ] Log a single summary line per request in non-debug mode (artist, album, matched tracks count).

## Docs
- [ ] Note the backup process and retention behavior already in place; link to VERSION snapshot section when updated.
- [ ] Add a short "Troubleshooting Charts" section: Last.fm connection, API key, and typical 404 causes.

Notes:
- These are low-risk; they shouldn’t change public behavior, only polish.
- When you’re ready, we can tackle these in one pass and verify by quick manual checks from Charts and Playlist pages.
