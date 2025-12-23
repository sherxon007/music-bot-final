"""Music search service using legal APIs."""
import asyncio
from typing import List, Optional
from urllib.parse import quote

import aiohttp
from fuzzywuzzy import fuzz

from config import Config
from models import Track
from utils import logger


class MusicService:
    """Service for searching music from legal APIs."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Create aiohttp session."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
    
    async def search(self, query: str, limit: int = 20) -> List[Track]:
        """
        Search for tracks using multiple APIs.
        
        Args:
            query: Search query (song name, artist, or both)
            limit: Maximum number of results
        
        Returns:
            List of Track objects sorted by relevance
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Search from multiple sources in parallel
        results = await asyncio.gather(
            self._search_itunes(query, limit),
            self._search_deezer(query, limit),
            return_exceptions=True
        )
        
        # Combine results
        all_tracks: List[Track] = []
        for result in results:
            if isinstance(result, list):
                all_tracks.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Search error: {result}")
        
        # Remove duplicates and sort by relevance
        unique_tracks = self._deduplicate_tracks(all_tracks)
        sorted_tracks = self._sort_by_relevance(unique_tracks, query)
        
        return sorted_tracks[:limit]
    
    async def _search_itunes(self, query: str, limit: int) -> List[Track]:
        """
        Search tracks using iTunes Search API.
        
        API Documentation: https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/
        """
        try:
            url = Config.ITUNES_API_URL
            params = {
                "term": query,
                "media": "music",
                "entity": "song",
                "limit": limit,
                "explicit": "yes"
            }
            # Many APIs like iTunes require a User-Agent to return proper JSON
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            async with self.session.get(url, params=params, headers=headers, timeout=10) as response:
                if response.status != 200:
                    logger.warning(f"iTunes API returned status {response.status}")
                    return []
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if 'javascript' in content_type:
                     # Sometimes iTunes returns javascript for 'alert' if blocked or rate limited
                     text = await response.text()
                     logger.warning(f"iTunes API returned javascript: {text[:100]}")
                     return []

                data = await response.json()
                results = data.get("results", [])
                
                tracks = []
                for item in results:
                    track = Track(
                        title=item.get("trackName", "Unknown"),
                        artist=item.get("artistName", "Unknown"),
                        duration=item.get("trackTimeMillis", 0) // 1000,
                        preview_url=item.get("previewUrl"),
                        audio_url=item.get("previewUrl"),  # iTunes only provides 30s previews
                        album=item.get("collectionName"),
                        artwork_url=item.get("artworkUrl100"),
                        track_id=str(item.get("trackId", "")),
                        source="itunes"
                    )
                    tracks.append(track)
                
                logger.info(f"iTunes API returned {len(tracks)} tracks for query: {query}")
                return tracks
                
        except asyncio.TimeoutError:
            logger.error("iTunes API timeout")
            return []
        except Exception as e:
            logger.error(f"iTunes API error: {e}")
            return []
    
    async def _search_deezer(self, query: str, limit: int) -> List[Track]:
        """
        Search tracks using Deezer API.
        
        API Documentation: https://developers.deezer.com/api
        """
        try:
            url = Config.DEEZER_API_URL
            params = {
                "q": query,
                "limit": limit
            }
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status != 200:
                    logger.warning(f"Deezer API returned status {response.status}")
                    return []
                
                data = await response.json()
                results = data.get("data", [])
                
                tracks = []
                for item in results:
                    # Deezer provides preview URLs (30 seconds)
                    track = Track(
                        title=item.get("title", "Unknown"),
                        artist=item.get("artist", {}).get("name", "Unknown"),
                        duration=item.get("duration", 0),
                        preview_url=item.get("preview"),
                        audio_url=item.get("preview"),
                        album=item.get("album", {}).get("title"),
                        artwork_url=item.get("album", {}).get("cover_medium"),
                        track_id=str(item.get("id", "")),
                        source="deezer"
                    )
                    tracks.append(track)
                
                logger.info(f"Deezer API returned {len(tracks)} tracks for query: {query}")
                return tracks
                
        except asyncio.TimeoutError:
            logger.error("Deezer API timeout")
            return []
        except Exception as e:
            logger.error(f"Deezer API error: {e}")
            return []
    
    def _deduplicate_tracks(self, tracks: List[Track]) -> List[Track]:
        """Remove duplicate tracks based on title and artist similarity."""
        if not tracks:
            return []
        
        unique_tracks = []
        seen_combinations = set()
        
        for track in tracks:
            # Create a normalized key for comparison
            key = f"{track.title.lower().strip()}_{track.artist.lower().strip()}"
            
            # Check if this combination is too similar to existing ones
            is_duplicate = False
            for seen_key in seen_combinations:
                similarity = fuzz.ratio(key, seen_key)
                if similarity > 85:  # 85% similarity threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_tracks.append(track)
                seen_combinations.add(key)
        
        return unique_tracks
    
    def _sort_by_relevance(self, tracks: List[Track], query: str) -> List[Track]:
        """Sort tracks by relevance to the search query."""
        query_lower = query.lower()
        
        def calculate_score(track: Track) -> int:
            """Calculate relevance score for a track."""
            title_lower = track.title.lower()
            artist_lower = track.artist.lower()
            
            # Calculate fuzzy match scores
            title_score = fuzz.partial_ratio(query_lower, title_lower)
            artist_score = fuzz.partial_ratio(query_lower, artist_lower)
            combined_score = fuzz.partial_ratio(query_lower, f"{artist_lower} {title_lower}")
            
            # Prefer exact matches
            exact_bonus = 0
            if query_lower in title_lower or query_lower in artist_lower:
                exact_bonus = 20
            
            # Combined score (weighted average)
            final_score = max(title_score, artist_score, combined_score) + exact_bonus
            
            return final_score
        
        # Sort by score (highest first)
        return sorted(tracks, key=calculate_score, reverse=True)
    
    async def download_audio(self, url: str) -> Optional[bytes]:
        """
        Download audio file from URL.
        
        Args:
            url: Audio file URL
        
        Returns:
            Audio file bytes or None if failed
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    logger.warning(f"Failed to download audio, status: {response.status}")
                    return None
                
                # Check file size
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > Config.MAX_DOWNLOAD_SIZE:
                    logger.warning(f"Audio file too large: {content_length} bytes")
                    return None
                
                audio_data = await response.read()
                logger.info(f"Downloaded audio: {len(audio_data)} bytes")
                return audio_data
                
        except asyncio.TimeoutError:
            logger.error("Audio download timeout")
            return None
        except Exception as e:
            logger.error(f"Audio download error: {e}")
            return None
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
