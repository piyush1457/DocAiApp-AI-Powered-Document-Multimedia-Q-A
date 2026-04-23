import pytest
import numpy as np
import tempfile
import os
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.vector_service import FAISSVectorStore


@pytest.fixture
def vector_store(tmp_path):
    return FAISSVectorStore(base_path=str(tmp_path), dimension=768)


@pytest.mark.asyncio
async def test_add_chunks_creates_index(vector_store):
    """Test that add_chunks creates a FAISS index file."""
    chunks = [MagicMock(text="text 1", file_id="file-1", page_number=1, start_time=None, end_time=None)]
    with patch.object(
        vector_store, "_get_embeddings", AsyncMock(return_value=[[0.1] * 768])
    ):
        await vector_store.add_chunks(chunks, "user123")
        index_file = os.path.join(vector_store.base_path, "user123.index")
        assert os.path.exists(index_file)


@pytest.mark.asyncio
async def test_add_chunks_empty_list_noop(vector_store):
    """Test that add_chunks with empty list does nothing."""
    await vector_store.add_chunks([], "user123")
    index_file = os.path.join(vector_store.base_path, "user123.index")
    assert not os.path.exists(index_file)


@pytest.mark.asyncio
async def test_similarity_search_no_index_returns_empty(vector_store):
    """Test that similarity_search returns empty list if index doesn't exist."""
    results = await vector_store.similarity_search("query", "user_nonexistent", "file-1")
    assert results == []


@pytest.mark.asyncio
async def test_add_and_search_roundtrip(vector_store):
    """Test adding chunks and searching returns results."""
    import uuid
    file_id = str(uuid.uuid4())
    chunks = [
        MagicMock(text="document about AI", file_id=file_id, page_number=1, start_time=None, end_time=None),
        MagicMock(text="machine learning basics", file_id=file_id, page_number=2, start_time=None, end_time=None),
    ]

    embedding = [0.1] * 768

    with patch.object(
        vector_store, "_get_embeddings", AsyncMock(return_value=[embedding, embedding])
    ):
        await vector_store.add_chunks(chunks, "user_search")

    with patch.object(
        vector_store, "_get_embeddings", AsyncMock(return_value=[embedding])
    ):
        results = await vector_store.similarity_search("AI query", "user_search", file_id, top_k=2)
        assert len(results) >= 1


def test_delete_by_file_id_no_index_noop(vector_store):
    """Test delete_by_file_id doesn't crash when no index exists."""
    vector_store.delete_by_file_id("user_none", "file_none")
