from dataclasses import dataclass, field
from typing import Optional
import uuid
from datetime import datetime

@dataclass
class UserEntity:
    email: str
    username: str
    hashed_password: str
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    profile_pic: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
