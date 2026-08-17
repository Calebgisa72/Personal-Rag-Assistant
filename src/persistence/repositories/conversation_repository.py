import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.interfaces import IConversationRepository
from domain.entities import ConversationEntity, MessageEntity
from infrastructure.database.models import Conversation, Message

class ConversationRepository(IConversationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, conversation: ConversationEntity) -> ConversationEntity:
        db_conv = Conversation(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            title=conversation.title
        )
        self.session.add(db_conv)
        await self.session.flush()
        return conversation

    async def get_by_id(self, conversation_id: uuid.UUID) -> Optional[ConversationEntity]:
        stmt = select(Conversation).options(selectinload(Conversation.messages)).where(Conversation.conversation_id == conversation_id)
        result = await self.session.execute(stmt)
        db_conv = result.scalar_one_or_none()
        if not db_conv:
            return None
        
        messages = [
            MessageEntity(
                message_id=m.message_id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                created_at=m.created_at
            ) for m in db_conv.messages
        ]

        return ConversationEntity(
            conversation_id=db_conv.conversation_id,
            user_id=db_conv.user_id,
            title=db_conv.title,
            messages=messages,
            created_at=db_conv.created_at,
            updated_at=db_conv.updated_at
        )

    async def get_by_user_id(self, user_id: uuid.UUID) -> List[ConversationEntity]:
        stmt = select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.created_at.desc())
        result = await self.session.execute(stmt)
        db_convs = result.scalars().all()
        
        return [
            ConversationEntity(
                conversation_id=c.conversation_id,
                user_id=c.user_id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at
            ) for c in db_convs
        ]

    async def add_message(self, message: MessageEntity) -> MessageEntity:
        db_msg = Message(
            message_id=message.message_id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content
        )
        self.session.add(db_msg)
        await self.session.flush()
        return message
