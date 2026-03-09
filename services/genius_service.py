"""
GeniusService - Encapsulates Genius API integration for lyrics lookup.

Handles:
- Genius API search and lyrics scraping
- Page scraping with BeautifulSoup and regex fallback
- Lyrics cleaning and formatting
- Instrumental track detection
"""

import logging
import requests
import re
import html
from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Default HTTP headers for outbound requests
DEFAULT_HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Instrumental keywords to detect non-lyrical tracks
INSTRUMENTAL_KEYWORDS = [
    'instrumental',
    'theme',
    'interlude',
    'intro',
    'outro',
    'remix',
    'version',
    'medley',
    'suite',
    'concerto',
    'symphony',
    'sonata',
    'prelude',
    'etude',
    'fugue',
    'nocturne',
]


class GeniusService:
    """
    Service for Genius lyrics integration.
    
    Provides:
    - Lyrics search and fetching from Genius.com
    - Page scraping with BeautifulSoup and regex fallback
    - Instrumental track detection
    - Lyrics cleaning and formatting
    """
    
    GENIUS_SEARCH_URL = "https://genius.com/api/search/song"
    
    def __init__(self):
        """Initialize GeniusService."""
        logger.info("GeniusService initialized")
    
    def get_lyrics(self, artist: str, title: str) -> Optional[str]:
        """
        Fetch lyrics for a track.
        
        Args:
            artist: Artist name
            title: Track title
            
        Returns:
            Lyrics string or None if not found/error
        """
        if not artist or not title:
            logger.warning(f"Missing artist or title for lyrics search")
            return None
        
        # Check if likely instrumental
        if self.is_likely_instrumental(title):
            logger.debug(f"Track appears instrumental: {artist} - {title}")
            return None
        
        # Try to fetch from Genius
        try:
            lyrics = self._fetch_lyrics_genius(artist, title)
            return lyrics
        except Exception as e:
            logger.error(f"Error fetching lyrics for {artist} - {title}: {e}")
            return None
    
    def is_likely_instrumental(self, title: str) -> bool:
        """
        Detect if track title suggests it's instrumental.
        
        Args:
            title: Track title
            
        Returns:
            True if appears to be instrumental, False otherwise
        """
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in INSTRUMENTAL_KEYWORDS)
    
    def test_connection(self, artist: str = '', title: str = '') -> tuple[bool, str]:
        """
        Test Genius API connectivity.
        
        Args:
            artist: Artist name (default: The Beatles)
            title: Track title (default: Hey Jude)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        artist = artist or 'The Beatles'
        title = title or 'Hey Jude'
        
        try:
            lyrics = self.get_lyrics(artist, title)
            if lyrics:
                snippet = (lyrics[:160] + '...') if len(lyrics) > 160 else lyrics
                return (True, f"Success! Sample lyrics: {snippet}")
            else:
                return (False, f"No lyrics found for {artist} - {title}. Try another song.")
        except Exception as e:
            return (False, f"Connection failed: {e}")
    
    def _fetch_lyrics_genius(self, artist: str, title: str) -> Optional[str]:
        """
        Search Genius API and scrape lyrics from matching song page.
        
        Args:
            artist: Artist name
            title: Track title
            
        Returns:
            Lyrics string or None if not found
        """
        try:
            query = f"{artist} {title}".strip()
            if not query:
                return None
            
            # Search Genius API
            params = {'q': query}
            resp = requests.get(
                self.GENIUS_SEARCH_URL,
                params=params,
                timeout=8,
                headers=DEFAULT_HTTP_HEADERS
            )
            resp.raise_for_status()
            data = resp.json()
            
            sections = data.get('response', {}).get('sections', [])
            song_section = next((s for s in sections if s.get('type') == 'song'), None)
            hits = song_section.get('hits', []) if song_section else []
            
            if not hits:
                logger.debug(f"No Genius results for: {artist} - {title}")
                return None
            
            # Try first few hits
            for hit in hits[:5]:  # Limit to first 5 results
                result = hit.get('result', {})
                url = result.get('url')
                if not url:
                    continue
                
                lyrics = self._scrape_genius_page(url)
                if lyrics:
                    logger.info(f"Found lyrics via Genius: {artist} - {title} ({len(lyrics)} chars)")
                    return lyrics
            
            logger.debug(f"No lyrics found for any Genius results: {artist} - {title}")
            return None
            
        except Exception as e:
            logger.error(f"Genius search error: {e}")
            return None
    
    def _scrape_genius_page(self, url: str) -> Optional[str]:
        """
        Scrape lyrics from a Genius song page using BeautifulSoup.
        
        Args:
            url: Genius song page URL
            
        Returns:
            Lyrics string or None on error
        """
        try:
            resp = requests.get(url, timeout=8, headers=DEFAULT_HTTP_HEADERS)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find all containers with data-lyrics-container="true"
            containers = soup.find_all('div', {'data-lyrics-container': 'true'})
            if not containers:
                logger.debug(f"No lyrics containers found on {url}")
                return self._scrape_genius_page_regex(url)
            
            parts = []
            for container in containers:
                # Extract all text from container, preserving line breaks
                text_parts = []
                for element in container.descendants:
                    if isinstance(element, str):
                        text = element.strip()
                        if text:
                            text_parts.append(text)
                    elif element.name == 'br':
                        text_parts.append('\n')
                
                # Join and clean up
                block_text = ''.join(text_parts)
                block_text = re.sub(r'\n{3,}', '\n\n', block_text).strip()
                
                if block_text:
                    parts.append(block_text)
            
            if not parts:
                logger.debug(f"No lyric text extracted from {url}")
                return None
            
            lyrics = "\n\n".join(parts)
            
            # Clean up common metadata junk
            lyrics = self._clean_genius_lyrics(lyrics)
            
            # Final cleanup
            lyrics = re.sub(r'\n{3,}', '\n\n', lyrics).strip()
            
            if not lyrics:
                return None
            
            logger.debug(f"Scraped {len(lyrics)} chars from {url}")
            return lyrics
            
        except Exception as e:
            logger.debug(f"BeautifulSoup scrape error (fallback to regex): {e}")
            return self._scrape_genius_page_regex(url)
    
    def _scrape_genius_page_regex(self, url: str) -> Optional[str]:
        """
        Fallback regex-based scraper if BeautifulSoup fails.
        
        Args:
            url: Genius song page URL
            
        Returns:
            Lyrics string or None on error
        """
        try:
            resp = requests.get(url, timeout=8, headers=DEFAULT_HTTP_HEADERS)
            resp.raise_for_status()
            html_text = resp.text
            
            # Find lyrics containers using regex
            pattern = r'<div[^>]*data-lyrics-container="true"[^>]*>(.*?)</div(?=>)'
            containers = re.findall(pattern, html_text, flags=re.DOTALL)
            
            if not containers:
                logger.debug(f"No regex containers found on {url}")
                return None
            
            parts = []
            for block in containers:
                block = block.replace('<br/>', '\n').replace('<br>', '\n')
                block = re.sub(r'<[^>]+>', '', block)
                block = html.unescape(block)
                block = block.strip()
                if block:
                    parts.append(block)
            
            if not parts:
                return None
            
            lyrics = "\n\n".join(parts)
            lyrics = re.sub(r'\n{3,}', '\n\n', lyrics).strip()
            
            return lyrics or None
            
        except Exception as e:
            logger.error(f"Regex scrape error: {e}")
            return None
    
    def _clean_genius_lyrics(self, lyrics: str) -> Optional[str]:
        """
        Remove common metadata junk from Genius lyrics.
        
        Strips contributor info, translations, descriptions, etc.
        Preserves actual lyrics including verses, choruses, etc.
        
        Args:
            lyrics: Raw lyrics text from Genius
            
        Returns:
            Cleaned lyrics or None if empty
        """
        lines = lyrics.split('\n')
        cleaned_lines = []
        
        # Patterns to completely remove lines
        junk_patterns = [
            r'^\d+\s+Contributors?$',  # "71 Contributors"
            r'^Translations?$',  # "Translations"
            r'^(Español|Italiano|Português|Français|Deutsch|中文|日本語)$',  # Language names
            r'^(Read More|See full lyrics|Get the lyrics|Lyrics)$',  # Common metadata
            r'^\[.*?\]\s*Lyrics.*$',  # "[Song Name] Lyrics"
        ]
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if this line is pure junk
            is_junk = any(re.match(pattern, line_stripped) for pattern in junk_patterns)
            
            # Skip long descriptions that aren't lyrics
            is_long_description = (
                len(line_stripped) > 100 and
                not re.match(r'^\[', line_stripped) and
                'believe' not in line_stripped.lower() and
                'dream' not in line_stripped.lower()
            )
            
            if not is_junk and not is_long_description:
                cleaned_lines.append(line)
        
        # Join and clean up excess blank lines
        result = '\n'.join(cleaned_lines).strip()
        result = re.sub(r'\n{3,}', '\n\n', result).strip()
        
        return result if result else None
