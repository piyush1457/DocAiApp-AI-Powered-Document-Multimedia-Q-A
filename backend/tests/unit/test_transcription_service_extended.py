import pytest
import subprocess
from unittest.mock import MagicMock, patch
from app.services.transcription_service import TranscriptionService
from app.core.exceptions import TranscriptionError


def test_extract_audio_failure():
    service = TranscriptionService()
    with patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "ffmpeg", stderr=b"error"),
    ):
        with pytest.raises(TranscriptionError, match="Failed to extract audio"):
            service.extract_audio("test.mp4")


def test_split_audio_failure():
    service = TranscriptionService()
    with patch("subprocess.check_output", side_effect=Exception("error")):
        with pytest.raises(TranscriptionError, match="Failed to split audio"):
            service.split_audio("test.mp3")


def test_call_whisper_failure():
    service = TranscriptionService()
    with (
        patch("builtins.open", MagicMock()),
        patch(
            "app.services.transcription_service.client.audio.transcriptions.create",
            side_effect=Exception("API error"),
        ),
    ):
        with pytest.raises(TranscriptionError, match="Groq transcription failed"):
            service._call_whisper("test.mp3")
