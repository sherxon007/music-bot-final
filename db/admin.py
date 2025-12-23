"""Admin user model and operations."""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import BigInteger, String, DateTime, Boolean, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base


class Admin(Base):
    """Admin user model."""
    
    __tablename__ = "admins"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    
    def __repr__(self) -> str:
        return f"<Admin(id={self.id}, username={self.username})>"


class AdminRepository:
    """Repository for admin operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_admin(self, user_id: int) -> Optional[Admin]:
        """Get admin by ID."""
        result = await self.session.execute(
            select(Admin).where(Admin.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        admin = await self.get_admin(user_id)
        return admin is not None
    
    async def is_super_admin(self, user_id: int) -> bool:
        """Check if user is super admin."""
        admin = await self.get_admin(user_id)
        return admin is not None and admin.is_super_admin
    
    async def add_admin(
        self, 
        user_id: int, 
        username: Optional[str] = None,
        is_super_admin: bool = False
    ) -> Admin:
        """Add new admin."""
        admin = Admin(
            id=user_id,
            username=username,
            is_super_admin=is_super_admin
        )
        self.session.add(admin)
        await self.session.commit()
        await self.session.refresh(admin)
        return admin
    
    async def remove_admin(self, user_id: int) -> bool:
        """Remove admin."""
        admin = await self.get_admin(user_id)
        if admin:
            await self.session.delete(admin)
            await self.session.commit()
            return True
        return False
    
    async def get_all_admins(self) -> List[Admin]:
        """Get all admins."""
        result = await self.session.execute(select(Admin))
        return list(result.scalars().all())
