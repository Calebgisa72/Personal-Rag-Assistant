import uuid
from typing import List, Tuple

from persistence.uow import UnitOfWork
from domain.entities.conversation import ConversationEntity


class ConversationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def rename_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, title: str
    ) -> None:
        async with self.uow:
            conv = await self.uow.conversation_repository.get_by_id(conversation_id)
            if not conv:
                raise ValueError("Conversation not found")
            if conv.user_id != user_id:
                raise PermissionError("User does not own this conversation")
            await self.uow.conversation_repository.update_title(conversation_id, title)
            await self.uow.commit()

    async def pin_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, is_pinned: bool
    ) -> None:
        async with self.uow:
            conv = await self.uow.conversation_repository.get_by_id(conversation_id)
            if not conv:
                raise ValueError("Conversation not found")
            if conv.user_id != user_id:
                raise PermissionError("User does not own this conversation")
            await self.uow.conversation_repository.update_pin_status(
                conversation_id, is_pinned
            )
            await self.uow.commit()

    async def list_conversations(
        self, user_id: uuid.UUID, page: int, limit: int
    ) -> Tuple[List[ConversationEntity], int]:
        offset = (page - 1) * limit
        async with self.uow:
            convs = await self.uow.conversation_repository.get_by_user_id(
                user_id, limit=limit, offset=offset
            )
            total = len(convs)
        return convs, total

    async def get_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> ConversationEntity:
        async with self.uow:
            conv = await self.uow.conversation_repository.get_by_id(conversation_id)
            if not conv:
                raise ValueError("Conversation not found")
            if conv.user_id != user_id:
                raise PermissionError("User does not own this conversation")
            return conv
