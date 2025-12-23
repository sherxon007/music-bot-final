"""FastSaver API service for social media and music downloads."""
import asyncio
from typing import Optional, Dict, List
import aiohttp

from config import Config
from utils import logger


class FastSaverAPI:
    """Service for downloading media using FastSaver API."""
    
    def __init__(self):
        """Initialize FastSaver API service."""
        self.api_url = Config.FASTSAVER_API_URL
        self.api_token = Config.FASTSAVER_API_TOKEN
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Create aiohttp session."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session."""
        await self.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication."""
        return {
            'X-Api-Key': self.api_token
        }
    
    async def fetch(self, url: str) -> Optional[Dict]:
        """
        Fetch media info from URL using FastSaver API.
        
        Supports: Instagram, YouTube, TikTok, Facebook, Twitter, etc.
        
        Args:
            url: Social media URL
            
        Returns:
            Dict with media info or None if failed
        """
        if not self.api_token:
            logger.error("FastSaver API token not configured")
            return None
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            params = {'url': url}
            headers = self._get_headers()
            
            async with self.session.get(
                f"{self.api_url}/v1/fetch",
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"FastSaver API error {response.status}: {text[:200]}")
                    return None
                
                data = await response.json()
                return data
                
        except asyncio.TimeoutError:
            logger.error("FastSaver API timeout")
            return None
        except Exception as e:
            logger.error(f"FastSaver API error: {e}")
            return None
    
    async def download_media_from_url(self, download_url: str) -> Optional[bytes]:
        """
        Download media file from direct URL.
        
        Args:
            download_url: Direct download URL
            
        Returns:
            Media bytes or None if failed
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Add headers to bypass 403 errors from Instagram/Facebook CDN
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.instagram.com/',
                'Origin': 'https://www.instagram.com'
            }
            
            async with self.session.get(
                download_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    logger.error(f"Media download error: {response.status}")
                    return None
                
                media_data = await response.read()
                logger.info(f"Downloaded media: {len(media_data)} bytes")
                return media_data
                
        except asyncio.TimeoutError:
            logger.error("Media download timeout")
            return None
        except Exception as e:
            logger.error(f"Media download error: {e}")
            return None
    
    def extract_platform(self, url: str) -> Optional[str]:
        """
        Detect platform from URL.
        
        Returns: 'youtube', 'instagram', 'tiktok', 'facebook', 'twitter', etc.
        """
        url_lower = url.lower()
        
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
            return 'facebook'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'pinterest.com' in url_lower:
            return 'pinterest'
        elif 'threads.net' in url_lower:
            return 'threads'
        elif 'snapchat.com' in url_lower:
            return 'snapchat'
        
        return None
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
