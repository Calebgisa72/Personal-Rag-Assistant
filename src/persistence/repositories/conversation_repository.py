import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.interfaces import IConversationRepository
from domain.entities import (
    ConversationEntity,
    MessageEntity,
    ConversationSummaryEntity,
    MessageAttachmentEntity,
)
from infrastructure.database.models import (
    Conversation,
    Message,
    ConversationSummary,
    MessageAttachment,
)


class ConversationRepository(IConversationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, conversation: ConversationEntity) -> ConversationEntity:
        db_conv = Conversation(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            title=conversation.title,
        )
        self.session.add(db_conv)
        await self.session.flush()
        return conversation

    async def get_by_id(
        self, conversation_id: uuid.UUID
    ) -> Optional[ConversationEntity]:
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.messages).selectinload(Message.attachments),
                selectinload(Conversation.summary),
            )
            .where(Conversation.conversation_id == conversation_id)
        )
        result = await self.session.execute(stmt)
        db_conv = result.scalar_one_or_none()
        if not db_conv:
            return None

        messages = []
        for m in db_conv.messages:
            attachments = [
                MessageAttachmentEntity(
                    attachment_id=a.attachment_id,
                    message_id=a.message_id,
                    file_name=a.file_name,
                    file_type=a.file_type,
                    is_temporary=a.is_temporary,
                    parsed_content=a.parsed_content,
                )
                for a in m.attachments
            ]

            messages.append(
                MessageEntity(
                    message_id=m.message_id,
                    conversation_id=m.conversation_id,
                    role=m.role,
                    content=m.content,
                    created_at=m.created_at,
                    attachments=attachments,
                )
            )

        summary_entity = None
        if db_conv.summary:
            summary_entity = ConversationSummaryEntity(
                summary_id=db_conv.summary.summary_id,
                conversation_id=db_conv.summary.conversation_id,
                summary=db_conv.summary.summary,
                message_count=db_conv.summary.message_count,
                last_summarized_at=db_conv.summary.last_summarized_at,
            )

        return ConversationEntity(
            conversation_id=db_conv.conversation_id,
            user_id=db_conv.user_id,
            title=db_conv.title,
            messages=messages,
            summary=summary_entity,
            created_at=db_conv.created_at,
            updated_at=db_conv.updated_at,
            is_pinned=db_conv.is_pinned,
        )

    async def get_by_user_id(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> List[ConversationEntity]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        db_convs = result.scalars().all()

        return [
            ConversationEntity(
                conversation_id=c.conversation_id,
                user_id=c.user_id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                is_pinned=c.is_pinned,
            )
            for c in db_convs
        ]

    async def add_message(self, message: MessageEntity) -> MessageEntity:
        db_msg = Message(
            message_id=message.message_id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
        )
        self.session.add(db_msg)

        for att in message.attachments:
            db_att = MessageAttachment(
                attachment_id=att.attachment_id,
                message_id=db_msg.message_id,
                file_name=att.file_name,
                file_type=att.file_type,
                is_temporary=att.is_temporary,
                parsed_content=att.parsed_content,
            )
            self.session.add(db_att)

        await self.session.flush()
        return message

    async def save_summary(
        self, summary: ConversationSummaryEntity
    ) -> ConversationSummaryEntity:
        stmt = select(ConversationSummary).where(
            ConversationSummary.conversation_id == summary.conversation_id
        )
        result = await self.session.execute(stmt)
        db_summary = result.scalar_one_or_none()

        if db_summary:
            db_summary.summary = summary.summary
            db_summary.message_count = summary.message_count
            db_summary.last_summarized_at = summary.last_summarized_at
        else:
            db_summary = ConversationSummary(
                summary_id=summary.summary_id,
                conversation_id=summary.conversation_id,
                summary=summary.summary,
                message_count=summary.message_count,
                last_summarized_at=summary.last_summarized_at,
            )
            self.session.add(db_summary)

        await self.session.flush()
        return summary

    async def trim_messages(self, conversation_id: uuid.UUID, keep_last: int):
        from sqlalchemy import delete

        stmt = (
            select(Message.message_id)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(keep_last)
        )
        result = await self.session.execute(stmt)
        kept_ids = [row[0] for row in result.all()]

        if kept_ids:
            del_stmt = delete(Message).where(
                Message.conversation_id == conversation_id,
                Message.message_id.not_in(kept_ids),
            )
            await self.session.execute(del_stmt)
            await self.session.flush()

    async def update_title(self, conversation_id: uuid.UUID, title: str) -> None:
        stmt = select(Conversation).where(
            Conversation.conversation_id == conversation_id
        )
        result = await self.session.execute(stmt)
        db_conv = result.scalar_one_or_none()
        if db_conv:
            db_conv.title = title
            await self.session.flush()

    async def update_pin_status(
        self, conversation_id: uuid.UUID, is_pinned: bool
    ) -> None:
        stmt = select(Conversation).where(
            Conversation.conversation_id == conversation_id
        )
        result = await self.session.execute(stmt)
        db_conv = result.scalar_one_or_none()
        if db_conv:
            db_conv.is_pinned = is_pinned
            await self.session.flush()
