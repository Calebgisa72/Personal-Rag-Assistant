import uuid
from persistence.uow import UnitOfWork
from api.schemas.admin_schemas import SystemStatsResponse
from services.document_service import DocumentService


class AdminService:
    def __init__(self, uow: UnitOfWork, document_service: DocumentService):
        self.uow = uow
        self.document_service = document_service

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

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            return False
            
        docs = await self.uow.documents.get_by_user_id(user_id)
        for doc in docs:
            await self.document_service.delete_document(user_id, doc.document_id)
            
        deleted = await self.uow.users.delete(user_id)
        if deleted:
            await self.uow.commit()
        return deleted
