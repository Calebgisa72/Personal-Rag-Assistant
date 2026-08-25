from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime


class UserAdminResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    username: str
    profile_pic: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    items: List[UserAdminResponse]
    total: int
    page: int
    limit: int


class SystemStatsResponse(BaseModel):
    total_users: int
    total_documents: int
    total_conversations: int


class UserStatusUpdate(BaseModel):
    is_active: bool
