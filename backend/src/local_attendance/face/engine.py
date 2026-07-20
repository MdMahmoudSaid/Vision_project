from abc import ABC, abstractmethod
from dataclasses import dataclass

from local_attendance.camera.base import CapturedFrame


class FaceEngineError(Exception):
    pass


@dataclass
class EnrollmentResult:
    usable: bool
    embedding: list[float] | None
    sample_count: int


@dataclass
class ComparisonResult:
    is_match: bool
    similarity_score: float


class FaceEngineBase(ABC):
    @abstractmethod
    def enroll(self, samples: list[CapturedFrame]) -> EnrollmentResult:
        """Produce a facial reference embedding from accepted enrollment samples."""
        raise NotImplementedError

    @abstractmethod
    def compare(self, capture: CapturedFrame, reference_embedding: list[float]) -> ComparisonResult:
        """Compare a verification capture against a stored reference embedding."""
        raise NotImplementedError


def get_face_engine() -> FaceEngineBase:
    from local_attendance.config import get_settings
    from local_attendance.face.deepface_engine import DeepFaceEngine

    return DeepFaceEngine(distance_threshold=get_settings().face_match_threshold)
