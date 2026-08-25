from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from services.auth_service import AuthService
from api.dependencies import get_auth_service
from api.schemas.auth_schemas import UserCreate, UserResponse, Token, RefreshTokenRequest

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate, auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """Register a new user."""
    return await auth_service.register_user(user_in)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """Login to get access and refresh tokens. Use email as username."""
    user = await auth_service.authenticate_user(
        email=form_data.username, password=form_data.password
    )
    return auth_service.create_tokens(user.user_id)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """Refresh access token using refresh token."""
    return await auth_service.refresh_access_token(request.refresh_token)
