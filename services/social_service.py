import aiohttp
from typing import Optional, Dict
from config import Config
import logging

logger = logging.getLogger(__name__)

class SocialDownloaderService:
    """Service to handle social media downloads (Instagram, TikTok, FB, etc.) using FastSaver /fetch."""
    
    @staticmethod
    def is_supported_url(url: str) -> bool:
        """Check if URL is supported by Social Downloader."""
        domains = [
            'instagram.com', 'tiktok.com', 'pinterest.com', 
            'facebook.com', 'fb.watch', 'twitter.com', 'x.com',
            'youtube.com/shorts', 'youtu.be' 
        ]
        return any(d in url.lower() for d in domains)

    @staticmethod
    async def fetch_media(url: str) -> Optional[Dict]:
        """
        Fetch media using FastSaver /fetch endpoint.
        Cost: ~1.5 credits (varies by platform).
        """
        api_url = f"{Config.FASTSAVER_API_URL}/v1/fetch"
        params = {'url': url}
        headers = {'X-Api-Key': Config.FASTSAVER_API_TOKEN}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"FastSaver /fetch error: {response.status}")
                        return None
                    
                    data = await response.json()
                    if not data.get('ok'):
                        logger.error(f"FastSaver /fetch failed: {data}")
                        return None
                    
                    return data
        except Exception as e:
            logger.error(f"Social download exception: {e}")
            return None
