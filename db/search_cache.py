"""Search cache for storing recent search results."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import asdict
import json

from sqlalchemy import BigInteger, String, DateTime, Text, Integer, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base
from models import Track


class SearchCache(Base):
    """Cache model for storing search results."""
    
    __tablename__ = "search_cache"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    query: Mapped[str] = mapped_column(String(255))
    results: Mapped[str] = mapped_column(Text)  # JSON serialized tracks
    current_offset: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    
    def __repr__(self) -> str:
        return f"<SearchCache(user_id={self.user_id}, query={self.query})>"


class SearchCacheRepository:
    """Repository for search cache operations."""
    
    CACHE_EXPIRY_HOURS = 1
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_search(
        self, 
        user_id: int, 
        query: str, 
        tracks: List[Track]
    ) -> SearchCache:
        """Save search results to cache."""
        # Delete old cache for this user
        await self.delete_user_cache(user_id)
        
        # Serialize tracks to JSON
        tracks_json = json.dumps([
            {
                "title": t.title,
                "artist": t.artist,
                "duration": t.duration,
                "preview_url": t.preview_url,
                "audio_url": t.audio_url,
                "album": t.album,
                "artwork_url": t.artwork_url,
                "track_id": t.track_id,
                "source": t.source
            }
            for t in tracks
        ])
        
        cache = SearchCache(
            user_id=user_id,
            query=query,
            results=tracks_json,
            current_offset=0
        )
        
        self.session.add(cache)
        await self.session.commit()
        await self.session.refresh(cache)
        return cache
    
    async def get_user_cache(self, user_id: int) -> Optional[SearchCache]:
        """Get latest search cache for user."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.CACHE_EXPIRY_HOURS)
        
        result = await self.session.execute(
            select(SearchCache)
            .where(
                SearchCache.user_id == user_id,
                SearchCache.created_at > cutoff_time
            )
            .order_by(SearchCache.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_cached_tracks(self, user_id: int) -> Optional[List[Track]]:
        """Get cached tracks for user."""
        cache = await self.get_user_cache(user_id)
        if not cache:
            return None
        
        # Deserialize JSON to Track objects
        tracks_data = json.loads(cache.results)
        return [Track(**track_data) for track_data in tracks_data]
    
    async def update_offset(self, user_id: int, offset: int) -> None:
        """Update current offset for pagination."""
        cache = await self.get_user_cache(user_id)
        if cache:
            cache.current_offset = offset
            await self.session.commit()
    
    async def get_offset(self, user_id: int) -> int:
        """Get current offset for user."""
        cache = await self.get_user_cache(user_id)
        return cache.current_offset if cache else 0
    
    async def delete_user_cache(self, user_id: int) -> None:
        """Delete all cache entries for user."""
        await self.session.execute(
            select(SearchCache).where(SearchCache.user_id == user_id)
        )
        # Delete old entries
        result = await self.session.execute(
            select(SearchCache).where(SearchCache.user_id == user_id)
        )
        caches = result.scalars().all()
        for cache in caches:
            await self.session.delete(cache)
        await self.session.commit()
    
    async def cleanup_old_cache(self) -> None:
        """Clean up expired cache entries."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.CACHE_EXPIRY_HOURS)
        
        result = await self.session.execute(
            select(SearchCache).where(SearchCache.created_at < cutoff_time)
        )
        caches = result.scalars().all()
        
        for cache in caches:
            await self.session.delete(cache)
        
        await self.session.commit()
