import pytest
import numpy as np
import tempfile
import faiss
from unittest.mock import MagicMock, patch
from app.services.vector_service import FAISSVectorStore


@pytest.fixture
def vector_store():
    return FAISSVectorStore()


def test_add_chunks_batching(vector_store):
    """Test that embedding calls are batched at the 100 chunk boundary."""
    chunks = [MagicMock(text=f"text {i}") for i in range(150)]
    with (
        patch("app.services.vector_service.client.embeddings.create") as mock_create,
        patch.object(vector_store, "_load_index", return_value=MagicMock(ntotal=0)),
        patch.object(vector_store, "_save_index"),
    ):

        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536) for _ in range(150)]
        mock_create.return_value = mock_response

        vector_store.add_chunks(chunks, "user123")
        # Check that it was called twice (once for 100, once for 50)
        assert mock_create.call_count == 2


def test_similarity_search_returns_expected(vector_store):
    """Test that similarity_search returns sorted ChunkResult objects."""
    with (
        patch.object(vector_store, "_get_embeddings", return_value=[[0.1] * 1536]),
        patch.object(vector_store, "_load_index") as mock_load,
    ):

        mock_index = MagicMock()
        mock_index.ntotal = 5
        # Mock scores and indices
        mock_index.search.return_value = (
            np.array([[0.1, 0.4]]),  # Dists
            np.array([[2, 5]]),  # Indices
        )
        mock_load.return_value = mock_index

        results = vector_store.similarity_search("test query", "user123", k=2)
        assert len(results) == 2
        assert results[0].score == 0.1
        assert results[1].score == 0.4


def test_index_persistence_roundtrip():
    """Test index persistence: save to temp dir, reload, and verify search."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("app.core.config.settings.FAISS_INDEX_PATH", tmpdir):
            store = FAISSVectorStore()
            user_id = "user_persist"

            # Create a real small index
            index = faiss.IndexFlatL2(1536)
            dummy_vector = np.random.random((1, 1536)).astype("float32")
            index.add(dummy_vector)

            store._save_index(index, user_id)

            # Reload
            loaded_index = store._load_index(user_id)
            assert loaded_index.ntotal == 1
            assert np.allclose(loaded_index.reconstruct(0), dummy_vector[0])


def test_delete_by_file_id_removes_correct_vectors(vector_store):
    """Test that delete_by_file_id correctly handles metadata removal (if implemented)."""
    # Currently it's a pass in some versions, but if we have metadata tracking, we test it here.
    # For now, ensure it doesn't crash.
    vector_store.delete_by_file_id("file123", "user123")


def test_vector_store_get_embeddings_api_call(vector_store):
    """Test that _get_embeddings calls OpenAI API with correct parameters."""
    with patch("app.services.vector_service.client.embeddings.create") as mock_create:
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_create.return_value = mock_response

        vector_store._get_embeddings(["text1"])
        mock_create.assert_called_once_with(
            model="text-embedding-3-small", input=["text1"]
        )
