# 🎵 Genius API Setup Guide

## What is Genius API?

Genius.com is a music database with comprehensive lyrics and artist information. The free Genius API allows you to search for lyrics legally and display them in your app.

---

## Step-by-Step Setup

### 1. Create a Genius Account
- Go to https://genius.com
- Sign up for a free account (if you don't have one)
- Takes 2 minutes

### 2. Create an API Client
- Visit https://genius.com/api-clients
- Click **"New API Client"**
- Fill in the form:
  - **App Name**: "Maestro" (or whatever you want)
  - **App Website**: "http://192.168.1.209:5003" (your server)
  - Click **"Create"**

### 3. Get Your Credentials
On the next page, you'll see:
- **Client ID** - Copy this
- **Client Secret** - Copy this

These are what you need for Maestro!

### 4. Save in Maestro Settings
- Go to http://192.168.1.209:5003/settings
- Scroll to **"Genius API (Lyrics)"** section
- Paste your **Client ID** 
- Paste your **Client Secret**
- Click **"Save Settings"**
- Click **"🧪 Test Genius API"** to verify it works

### 5. Done! 🎉
- Click the **🎵 Lyrics** button on the player
- Real lyrics will now appear!

---

## Rate Limits

Genius free API allows:
- **10,000 requests per hour** per IP address
- This is plenty for a personal music player
- Lyrics are cached, so repeated requests are quick

---

## Troubleshooting

### "Test Failed" message?
- Double-check Client ID and Secret are copied correctly
- Make sure there are no extra spaces
- Genius account needs to be created first

### Still no lyrics?
- Some songs may not be in Genius database
- Try searching on genius.com manually for that song
- Classics like "Hey Jude" should work

### "Rate limited"?
- Wait 1 hour before making more requests
- Very unlikely for personal use

---

## Security Notes

✅ Your Client Secret is stored securely in `settings.json` (file permissions: 0600)
✅ Genius API doesn't require authentication tokens, just Client ID
✅ All requests go directly to Genius (no intermediary)
✅ You can revoke access anytime at genius.com/api-clients

---

**Questions?** Check the Genius API docs: https://docs.genius.com/
