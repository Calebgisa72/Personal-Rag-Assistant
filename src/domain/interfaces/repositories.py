from abc import ABC, abstractmethod
import uuid
from typing import Optional, List
from domain.entities import (
    UserEntity,
    ConversationEntity,
    MessageEntity,
    DocumentEntity,
)


class IRepository(ABC):
    pass


class IUserRepository(IRepository):
    @abstractmethod
    async def create(self, user: UserEntity) -> UserEntity:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> Optional[UserEntity]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        pass

    @abstractmethod
    async def get_auth_user_by_email(self, email: str) -> Optional[UserEntity]:
        """Returns the user including the hashed_password for authentication purposes."""
        pass


class IConversationRepository(IRepository):
    @abstractmethod
    async def create(self, conversation: ConversationEntity) -> ConversationEntity:
        pass

    @abstractmethod
    async def get_by_id(
        self, conversation_id: uuid.UUID
    ) -> Optional[ConversationEntity]:
        pass

    @abstractmethod
    async def get_by_user_id(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> List[ConversationEntity]:
        pass

    @abstractmethod
    async def update_title(self, conversation_id: uuid.UUID, title: str) -> None:
        pass

    @abstractmethod
    async def update_pin_status(
        self, conversation_id: uuid.UUID, is_pinned: bool
    ) -> None:
        pass

    @abstractmethod
    async def add_message(self, message: MessageEntity) -> MessageEntity:
        pass


class IDocumentRepository(IRepository):
    @abstractmethod
    async def create(self, document: DocumentEntity) -> DocumentEntity:
        pass

    @abstractmethod
    async def get_by_id(self, document_id: uuid.UUID) -> Optional[DocumentEntity]:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID) -> List[DocumentEntity]:
        pass

    @abstractmethod
    async def get_all_by_user_id_paginated(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 10,
        mime_type: Optional[str] = None,
        upload_status: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[List[DocumentEntity], int]:
        """Returns a paginated list of documents matching the filters, and the total count."""
        pass

    @abstractmethod
    async def update_status(self, document_id: uuid.UUID, status: str) -> bool:
        pass

    @abstractmethod
    async def delete(self, document_id: uuid.UUID) -> bool:
        pass
