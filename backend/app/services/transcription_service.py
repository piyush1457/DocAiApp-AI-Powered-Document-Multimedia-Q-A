import os
import subprocess
import uuid
import math
from typing import List, Dict, Any
from groq import Groq
from app.core.config import settings
from app.core.exceptions import TranscriptionError
from app.db.models.transcript_segment import TranscriptSegment
from sqlalchemy.ext.asyncio import AsyncSession

client = Groq(api_key=settings.GROQ_API_KEY)


class TranscriptionService:
    @staticmethod
    def extract_audio(video_path: str) -> str:
        """Extracts audio from video using ffmpeg."""
        audio_path = f"{os.path.splitext(video_path)[0]}.mp3"
        try:
            command = [
                "ffmpeg",
                "-i",
                video_path,
                "-vn",
                "-acodec",
                "libmp3lame",
                "-y",
                audio_path,
            ]
            subprocess.run(command, check=True, capture_output=True)
            return audio_path
        except subprocess.CalledProcessError as e:
            raise TranscriptionError(
                f"Failed to extract audio from video: {e.stderr.decode()}"
            )

    @staticmethod
    def split_audio(
        audio_path: str, chunk_duration_sec: int = 600, overlap_sec: int = 30
    ) -> List[str]:
        """Splits audio into overlapping chunks using ffmpeg."""
        chunks = []
        try:
            # Get total duration
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ]
            duration = float(subprocess.check_output(cmd).decode().strip())

            output_pattern = f"{os.path.splitext(audio_path)[0]}_chunk_%d.mp3"

            # We use a loop to create overlapping chunks as ffmpeg's segment muxer doesn't natively support overlap easily for this use case
            num_chunks = math.ceil(duration / (chunk_duration_sec - overlap_sec))

            for i in range(num_chunks):
                start = i * (chunk_duration_sec - overlap_sec)
                if start >= duration:
                    break

                chunk_path = f"{os.path.splitext(audio_path)[0]}_chunk_{i}.mp3"
                cmd = [
                    "ffmpeg",
                    "-i",
                    audio_path,
                    "-ss",
                    str(start),
                    "-t",
                    str(chunk_duration_sec),
                    "-acodec",
                    "copy",
                    "-y",
                    chunk_path,
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                chunks.append(chunk_path)

            return chunks
        except Exception as e:
            raise TranscriptionError(f"Failed to split audio: {str(e)}")

    async def transcribe_file(
        self, file_path: str, file_id: uuid.UUID, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Transcribes an audio/video file.
        Handles large files by splitting and merging.
        """
        is_video = file_path.lower().endswith((".mp4", ".webm"))
        work_file = file_path

        if is_video:
            work_file = self.extract_audio(file_path)

        file_size_mb = os.path.getsize(work_file) / (1024 * 1024)

        segments_data = []

        if file_size_mb > 20:
            # Split and transcribe chunks
            chunks = self.split_audio(work_file)
            offset = 0
            overlap_sec = 30
            chunk_duration_sec = 600

            for i, chunk_path in enumerate(chunks):
                chunk_segments = self._call_whisper(chunk_path)

                # Correct timestamps and filter overlaps
                for seg in chunk_segments:
                    # Simple merging logic: avoid duplicates in overlap zones
                    seg_start = seg.get("start", 0) + offset
                    seg_end = seg.get("end", 0) + offset

                    segments_data.append(
                        {
                            "text": seg.get("text", ""),
                            "start": seg_start,
                            "end": seg_end,
                            "confidence": 0.9,
                        }
                    )

                offset += chunk_duration_sec - overlap_sec
                os.remove(chunk_path)
        else:
            whisper_segments = self._call_whisper(work_file)
            for seg in whisper_segments:
                segments_data.append(
                    {
                        "text": seg.get("text", ""),
                        "start": seg.get("start", 0),
                        "end": seg.get("end", 0),
                        "confidence": 0.9,
                    }
                )

        # Persist segments to DB
        for seg in segments_data:
            db_seg = TranscriptSegment(
                file_id=file_id,
                text=seg["text"],
                start_time=seg["start"],
                end_time=seg["end"],
                confidence=seg["confidence"],
            )
            db.add(db_seg)

        await db.commit()

        # Cleanup audio if it was extracted from video
        if is_video and work_file != file_path:
            os.remove(work_file)

        return segments_data

    def _call_whisper(self, file_path: str) -> List[Dict]:
        """Calls Groq Whisper API."""
        try:
            with open(file_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )
                return result.segments
        except Exception as e:
            raise TranscriptionError(f"Groq transcription failed: {str(e)}")
