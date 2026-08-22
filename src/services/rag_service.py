import uuid
from typing import Optional, Tuple
from domain.interfaces import IAIProvider, IVectorStore
from services.embedding_service import EmbeddingStrategyService
from core.logger import logger
from core.exceptions import VectorStoreError, AIProviderError
from core.config import settings
from persistence.uow import UnitOfWork
from domain.entities.conversation import (
    ConversationEntity,
    MessageEntity,
    ConversationSummaryEntity,
    MessageAttachmentEntity,
)
from prompts.rag_prompts import (
    RAG_SYSTEM_PROMPT,
    CHAT_SYSTEM_PROMPT,
    SUMMARIZATION_PROMPT,
)
import tempfile
import os
from fastapi import UploadFile
from infrastructure.document.parsers.parser_factory import ParserFactory


class RAGService:
    def __init__(
        self,
        embedding_service: EmbeddingStrategyService,
        ai_provider: IAIProvider,
        vector_store: IVectorStore,
        uow: UnitOfWork,
    ):
        self.embedding_service = embedding_service
        self.ai_provider = ai_provider
        self.vector_store = vector_store
        self.uow = uow

    async def ask_question(
        self,
        question: str,
        user_id: uuid.UUID,
        conversation_id_str: Optional[str] = None,
        file: Optional[UploadFile] = None,
    ) -> Tuple[str, str, bool]:
        """
        Returns answer, conversation_id, and a boolean indicating if summarization is needed.
        """
        # 0. Handle Optional Direct Document
        temp_parsed_content = ""
        attachment_entity = None
        if file:
            if file.content_type not in settings.ALLOWED_MIME_TYPES:
                raise ValueError(f"MIME type {file.content_type} not allowed.")

            tmp_path = None
            try:
                # Create a temporary file to parse
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(file.filename or "")[1]
                ) as tmp:
                    tmp_path = tmp.name
                    file_size = 0
                    while content := await file.read(1024 * 1024):  # 1MB chunks
                        file_size += len(content)
                        if file_size > settings.MAX_UPLOAD_SIZE:
                            raise ValueError(
                                f"File size exceeds the maximum limit of {settings.MAX_UPLOAD_SIZE} bytes."
                            )
                        tmp.write(content)

                parser = ParserFactory.get_parser(file.content_type)
                temp_parsed_content = parser.parse(tmp_path)
            except ValueError as e:
                if "maximum limit" in str(e):
                    raise
                logger.error("temp_document.parse_failed", detail=str(e))
                raise ValueError(f"Failed to parse temporary document: {str(e)}")
            except Exception as e:
                logger.error("temp_document.parse_failed", detail=str(e))
                raise ValueError(f"Failed to parse temporary document: {str(e)}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            attachment_entity = MessageAttachmentEntity(
                file_name=file.filename or "temp_doc",
                file_type=file.content_type,
                is_temporary=True,
                parsed_content=temp_parsed_content,
                message_id=uuid.uuid4(),  # placeholder, will be set when MessageEntity is created
            )

        # 1. Embed question
        query_embedding = await self.embedding_service.get_embedding(question)

        # 2. Retrieve context
        try:
            chunks = await self.vector_store.similarity_search(query_embedding, k=5)
        except Exception as e:
            logger.error("vector_store.search_failed", detail=str(e))
            raise VectorStoreError(f"Failed to retrieve context: {str(e)}")

        # The ChromaDB Vector store now filters chunks by RAG_RELEVANCE_THRESHOLD natively
        context_text = "\n\n---\n\n".join([c.content for c in chunks])

        if temp_parsed_content:
            context_text = f"=== TEMPORARY DIRECT DOCUMENT CONTENT ===\n{temp_parsed_content}\n\n=== RETRIEVED KNOWLEDGE ===\n{context_text}"

        # 3. Setup Conversation
        conversation = None
        conv_repo = self.uow.conversation_repository

        if conversation_id_str:
            try:
                conv_uuid = uuid.UUID(conversation_id_str)
                conversation = await conv_repo.get_by_id(conv_uuid)
            except ValueError:
                pass

        if not conversation:
            # Create a new conversation
            conversation = ConversationEntity(
                user_id=user_id,
                title=question[:50] + "..." if len(question) > 50 else question,
            )
            conversation = await conv_repo.create(conversation)

        conv_uuid = conversation.conversation_id

        # 4. Formulate Prompt using Memory
        summary_section = ""
        if conversation.summary:
            summary_section = (
                f"Previous Conversation Summary:\n{conversation.summary.summary}\n"
            )

        # Select prompt and temperature based on context availability
        temperature = settings.CHAT_TEMPERATURE
        if not context_text.strip():
            # No context at all (no chunks passed threshold, no temp file)
            # We use RAG prompt but with strict instructions handled inside the prompt to not hallucinate.
            # We lower temperature to ensure the fallback response is deterministic.
            temperature = settings.INSUFFICIENT_CONTEXT_TEMPERATURE
            system_prompt = RAG_SYSTEM_PROMPT.format(
                context_chunks="", summary_section=summary_section
            )
        else:
            # We have context
            temperature = settings.RAG_TEMPERATURE
            system_prompt = RAG_SYSTEM_PROMPT.format(
                context_chunks=context_text, summary_section=summary_section
            )

        messages = [{"role": "system", "content": system_prompt}]

        # Add recent history (up to max configured)
        for msg in conversation.messages:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": question})

        # 5. Generate Answer
        logger.info(
            "generating_rag_answer",
            num_chunks_retrieved=len(chunks),
            temp_doc_included=bool(temp_parsed_content),
            conversation_id=str(conv_uuid),
        )
        try:
            answer = await self.ai_provider.generate_completion(
                messages, temperature=temperature
            )
        except Exception as e:
            logger.error("ai_provider.completion_failed", detail=str(e))
            raise AIProviderError(f"Failed to generate answer: {str(e)}")

        # 6. Save Messages to DB
        user_msg = MessageEntity(
            role="user", content=question, conversation_id=conv_uuid
        )
        if attachment_entity:
            attachment_entity.message_id = user_msg.message_id
            user_msg.attachments.append(attachment_entity)

        ai_msg = MessageEntity(
            role="assistant", content=answer, conversation_id=conv_uuid
        )

        await conv_repo.add_message(user_msg)
        await conv_repo.add_message(ai_msg)
        await self.uow.commit()

        # 7. Check if summarization is needed
        # We check the length of messages plus the 2 we just added
        total_messages = len(conversation.messages) + 2
        needs_summarization = total_messages >= settings.MAX_MESSAGES_BEFORE_SUMMARY

        return answer, str(conv_uuid), needs_summarization

    async def summarize_conversation(self, conversation_id_str: str):
        """
        Background task to summarize a conversation and trim old messages.
        """
        try:
            conv_uuid = uuid.UUID(conversation_id_str)
        except ValueError:
            return

        async with UnitOfWork() as uow:
            conv_repo = uow.conversation_repository
            conversation = await conv_repo.get_by_id(conv_uuid)
            if not conversation:
                return

            total_messages = len(conversation.messages)
            if total_messages < settings.MAX_MESSAGES_BEFORE_SUMMARY:
                return  # In case it was already summarized or doesn't need it

            previous_summary_text = ""
            if conversation.summary:
                previous_summary_text = (
                    f"Previous Summary:\n{conversation.summary.summary}"
                )

            # We will summarize all messages except the ones we want to keep
            messages_to_summarize = conversation.messages[
                : -settings.MESSAGES_TO_KEEP_AFTER_SUMMARY
            ]
            messages_to_keep = conversation.messages[
                -settings.MESSAGES_TO_KEEP_AFTER_SUMMARY :
            ]

            if not messages_to_summarize:
                return

            new_msgs_text = "\n".join(
                [f"{m.role}: {m.content}" for m in messages_to_summarize]
            )

            prompt = SUMMARIZATION_PROMPT.format(
                previous_summary_text=previous_summary_text, new_messages=new_msgs_text
            )

            messages = [{"role": "user", "content": prompt}]

            logger.info("summarizing_conversation", conversation_id=conversation_id_str)
            try:
                summary_result = await self.ai_provider.generate_completion(messages)
            except Exception as e:
                logger.error("summarization_failed", detail=str(e))
                return

            # Create or update summary
            summary_entity = ConversationSummaryEntity(
                conversation_id=conv_uuid,
                summary=summary_result,
                message_count=(
                    conversation.summary.message_count if conversation.summary else 0
                )
                + len(messages_to_summarize),
                last_summarized_at=__import__("datetime").datetime.utcnow(),
            )

            if conversation.summary:
                summary_entity.summary_id = conversation.summary.summary_id

            await conv_repo.save_summary(summary_entity)
            await conv_repo.trim_messages(
                conv_uuid, keep_last=settings.MESSAGES_TO_KEEP_AFTER_SUMMARY
            )

            await uow.commit()
