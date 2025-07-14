"""
Speaker diarization service for identifying and separating speakers in audio
"""

import logging
import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import torch
    from pyannote.audio import Pipeline
    from pyannote.core import Annotation, Segment

    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    Pipeline = None
    Annotation = None
    Segment = None

try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

logger = logging.getLogger(__name__)


class SpeakerDiarizationService:
    """Advanced speaker diarization using pyannote.audio"""

    def __init__(self, use_auth_token: Optional[str] = None):
        """
        Initialize speaker diarization service

        Args:
            use_auth_token: Hugging Face auth token for pyannote models
        """
        self.pipeline = None
        self.auth_token = use_auth_token
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if not PYANNOTE_AVAILABLE:
            logger.warning(
                "pyannote.audio not available. Install with: pip install pyannote.audio"
            )
            return

        try:
            self._initialize_pipeline()
        except Exception as e:
            logger.error(f"Failed to initialize speaker diarization pipeline: {e}")

    def _initialize_pipeline(self):
        """Initialize the pyannote speaker diarization pipeline"""
        try:
            # Use the speaker diarization pipeline
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1", use_auth_token=self.auth_token
            )

            if torch.cuda.is_available():
                self.pipeline = self.pipeline.to(torch.device("cuda"))

            logger.info(f"Speaker diarization pipeline initialized on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load pyannote pipeline: {e}")
            self.pipeline = None

    def is_available(self) -> bool:
        """Check if speaker diarization is available"""
        return PYANNOTE_AVAILABLE and self.pipeline is not None

    def diarize_audio(
        self, audio_path: str, min_speakers: int = 1, max_speakers: int = 10
    ) -> Optional[Annotation]:
        """
        Perform speaker diarization on audio file

        Args:
            audio_path: Path to audio file
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers

        Returns:
            pyannote Annotation object with speaker segments
        """
        if not self.is_available():
            logger.warning("Speaker diarization not available")
            return None

        try:
            # Apply the pipeline to an audio file
            diarization = self.pipeline(
                audio_path, min_speakers=min_speakers, max_speakers=max_speakers
            )

            return diarization

        except Exception as e:
            logger.error(f"Speaker diarization failed: {e}")
            return None

    def extract_speaker_segments(self, diarization: Annotation) -> List[Dict]:
        """
        Extract speaker segments from diarization annotation

        Args:
            diarization: pyannote Annotation object

        Returns:
            List of speaker segments with timing and speaker info
        """
        if not diarization:
            return []

        segments = []
        for segment, _, speaker in diarization.itertracks(yield_label=True):
            segments.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "duration": segment.duration,
                    "speaker": speaker,
                    "speaker_id": f"speaker_{speaker}",
                }
            )

        return sorted(segments, key=lambda x: x["start"])

    def align_transcription_with_speakers(
        self,
        transcription_segments: List[Dict],
        speaker_segments: List[Dict],
        overlap_threshold: float = 0.5,
    ) -> List[Dict]:
        """
        Align transcription segments with speaker information

        Args:
            transcription_segments: Whisper transcription segments
            speaker_segments: Speaker diarization segments
            overlap_threshold: Minimum overlap ratio to assign speaker

        Returns:
            Enhanced transcription segments with speaker information
        """
        enhanced_segments = []

        for trans_seg in transcription_segments:
            trans_start = trans_seg["start"]
            trans_end = trans_seg["end"]
            trans_duration = trans_end - trans_start

            # Find best matching speaker
            best_speaker = None
            best_overlap = 0

            for speaker_seg in speaker_segments:
                # Calculate overlap
                overlap_start = max(trans_start, speaker_seg["start"])
                overlap_end = min(trans_end, speaker_seg["end"])

                if overlap_end > overlap_start:
                    overlap_duration = overlap_end - overlap_start
                    overlap_ratio = overlap_duration / trans_duration

                    if (
                        overlap_ratio > best_overlap
                        and overlap_ratio >= overlap_threshold
                    ):
                        best_overlap = overlap_ratio
                        best_speaker = speaker_seg["speaker_id"]

            # Create enhanced segment
            enhanced_seg = trans_seg.copy()
            enhanced_seg["speaker"] = best_speaker or "unknown"
            enhanced_seg["speaker_confidence"] = best_overlap
            enhanced_segments.append(enhanced_seg)

        return enhanced_segments

    def get_speaker_statistics(self, enhanced_segments: List[Dict]) -> Dict[str, Any]:
        """
        Calculate speaker statistics from enhanced segments

        Args:
            enhanced_segments: Transcription segments with speaker info

        Returns:
            Dictionary with speaker statistics
        """
        speaker_stats = {}
        total_duration = 0

        for segment in enhanced_segments:
            speaker = segment.get("speaker", "unknown")
            duration = segment["end"] - segment["start"]
            total_duration += duration

            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    "total_duration": 0,
                    "segment_count": 0,
                    "word_count": 0,
                    "percentage": 0,
                }

            speaker_stats[speaker]["total_duration"] += duration
            speaker_stats[speaker]["segment_count"] += 1
            speaker_stats[speaker]["word_count"] += len(segment.get("text", "").split())

        # Calculate percentages
        for speaker in speaker_stats:
            if total_duration > 0:
                speaker_stats[speaker]["percentage"] = (
                    speaker_stats[speaker]["total_duration"] / total_duration * 100
                )

        # Add summary
        summary = {
            "total_speakers": len([s for s in speaker_stats.keys() if s != "unknown"]),
            "total_duration": total_duration,
            "speaker_breakdown": speaker_stats,
        }

        return summary

    def process_audio_with_speakers(
        self,
        audio_path: str,
        transcription_segments: List[Dict],
        min_speakers: int = 1,
        max_speakers: int = 10,
    ) -> Dict[str, Any]:
        """
        Complete speaker diarization pipeline

        Args:
            audio_path: Path to audio file
            transcription_segments: Existing transcription segments
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers

        Returns:
            Complete results with speaker-enhanced transcription
        """
        if not self.is_available():
            return {
                "enhanced_segments": transcription_segments,
                "speaker_segments": [],
                "speaker_statistics": {"total_speakers": 0, "total_duration": 0},
                "error": "Speaker diarization not available",
            }

        try:
            # Perform diarization
            diarization = self.diarize_audio(audio_path, min_speakers, max_speakers)

            if not diarization:
                return {
                    "enhanced_segments": transcription_segments,
                    "speaker_segments": [],
                    "speaker_statistics": {"total_speakers": 0, "total_duration": 0},
                    "error": "Diarization failed",
                }

            # Extract speaker segments
            speaker_segments = self.extract_speaker_segments(diarization)

            # Align with transcription
            enhanced_segments = self.align_transcription_with_speakers(
                transcription_segments, speaker_segments
            )

            # Calculate statistics
            speaker_stats = self.get_speaker_statistics(enhanced_segments)

            return {
                "enhanced_segments": enhanced_segments,
                "speaker_segments": speaker_segments,
                "speaker_statistics": speaker_stats,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Speaker diarization processing failed: {e}")
            return {
                "enhanced_segments": transcription_segments,
                "speaker_segments": [],
                "speaker_statistics": {"total_speakers": 0, "total_duration": 0},
                "error": str(e),
            }
