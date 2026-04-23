import pytest
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
async def test_get_summary_raises_on_llm_error(llm_service):
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

