import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.llm_service import LLMService
from openai import RateLimitError


@pytest.fixture
def llm_service():
    return LLMService()


@pytest.mark.asyncio
async def test_llm_retry_logic(llm_service):
    """Test exponential backoff on RateLimitError."""
    mock_func = AsyncMock()
    # Fail twice with RateLimitError, then succeed
    mock_func.side_effect = [
        RateLimitError("Rate limit", response=MagicMock(), body={}),
        RateLimitError("Rate limit", response=MagicMock(), body={}),
        MagicMock(),
    ]

    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        await llm_service._call_with_retry(mock_func)
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2


@pytest.mark.asyncio
async def test_map_reduce_summary(llm_service):
    """Test map-reduce logic for large documents."""
    chunks = ["c1", "c2", "c3", "c4", "c5", "c6"]  # > 5

    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"summary": "s", "key_topics": [], "word_count": 1}'
            )
        )
    ]

    with patch.object(
        llm_service,
        "_single_pass_summary",
        AsyncMock(return_value={"summary": "s", "key_topics": [], "word_count": 1}),
    ) as mock_single:
        await llm_service._map_reduce_summary(chunks)
        # Should call once for first 5, once for next 1, then once for reduce
        assert mock_single.call_count == 3


@pytest.mark.asyncio
async def test_generate_embeddings_cache_hit(llm_service):
    """Test that embeddings are retrieved from cache if available."""
    from app.services.cache_service import cache_service

    with (
        patch.object(cache_service, "get", AsyncMock(return_value=[0.1, 0.2])),
        patch.object(llm_service.client.embeddings, "create") as mock_create,
    ):

        emb = await llm_service.generate_embeddings("test text")
        assert emb == [0.1, 0.2]
        mock_create.assert_not_called()
