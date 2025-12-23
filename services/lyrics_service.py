from lyricsgenius import Genius
from config import Config
import logging

logger = logging.getLogger(__name__)

class LyricsService:
    _genius = None

    @classmethod
    def get_client(cls):
        if not cls._genius:
            # Public access token (Free tier is enough usually, but strictly speaking we should use an API Key)
            # However, lyricsgenius works well even with just a simple setup or scraping mode.
            # But to be stable, we need a token.
            # I will use a generic free token or scraper logic.
            # Actually, lyricsgenius requires a token.
            # Let's use a standard method or ask user to provide one if they have.
            # Since user wants "Saving Credit", Genius is best.
            # I'll initializing with a placeholder token that works for public scraping or 
            # we can try to find lyrics without token if library supports, but it usually needs one.
            # Let's try to scrape directly if possible or used a known public key.
            # Wait, 100% free way without key?
            # Let's use `BeautifulSoup` to scrape Genius URL directly if we don't have a key.
            # But `lyricsgenius` is easier.
            
            # Let's use a Dummy token if the user hasn't provided one, but it might fail.
            # Better approach: Direct scraping for maximum "Free".
            pass
        return cls._genius

    @staticmethod
    async def get_lyrics(artist: str, title: str) -> str:
        """Get lyrics for a song using direct scraping to avoid API keys."""
        import aiohttp
        from bs4 import BeautifulSoup
        import re

        query = f"{artist} {title} lyrics"
        search_url = "https://genius.com/api/search/multi"
        
        # We need to act like a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. Search for the song page on Genius
                # We can cheat and use their internal API or just search on Google.
                # Let's use their public API endpoint which sometimes works without auth or just Google Search.
                # Actually, simplest, most robust way without API Key:
                # Search on DuckDuckGo or Google -> find genius link -> scrape.
                
                # Let's try searching via simple HTML search on genius.com/search
                async with session.get(f"https://genius.com/search?q={query}", headers=headers) as resp:
                     html = await resp.text()
                
                # We need to parse this HTML to find the song link.
                # Genius HTML is complex. 
                # Let's try `lyricsgenius` library but it NEEDS a token. 
                
                # Alternative: Use `requests` to search?
                # Let's try to construct the URL directly: artist-song-lyrics
                # e.g. Eminem - Till I Collapse -> https://genius.com/Eminem-till-i-collapse-lyrics
                
                def format_for_url(s):
                    return re.sub(r'[^a-zA-Z0-9\s-]', '', s).replace(' ', '-').lower()
                
                url_slug = f"{format_for_url(artist)}-{format_for_url(title)}-lyrics"
                direct_url = f"https://genius.com/{url_slug}"
                
                logger.info(f"Trying direct Genius URL: {direct_url}")
                
                async with session.get(direct_url, headers=headers) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Genius Lyrics Containers (they change these classes often)
                        lyrics_containers = soup.select('div[data-lyrics-container="true"]')
                        
                        if lyrics_containers:
                            lyrics_text = "\n".join([c.get_text(separator="\n") for c in lyrics_containers])
                            return lyrics_text
                            
            return None
            
        except Exception as e:
            logger.error(f"Lyrics scrape error: {e}")
            return None
