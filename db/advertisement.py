"""Advertisement model and operations."""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import (
    BigInteger, String, DateTime, Boolean, Integer, Text, select
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base


class AdType(str, Enum):
    """Advertisement type enum."""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"


class Advertisement(Base):
    """Advertisement model."""
    
    __tablename__ = "advertisements"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ad_type: Mapped[str] = mapped_column(String(20), default=AdType.TEXT.value)
    text: Mapped[str] = mapped_column(Text, nullable=True)
    file_id: Mapped[str] = mapped_column(String(255), nullable=True)
    button_text: Mapped[str] = mapped_column(String(100), nullable=True)
    button_url: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    show_after_tracks: Mapped[int] = mapped_column(Integer, default=5)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    def __repr__(self) -> str:
        return f"<Ad(id={self.id}, type={self.ad_type}, active={self.is_active})>"


class AdRepository:
    """Repository for advertisement operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_ad(self, ad_id: int) -> Optional[Advertisement]:
        """Get advertisement by ID."""
        result = await self.session.execute(
            select(Advertisement).where(Advertisement.id == ad_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_ads(self) -> List[Advertisement]:
        """Get all active advertisements."""
        result = await self.session.execute(
            select(Advertisement)
            .where(Advertisement.is_active == True)
            .order_by(Advertisement.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_random_active_ad(self) -> Optional[Advertisement]:
        """Get random active advertisement."""
        ads = await self.get_active_ads()
        if ads:
            import random
            return random.choice(ads)
        return None
    
    async def create_ad(
        self,
        ad_type: str,
        text: Optional[str] = None,
        file_id: Optional[str] = None,
        button_text: Optional[str] = None,
        button_url: Optional[str] = None,
        show_after_tracks: int = 5
    ) -> Advertisement:
        """Create new advertisement."""
        ad = Advertisement(
            ad_type=ad_type,
            text=text,
            file_id=file_id,
            button_text=button_text,
            button_url=button_url,
            show_after_tracks=show_after_tracks,
            is_active=True
        )
        self.session.add(ad)
        await self.session.commit()
        await self.session.refresh(ad)
        return ad
    
    async def update_ad(
        self,
        ad_id: int,
        text: Optional[str] = None,
        button_text: Optional[str] = None,
        button_url: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Advertisement]:
        """Update advertisement."""
        ad = await self.get_ad(ad_id)
        if ad:
            if text is not None:
                ad.text = text
            if button_text is not None:
                ad.button_text = button_text
            if button_url is not None:
                ad.button_url = button_url
            if is_active is not None:
                ad.is_active = is_active
            ad.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(ad)
        return ad
    
    async def delete_ad(self, ad_id: int) -> bool:
        """Delete advertisement."""
        ad = await self.get_ad(ad_id)
        if ad:
            await self.session.delete(ad)
            await self.session.commit()
            return True
        return False
    
    async def increment_impressions(self, ad_id: int) -> None:
        """Increment advertisement impressions."""
        ad = await self.get_ad(ad_id)
        if ad:
            ad.impressions += 1
            await self.session.commit()
    
    async def increment_clicks(self, ad_id: int) -> None:
        """Increment advertisement clicks."""
        ad = await self.get_ad(ad_id)
        if ad:
            ad.clicks += 1
            await self.session.commit()
    
    async def get_all_ads(self) -> List[Advertisement]:
        """Get all advertisements."""
        result = await self.session.execute(
            select(Advertisement).order_by(Advertisement.created_at.desc())
        )
        return list(result.scalars().all())
