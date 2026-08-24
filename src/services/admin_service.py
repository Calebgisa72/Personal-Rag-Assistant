import uuid
from persistence.uow import UnitOfWork
from api.schemas.admin_schemas import SystemStatsResponse


class AdminService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_all_users(self, page: int = 1, limit: int = 20):
        skip = (page - 1) * limit
        return await self.uow.users.get_all_paginated(skip=skip, limit=limit)

    async def get_system_stats(self) -> SystemStatsResponse:
        total_users = await self.uow.users.count()
        total_docs = await self.uow.documents.count()
        total_convs = await self.uow.conversations.count()
        return SystemStatsResponse(
            total_users=total_users,
            total_documents=total_docs,
            total_conversations=total_convs,
        )

    async def update_user_status(self, user_id: uuid.UUID, is_active: bool) -> bool:
        updated = await self.uow.users.update_status(user_id, is_active)
        if updated:
            await self.uow.commit()
        return updated
