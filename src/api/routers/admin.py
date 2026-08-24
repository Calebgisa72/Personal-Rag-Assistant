import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from services.admin_service import AdminService
from api.dependencies import get_admin_service, get_current_superuser
from api.schemas.admin_schemas import (
    UserListResponse,
    SystemStatsResponse,
    UserStatusUpdate,
)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    limit: int = 20,
    admin_service: AdminService = Depends(get_admin_service),
    current_superuser: uuid.UUID = Depends(get_current_superuser),
):
    users, total = await admin_service.get_all_users(page=page, limit=limit)
    return UserListResponse(items=users, total=total, page=page, limit=limit)


@router.get("/stats", response_model=SystemStatsResponse)
async def system_stats(
    admin_service: AdminService = Depends(get_admin_service),
    current_superuser: uuid.UUID = Depends(get_current_superuser),
):
    return await admin_service.get_system_stats()


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: uuid.UUID,
    status_update: UserStatusUpdate,
    admin_service: AdminService = Depends(get_admin_service),
    current_superuser: uuid.UUID = Depends(get_current_superuser),
):
    updated = await admin_service.update_user_status(
        user_id, status_update.is_active
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return {"message": "User status updated successfully"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    admin_service: AdminService = Depends(get_admin_service),
    current_superuser: uuid.UUID = Depends(get_current_superuser),
):
    deleted = await admin_service.delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
