"""Statistics tracking model and operations."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import (
    BigInteger, String, DateTime, Integer, select, func
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base


class UserActivity(Base):
    """User activity tracking."""
    
    __tablename__ = "user_activities"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    action: Mapped[str] = mapped_column(String(50))  # search, download, inline_query
    query: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<UserActivity(user_id={self.user_id}, action={self.action})>"


class StatisticsRepository:
    """Repository for statistics operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_activity(
        self,
        user_id: int,
        action: str,
        query: Optional[str] = None
    ) -> UserActivity:
        """Log user activity."""
        activity = UserActivity(
            user_id=user_id,
            action=action,
            query=query
        )
        self.session.add(activity)
        await self.session.commit()
        return activity
    
    async def get_total_users(self) -> int:
        """Get total number of unique users."""
        from .user import User
        result = await self.session.execute(
            select(func.count(User.id))
        )
        return result.scalar_one()
    
    async def get_active_users_today(self) -> int:
        """Get number of active users today."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(func.distinct(UserActivity.user_id)))
            .where(UserActivity.created_at >= today)
        )
        return result.scalar_one()
    
    async def get_active_users_week(self) -> int:
        """Get number of active users this week."""
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await self.session.execute(
            select(func.count(func.distinct(UserActivity.user_id)))
            .where(UserActivity.created_at >= week_ago)
        )
        return result.scalar_one()
    
    async def get_total_searches(self) -> int:
        """Get total number of searches."""
        result = await self.session.execute(
            select(func.count(UserActivity.id))
            .where(UserActivity.action == 'search')
        )
        return result.scalar_one()
    
    async def get_total_downloads(self) -> int:
        """Get total number of downloads."""
        result = await self.session.execute(
            select(func.count(UserActivity.id))
            .where(UserActivity.action == 'download')
        )
        return result.scalar_one()
    
    async def get_searches_today(self) -> int:
        """Get searches today."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(UserActivity.id))
            .where(
                UserActivity.action == 'search',
                UserActivity.created_at >= today
            )
        )
        return result.scalar_one()
    
    async def get_downloads_today(self) -> int:
        """Get downloads today."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(UserActivity.id))
            .where(
                UserActivity.action == 'download',
                UserActivity.created_at >= today
            )
        )
        return result.scalar_one()
    
    async def get_top_queries(self, limit: int = 10) -> List[Dict]:
        """Get top search queries."""
        result = await self.session.execute(
            select(
                UserActivity.query,
                func.count(UserActivity.id).label('count')
            )
            .where(
                UserActivity.action == 'search',
                UserActivity.query.isnot(None)
            )
            .group_by(UserActivity.query)
            .order_by(func.count(UserActivity.id).desc())
            .limit(limit)
        )
        
        return [
            {"query": row[0], "count": row[1]}
            for row in result.all()
        ]
    
    async def get_new_users_today(self) -> int:
        """Get number of new users today."""
        from .user import User
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(User.id))
            .where(User.created_at >= today)
        )
        return result.scalar_one()
    
    async def get_new_users_week(self) -> int:
        """Get number of new users this week."""
        from .user import User
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await self.session.execute(
            select(func.count(User.id))
            .where(User.created_at >= week_ago)
        )
        return result.scalar_one()
    
    async def get_language_distribution(self) -> List[Dict]:
        """Get user language distribution."""
        from .user import User
        result = await self.session.execute(
            select(
                User.language,
                func.count(User.id).label('count')
            )
            .group_by(User.language)
            .order_by(func.count(User.id).desc())
        )
        
        return [
            {"language": row[0], "count": row[1]}
            for row in result.all()
        ]
    
    async def cleanup_old_activities(self, days: int = 30) -> None:
        """Delete activities older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(UserActivity).where(UserActivity.created_at < cutoff_date)
        )
        activities = result.scalars().all()
        
        for activity in activities:
            await self.session.delete(activity)
        
        await self.session.commit()
