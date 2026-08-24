from fastapi import HTTPException, status
from pydantic import EmailStr
import uuid
from jose import jwt, JWTError

from persistence.uow import UnitOfWork
from domain.entities.user import UserEntity
from core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from api.schemas.auth_schemas import UserCreate, Token
from core.config import settings


class AuthService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def register_user(self, user_in: UserCreate) -> UserEntity:
        # Check if user exists
        existing_user = await self.uow.users.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Hardcoding the first user to be superuser (optional heuristic)
        total_users = await self.uow.users.count()
        is_superuser = total_users == 0

        hashed_password = get_password_hash(user_in.password)
        new_user = UserEntity(
            email=user_in.email,
            username=user_in.username,
            hashed_password=hashed_password,
            is_superuser=is_superuser,
        )

        created_user = await self.uow.users.create(new_user)
        await self.uow.commit()
        return created_user

    async def authenticate_user(
        self, email: EmailStr, password: str
    ) -> UserEntity:
        user = await self.uow.users.get_auth_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Your account has been deactivated. Please reach out to the admin for inquiries."
            )
        return user

    def create_tokens(self, user_id: uuid.UUID) -> Token:
        access_token = create_access_token(subject=str(user_id))
        refresh_token = create_refresh_token(subject=str(user_id))
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_access_token(self, refresh_token: str) -> Token:
        try:
            payload = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[
                    settings.ALGORITHM]
            )
            user_id_str = payload.get("sub")
            token_type = payload.get("type")
            if user_id_str is None or token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = uuid.UUID(user_id_str)
        user = await self.uow.users.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please reach out to the admin for inquiries." if user and not user.is_active else "User not found",
            )

        return self.create_tokens(user_id)
