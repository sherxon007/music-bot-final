"""YouTube service using both Local Search (backup) and FastSaver API (download)."""
import logging
import aiohttp
import re
from config import Config

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service for handling YouTube search and audio retrieval."""
    
    @staticmethod
    async def get_video_id(query: str) -> str | None:
        """
        Search for a video using direct HTML parsing (No external libs).
        This avoids 'proxies' error in youtubesearchpython.
        """
        try:
            logger.info(f"Searching YouTube (HTML) for: {query}")
            
            # Simple search mechanism
            from urllib.parse import quote
            async with aiohttp.ClientSession() as session:
                url = f"https://www.youtube.com/results?search_query={quote(query)}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        logger.error(f"YouTube search failed: {resp.status}")
                        return None
                    html = await resp.text()
            
            # Find first video ID using Regex
            video_ids = re.findall(r"\"videoId\":\"([a-zA-Z0-9_-]{11})\"", html)
            
            if video_ids:
                # Filter out duplicates and take first unique one
                unique_ids = []
                seen = set()
                for vid in video_ids:
                    if vid not in seen:
                        unique_ids.append(vid)
                        seen.add(vid)
                
                if unique_ids:
                    video_id = unique_ids[0]
                    logger.info(f"Found video ID (Regex): {video_id}")
                    return video_id
            
            logger.warning("No video ID found in search results")
            return None
            
        except Exception as e:
            logger.error(f"Local search error: {e}")
            return None

    @staticmethod
    async def get_audio_file_id(video_id: str) -> str | None:
        """
        Get Telegram file_id for audio using FastSaver API.
        Cost: 7 credits.
        """
        api_url = f"{Config.FASTSAVER_API_URL}/v1/youtube/audio/tg-bot"
        headers = {
            'X-Api-Key': Config.FASTSAVER_API_TOKEN,
            'Content-Type': 'application/json'
        }
        payload = {
            'video_id': video_id,
            'bot_username': Config.BOT_USERNAME
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload, headers=headers, timeout=60) as response:
                    if response.status != 200:
                        logger.error(f"FastSaver audio error: {response.status}")
                        return None
                    
                    data = await response.json()
                    if data.get('ok') and data.get('file_id'):
                        return data['file_id']
                    else:
                        logger.error(f"FastSaver failed to return file_id: {data}")
                        return None
        except Exception as e:
            logger.error(f"FastSaver API exception: {e}")
            return None
