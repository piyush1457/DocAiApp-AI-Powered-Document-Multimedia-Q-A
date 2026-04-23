import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.llm_service import LLMService
from app.core.exceptions import LLMError


@pytest.fixture
def llm_service():
    return LLMService()


@pytest.mark.asyncio
async def test_get_summary_returns_dict(llm_service):
    """Test that get_summary returns a dict with expected keys."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"summary": "Test summary", "key_topics": ["a", "b"], "word_count": 5}'
            )
        )
    ]
    with patch(
        "app.services.llm_service.asyncio.to_thread",
        AsyncMock(return_value=mock_response),
    ):
        result = await llm_service.get_summary(["chunk one", "chunk two"])
        assert "summary" in result
        assert "key_topics" in result
        assert result["summary"] == "Test summary"


@pytest.mark.asyncio
async def test_get_summary_raises_llm_error(llm_service):
    """Test that LLMError is raised when Groq call fails."""
    with patch(
        "app.services.llm_service.asyncio.to_thread",
        AsyncMock(side_effect=Exception("Groq down")),
    ):
        with pytest.raises(LLMError):
            await llm_service.get_summary(["some chunk"])


@pytest.mark.asyncio
async def test_generate_chapter_markers_returns_list(llm_service):
    """Test that generate_chapter_markers returns a list."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"chapters": [{"title": "Intro", "start_time": 0.0, "end_time": 60.0}]}'
            )
        )
    ]
    with patch(
        "app.services.llm_service.asyncio.to_thread",
        AsyncMock(return_value=mock_response),
    ):
        result = await llm_service.generate_chapter_markers("transcript text here")
        assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_chat_response_stream_yields_tokens(llm_service):
    """Test that get_chat_response_stream yields SSE-formatted token events."""
    messages = [{"role": "user", "content": "Hello?"}]
    context = [{"text_preview": "Some text", "page_number": 1, "start_time": None}]

    mock_chunk = MagicMock()
    mock_chunk.choices = [MagicMock(delta=MagicMock(content="Hello"))]

    mock_completion = [mock_chunk]

    with patch(
        "app.services.llm_service.asyncio.to_thread",
        AsyncMock(return_value=mock_completion),
    ):
        events = []
        async for event in llm_service.get_chat_response_stream(messages, context):
            events.append(event)

        assert len(events) > 0
        assert any("token" in e for e in events)


@pytest.mark.asyncio
async def test_generate_chapter_markers_raises_llm_error(llm_service):
    """Test that LLMError is raised when chapter marker generation fails."""
    with patch(
        "app.services.llm_service.asyncio.to_thread",
        AsyncMock(side_effect=Exception("API Down")),
    ):
        with pytest.raises(LLMError):
            await llm_service.generate_chapter_markers("transcript")
