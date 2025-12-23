"""User database model and operations."""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, DateTime, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base


class User(Base):
    """User model for storing user preferences."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    language: Mapped[str] = mapped_column(String(2), default="en")
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
        return f"<User(id={self.id}, language={self.language})>"


class UserRepository:
    """Repository for user operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, user_id: int, language: str = "en") -> User:
        """Create a new user."""
        user = User(id=user_id, language=language)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_or_create_user(self, user_id: int) -> User:
        """Get existing user or create new one."""
        user = await self.get_user(user_id)
        if not user:
            user = await self.create_user(user_id)
        return user
    
    async def update_language(self, user_id: int, language: str) -> Optional[User]:
        """Update user language preference."""
        user = await self.get_user(user_id)
        if user:
            user.language = language
            user.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(user)
        return user
