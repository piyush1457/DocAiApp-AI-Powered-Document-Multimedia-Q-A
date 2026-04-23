import pytest
from unittest.mock import MagicMock, patch, mock_open
from app.services.transcription_service import TranscriptionService
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def transcription_service():
    return TranscriptionService()


@pytest.fixture
def verbose_json_response():
    return {
        "segments": [
            {"text": "First segment", "start": 0.0, "end": 2.5},
            {"text": "Second segment", "start": 2.5, "end": 5.0},
        ]
    }


def test_extract_audio_success(transcription_service):
    """Test that ffmpeg is called correctly to extract audio from video."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        audio_path = transcription_service.extract_audio("test.mp4")
        assert audio_path.endswith(".mp3")
        mock_run.assert_called_once()


def test_split_audio_success(transcription_service):
    """Test large file chunking logic using ffmpeg and ffprobe."""
    with (
        patch("subprocess.check_output") as mock_probe,
        patch("subprocess.run") as mock_run,
    ):
        mock_probe.return_value = b"1200\n"  # 20 minutes
        mock_run.return_value = MagicMock(returncode=0)

        chunks = transcription_service.split_audio(
            "test.mp3", chunk_duration_sec=600, overlap_sec=60
        )
        # 1200s total. Chunks: [0, 600], [540, 1140], [1080, 1200] -> 3 chunks
        assert len(chunks) == 3
        assert mock_run.call_count == 3


@pytest.mark.asyncio
async def test_transcribe_file_offset_correction(transcription_service):
    """Test that segments from chunks are corrected with the proper time offset."""
    db = MagicMock(spec=AsyncSession)
    file_id = "mock-id"

    with (
        patch("os.path.getsize", return_value=30 * 1024 * 1024),
        patch.object(
            transcription_service, "split_audio", return_value=["c1.mp3", "c2.mp3"]
        ),
        patch.object(transcription_service, "_call_whisper") as mock_whisper,
        patch("os.remove"),
    ):

        # Mock 600s chunks
        mock_whisper.side_effect = [
            [{"text": "t1", "start": 0, "end": 5}],  # Chunk 1 (offset 0)
            [
                {"text": "t2", "start": 0, "end": 5}
            ],  # Chunk 2 (offset 540 if overlap=60)
        ]

        # We need to ensure split_audio returns metadata about offsets if the service uses it
        # Actually our split_audio just returns paths. Let's assume the service calculates offset.
        results = await transcription_service.transcribe_file("test.mp3", file_id, db)

        assert len(results) == 2
        # Check second segment offset (assuming 600s chunks with 30s overlap)
        # chunk_duration_sec - overlap_sec = 570
        assert results[1]["start"] == 570.0


@pytest.mark.asyncio
async def test_transcribe_persistence(transcription_service):
    """Test that all segments are persisted to the database with the correct file_id."""
    db = MagicMock(spec=AsyncSession)
    file_id = "mock-uuid"

    with (
        patch("os.path.getsize", return_value=1 * 1024 * 1024),
        patch.object(
            transcription_service,
            "_call_whisper",
            return_value=[{"text": "persist me", "start": 0, "end": 2}],
        ),
        patch("os.remove"),
    ):

        await transcription_service.transcribe_file("test.mp3", file_id, db)
        # Check db.add was called (it might be called in bulk or individual)
        assert db.add.called


def test_parse_segments_from_json(transcription_service, verbose_json_response):
    """Test segment parsing from verbose JSON fixture."""
    with patch(
        "app.services.transcription_service.client.audio.transcriptions.create"
    ) as mock_whisper:
        mock_response = MagicMock()
        mock_response.segments = verbose_json_response["segments"]
        mock_whisper.return_value = mock_response

        with patch("builtins.open", mock_open()):
            segments = transcription_service._call_whisper("test.mp3")
            assert len(segments) == 2
            assert segments[0]["text"] == "First segment"
            assert segments[1]["start"] == 2.5
