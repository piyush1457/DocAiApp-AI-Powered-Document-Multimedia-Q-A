import pytest
from app.utils.chunker import RecursiveCharacterTextSplitter, Chunk

def test_chunker_basic_split():
    """Test that text is split into multiple chunks when exceeding chunk_size."""
    text = "This is a test sentence. This is another test sentence."
    splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=0)
    chunks = splitter.create_chunks(text, {"source": "test"})
    assert len(chunks) > 1
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(c.token_count <= 10 for c in chunks)

def test_chunker_overlap_correctness():
    """Test that overlap text appears in adjacent chunks correctly."""
    text = "Alpha Beta Gamma Delta Epsilon Zeta Eta Theta"
    splitter = RecursiveCharacterTextSplitter(chunk_size=4, chunk_overlap=2)
    chunks = splitter.create_chunks(text, {})
    assert len(chunks) > 1
    # Check if the end of first chunk exists in the start of second chunk
    overlap_found = False
    for i in range(len(chunks) - 1):
        if any(word in chunks[i+1].text for word in chunks[i].text.split()[-2:]):
            overlap_found = True
            break
    assert overlap_found

def test_chunker_boundary_exactly_chunk_size():
    """Test chunking when text is exactly the chunk_size."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=10)
    # "Hello " * 5 is approx 10 tokens in cl100k_base (1 token per "Hello ")
    text = "Hello " * 5
    chunks = splitter.create_chunks(text, {})
    assert len(chunks) == 1

def test_chunker_boundary_chunk_size_plus_one():
    """Test chunking when text is exactly chunk_size + 1 token."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=0)
    text = "Hello " * 6
    chunks = splitter.create_chunks(text, {})
    assert len(chunks) > 1

def test_chunker_empty_input():
    """Test that empty input returns no chunks."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=100)
    chunks = splitter.create_chunks("", {})
    assert len(chunks) == 0

def test_chunker_single_word():
    """Test that a single word is handled correctly."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=100)
    chunks = splitter.create_chunks("Hello", {})
    assert len(chunks) == 1
    assert chunks[0].text == "Hello"

def test_chunker_unicode_and_emojis():
    """Test chunking with unicode characters and emojis."""
    text = "🌟" * 20 + " 🚀 " + "こんにちは" * 10
    splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=2)
    chunks = splitter.create_chunks(text, {})
    assert len(chunks) > 1
    assert "".join([c.text for c in chunks]).replace(" ", "") == text.replace(" ", "")

def test_chunker_code_blocks():
    """Test that code blocks are handled, prioritizing separators."""
    text = "```python\ndef hello():\n    print('world')\n```\n\nNext section."
    splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=0, separators=["\n\n", "\n", " "])
    chunks = splitter.create_chunks(text, {})
    assert len(chunks) > 1
    assert any("Next section" in c.text for c in chunks)

def test_chunker_metadata_preservation_per_chunk():
    """Test that metadata like page_number and start_time is preserved in all chunks."""
    text = "Part one. Part two. Part three."
    metadata = {"page_number": 5, "start_time": 120.5}
    splitter = RecursiveCharacterTextSplitter(chunk_size=2, chunk_overlap=0)
    chunks = splitter.create_chunks(text, metadata)
    for chunk in chunks:
        assert chunk.metadata["page_number"] == 5
        assert chunk.metadata["start_time"] == 120.5
