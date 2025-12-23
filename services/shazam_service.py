"""Shazam music identification service using FastSaver API."""
import asyncio
from typing import Optional, Dict
import aiohttp
import logging

from config import Config

logger = logging.getLogger(__name__)

class ShazamService:
    """Service for identifying music using Shazam via FastSaver API."""
    
    @staticmethod
    async def identify_music(audio_bytes: bytes) -> Optional[Dict]:
        """
        Identify music from audio bytes using Shazam.
        
        Args:
            audio_bytes: Audio file bytes (max 50MB)
            
        Returns:
            Dict containing:
            - title
            - artist
            - results: List of YouTube videos (We need video_id from here)
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Prepare multipart form data
                data = aiohttp.FormData()
                data.add_field('file', 
                             audio_bytes, 
                             filename='file', # Generic name
                             content_type='application/octet-stream') # Generic stream
                
                headers = {
                    'X-Api-Key': Config.FASTSAVER_API_TOKEN
                }
                
                # Timeout is crucial here as upload might take time
                async with session.post(
                    f"{Config.FASTSAVER_API_URL}/v1/shazam/identify",
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"Shazam API error {response.status}: {text}")
                        return None
                    
                    result = await response.json()
                    
                    if not result.get('ok'):
                        logger.error(f"Shazam identification failed: {result}")
                        return None
                    
                    # Log success
                    title = result.get('title', 'Unknown')
                    logger.info(f"Shazam identified: {title}")
                    
                    return result
                    
        except asyncio.TimeoutError:
            logger.error("Shazam API timeout")
            return None
        except Exception as e:
            logger.error(f"Shazam identification error: {e}")
            return None
