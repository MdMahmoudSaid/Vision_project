from abc import ABC, abstractmethod
from dataclasses import dataclass

from local_attendance.camera.base import CapturedFrame


class FaceEngineError(Exception):
    def __init__(self, message: str, reason: str = "face_not_detected") -> None:
        super().__init__(message)
        self.reason = reason


@dataclass
class ComparisonResult:
    is_match: bool
    similarity_score: float


class FaceEngineBase(ABC):
    @abstractmethod
    def enroll_sample(self, frame: CapturedFrame) -> list[float] | None:
        """Attempt to produce a facial embedding from a single enrollment frame.

        Returns None (rather than raising) when the frame does not contain a
        clear, confidently-detected face — callers are expected to discard the
        frame and capture a fresh one rather than treat a rejected sample as
        an error.
        """
        raise NotImplementedError

    @abstractmethod
    def compare(self, capture: CapturedFrame, reference_embedding: list[float]) -> ComparisonResult:
        """Compare a verification capture against a stored reference embedding."""
        raise NotImplementedError


def get_face_engine() -> FaceEngineBase:
    from local_attendance.config import get_settings
    from local_attendance.face.deepface_engine import DeepFaceEngine

    settings = get_settings()
    return DeepFaceEngine(
        distance_threshold=settings.face_match_threshold,
        anti_spoofing=settings.anti_spoofing_enabled,
    )
