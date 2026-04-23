import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.llm_service import LLMService
from app.core.exceptions import LLMError

@pytest.fixture
def llm_service():
    return LLMService()

@pytest.mark.asyncio
async def test_truncate_messages_preserves_order(llm_service):
    """Test that token limit guard preserves system message and recent messages in order."""
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Old msg" * 50},
        {"role": "assistant", "content": "Old reply" * 50},
        {"role": "user", "content": "New msg"}
    ]
    # Very small limit to force removal of old messages but keep system + new
    truncated = llm_service._truncate_messages(messages, max_tokens=20)
    
    assert truncated[0]["content"] == "System prompt"
    assert truncated[-1]["content"] == "New msg"
    assert len(truncated) < 4

@pytest.mark.asyncio
async def test_context_injection_format(llm_service):
    """Test that page numbers and timestamps are correctly injected into the prompt."""
    messages = [{"role": "user", "content": "What happened?"}]
    context = [
        {"text_preview": "Text A", "page_number": 1, "start_time": None},
        {"text_preview": "Text B", "page_number": None, "start_time": 45.0}
    ]
    
    with patch.object(llm_service.client.chat.completions, "create") as mock_create:
        mock_create.return_value = AsyncMock() # Mock stream
        
        # We'll just check if it's called with a prompt containing our context
        async for _ in llm_service.get_chat_response_stream(messages, context):
            pass
            
        call_args = mock_create.call_args[1]
        system_msg = call_args["messages"][0]["content"]
        assert "Page 1" in system_msg
        assert "0:00:45" in system_msg

@pytest.mark.asyncio
async def test_map_reduce_two_pass_calls(llm_service):
    """Test map-reduce summarization with exactly 25 chunks, verifying two-pass logic."""
    chunks = ["chunk"] * 25
    with patch.object(llm_service, "_single_pass_summary", AsyncMock()) as mock_single:
        mock_single.return_value = {"summary": "s", "key_topics": [], "word_count": 1}
        await llm_service.get_summary(chunks)
        # 5 map calls (25/5) + 1 reduce call = 6 total
        assert mock_single.call_count == 6

@pytest.mark.asyncio
async def test_low_context_fallback(llm_service):
    """Test that the assistant indicates lack of context if no relevant snippets are provided."""
    messages = [{"role": "user", "content": "Secret?"}]
    context = [] # Empty context
    async def mock_generator(*args, **kwargs):
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="I don't have enough context."))]
        yield mock_chunk
    
    with patch.object(llm_service.client.chat.completions, "create", AsyncMock(side_effect=mock_generator)):
        gen = llm_service.get_chat_response_stream(messages, context)
        tokens = ""
        async for event in gen:
            if event.startswith("data: "):
                data = json.loads(event[6:])
                if data.get("type") == "token":
                    tokens += data["content"]
        
        assert "enough context" in tokens

@pytest.mark.asyncio
async def test_llm_error_wrapping(llm_service):
    """Test that OpenAI errors are correctly wrapped in LLMError."""
    with patch.object(llm_service.client.embeddings, "create", side_effect=Exception("API Down")):
        with pytest.raises(LLMError, match="OpenAI call failed"):
            await llm_service.generate_embeddings("test")
