import uuid
from typing import Optional, Tuple
from domain.interfaces import IAIProvider, IVectorStore
from services.embedding_service import EmbeddingStrategyService
from core.logger import logger
from core.exceptions import VectorStoreError, AIProviderError
from core.config import settings
from persistence.uow import UnitOfWork
from domain.entities.conversation import ConversationEntity, MessageEntity, ConversationSummaryEntity
from prompts.chat_prompts import RAG_SYSTEM_PROMPT, SUMMARIZATION_PROMPT

class RAGService:
    def __init__(self, embedding_service: EmbeddingStrategyService, ai_provider: IAIProvider, vector_store: IVectorStore, uow: UnitOfWork):
        self.embedding_service = embedding_service
        self.ai_provider = ai_provider
        self.vector_store = vector_store
        self.uow = uow

    async def ask_question(self, question: str, user_id: uuid.UUID, conversation_id_str: Optional[str] = None) -> Tuple[str, str, bool]:
        """
        Returns answer, conversation_id, and a boolean indicating if summarization is needed.
        """
        # 1. Embed question
        query_embedding = await self.embedding_service.get_embedding(question)
        
        # 2. Retrieve context
        try:
            chunks = await self.vector_store.similarity_search(query_embedding, k=5)
        except Exception as e:
            logger.error("vector_store.search_failed", detail=str(e))
            raise VectorStoreError(f"Failed to retrieve context: {str(e)}")
        
        context_text = "\n\n---\n\n".join([c.content for c in chunks])
        
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
                title=question[:50] + "..." if len(question) > 50 else question
            )
            conversation = await conv_repo.create(conversation)
            
        conv_uuid = conversation.conversation_id
        
        # 4. Formulate Prompt using Memory
        summary_section = ""
        if conversation.summary:
            summary_section = f"Previous Conversation Summary:\n{conversation.summary.summary}\n"
            
        system_prompt = RAG_SYSTEM_PROMPT.format(
            context_chunks=context_text,
            summary_section=summary_section
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent history (up to max configured)
        for msg in conversation.messages:
            messages.append({"role": msg.role, "content": msg.content})
            
        messages.append({"role": "user", "content": question})
        
        # 5. Generate Answer
        logger.info("generating_rag_answer", num_chunks_retrieved=len(chunks), conversation_id=str(conv_uuid))
        try:
            answer = await self.ai_provider.generate_completion(messages)
        except Exception as e:
            logger.error("ai_provider.completion_failed", detail=str(e))
            raise AIProviderError(f"Failed to generate answer: {str(e)}")
            
        # 6. Save Messages to DB
        user_msg = MessageEntity(role="user", content=question, conversation_id=conv_uuid)
        ai_msg = MessageEntity(role="assistant", content=answer, conversation_id=conv_uuid)
        
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
                return # In case it was already summarized or doesn't need it
                
            previous_summary_text = ""
            if conversation.summary:
                previous_summary_text = f"Previous Summary:\n{conversation.summary.summary}"
                
            # We will summarize all messages except the ones we want to keep
            messages_to_summarize = conversation.messages[:-settings.MESSAGES_TO_KEEP_AFTER_SUMMARY]
            messages_to_keep = conversation.messages[-settings.MESSAGES_TO_KEEP_AFTER_SUMMARY:]
            
            if not messages_to_summarize:
                return
                
            new_msgs_text = "\n".join([f"{m.role}: {m.content}" for m in messages_to_summarize])
            
            prompt = SUMMARIZATION_PROMPT.format(
                previous_summary_text=previous_summary_text,
                new_messages=new_msgs_text
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
                message_count=(conversation.summary.message_count if conversation.summary else 0) + len(messages_to_summarize),
                last_summarized_at=__import__('datetime').datetime.utcnow()
            )
            
            if conversation.summary:
                summary_entity.summary_id = conversation.summary.summary_id
                
            await conv_repo.save_summary(summary_entity)
            await conv_repo.trim_messages(conv_uuid, keep_last=settings.MESSAGES_TO_KEEP_AFTER_SUMMARY)
            
            await uow.commit()