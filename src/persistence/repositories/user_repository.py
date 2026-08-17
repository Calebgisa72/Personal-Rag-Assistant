import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.interfaces import IUserRepository
from domain.entities import UserEntity
from infrastructure.database.models import User

class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: UserEntity) -> UserEntity:
        db_user = User(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            hashed_password=user.hashed_password,
            profile_pic=user.profile_pic,
            is_active=user.is_active,
            is_superuser=user.is_superuser
        )
        self.session.add(db_user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[UserEntity]:
        stmt = select(User).where(User.user_id == user_id)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return UserEntity(
            user_id=db_user.user_id,
            email=db_user.email,
            username=db_user.username,
            hashed_password=db_user.hashed_password,
            profile_pic=db_user.profile_pic,
            is_active=db_user.is_active,
            is_superuser=db_user.is_superuser,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )

    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return UserEntity(
            user_id=db_user.user_id,
            email=db_user.email,
            username=db_user.username,
            hashed_password=db_user.hashed_password,
            profile_pic=db_user.profile_pic,
            is_active=db_user.is_active,
            is_superuser=db_user.is_superuser,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )
