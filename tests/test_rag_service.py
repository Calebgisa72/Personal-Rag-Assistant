import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from services.rag_service import RAGService
from core.config import settings


@pytest.fixture
def mock_dependencies():
    embedding_service = AsyncMock()
    ai_provider = AsyncMock()
    vector_store = AsyncMock()
    uow = AsyncMock()

    # Mock UOW repositories
    uow.conversation_repository = AsyncMock()
    uow.conversation_repository.get_by_id.return_value = None
    uow.conversation_repository.create.return_value = MagicMock(
        conversation_id=uuid.uuid4(), messages=[], summary=None
    )

    return embedding_service, ai_provider, vector_store, uow


@pytest.mark.asyncio
async def test_ask_question_insufficient_context(mock_dependencies):
    embedding_service, ai_provider, vector_store, uow = mock_dependencies

    # Setup Vector store to return no chunks (or chunks below threshold which ChromaAdapter handles)
    vector_store.similarity_search.return_value = []

    # Setup AI Provider to return fallback
    ai_provider.generate_completion.return_value = "I don't have enough information in the documents available to me to answer that accurately. Please upload a relevant document."

    rag_service = RAGService(embedding_service, ai_provider, vector_store, uow)

    answer, conv_id, _ = await rag_service.ask_question(
        question="What is the revenue for 2025?", user_id=uuid.uuid4()
    )

    # Assert Vector search was called
    vector_store.similarity_search.assert_called_once()

    # Assert AI Provider was called with INSUFFICIENT_CONTEXT_TEMPERATURE
    ai_provider.generate_completion.assert_called_once()
    call_kwargs = ai_provider.generate_completion.call_args.kwargs
    assert call_kwargs.get("temperature") == settings.INSUFFICIENT_CONTEXT_TEMPERATURE

    assert "I don't have enough information" in answer


@pytest.mark.asyncio
@patch("src.services.rag_service.tempfile.NamedTemporaryFile")
@patch("src.services.rag_service.ParserFactory.get_parser")
@patch("src.services.rag_service.os.unlink")
async def test_ask_question_with_temp_document(
    mock_unlink, mock_get_parser, mock_tempfile, mock_dependencies
):
    embedding_service, ai_provider, vector_store, uow = mock_dependencies

    # Setup Mock Parser
    mock_parser = MagicMock()
    mock_parser.parse.return_value = "This is temporary document content."
    mock_get_parser.return_value = mock_parser

    # Setup Mock UploadFile
    mock_file = AsyncMock()
    mock_file.content_type = "text/plain"
    mock_file.filename = "temp.txt"
    mock_file.read.return_value = b"raw text"

    # Setup AI Provider
    ai_provider.generate_completion.return_value = "Based on the temporary document..."

    rag_service = RAGService(embedding_service, ai_provider, vector_store, uow)

    answer, conv_id, _ = await rag_service.ask_question(
        question="What does the document say?", user_id=uuid.uuid4(), file=mock_file
    )

    mock_get_parser.assert_called_once_with("text/plain")
    mock_parser.parse.assert_called_once()

    # The temperature should be RAG_TEMPERATURE because we have context
    call_kwargs = ai_provider.generate_completion.call_args.kwargs
    assert call_kwargs.get("temperature") == settings.RAG_TEMPERATURE

    # Verify the AI received the temp document in the messages payload
    call_args = ai_provider.generate_completion.call_args.args[0]
    system_prompt = call_args[0]["content"]
    assert "=== TEMPORARY DIRECT DOCUMENT CONTENT ===" in system_prompt
    assert "This is temporary document content." in system_prompt
