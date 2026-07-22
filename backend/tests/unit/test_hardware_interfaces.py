import pytest

from local_attendance.camera.base import CameraBase, CameraCaptureError, CapturedFrame
from local_attendance.face.engine import ComparisonResult, FaceEngineBase


class FakeCamera(CameraBase):
    def __init__(self, frame: CapturedFrame | None = None, raise_error: bool = False):
        self._frame = frame or CapturedFrame(image="fake-image")
        self._raise_error = raise_error

    def capture_frame(self) -> CapturedFrame:
        if self._raise_error:
            raise CameraCaptureError("no usable frame")
        return self._frame

    def encode_jpeg(self, frame: CapturedFrame) -> bytes:
        return b"fake-jpeg-bytes"


class FakeFaceEngine(FaceEngineBase):
    def __init__(self, is_match: bool = True, similarity: float = 0.9, usable: bool = True):
        self._is_match = is_match
        self._similarity = similarity
        self._usable = usable

    def enroll_sample(self, frame: CapturedFrame) -> list[float] | None:
        if not self._usable:
            return None
        return [0.1, 0.2, 0.3]

    def compare(self, capture: CapturedFrame, reference_embedding: list[float]) -> ComparisonResult:
        return ComparisonResult(is_match=self._is_match, similarity_score=self._similarity)


def test_camera_capture_frame_returns_frame():
    camera = FakeCamera()
    frame = camera.capture_frame()
    assert frame.image == "fake-image"


def test_camera_capture_frame_raises_capture_error():
    camera = FakeCamera(raise_error=True)
    with pytest.raises(CameraCaptureError):
        camera.capture_frame()


def test_face_engine_enroll_sample_returns_embedding_for_clear_face():
    engine = FakeFaceEngine(usable=True)
    embedding = engine.enroll_sample(CapturedFrame(image="a"))
    assert embedding is not None


def test_face_engine_enroll_sample_rejects_when_no_face():
    engine = FakeFaceEngine(usable=False)
    embedding = engine.enroll_sample(CapturedFrame(image="a"))
    assert embedding is None


def test_face_engine_compare_reports_match():
    engine = FakeFaceEngine(is_match=True, similarity=0.95)
    result = engine.compare(CapturedFrame(image="a"), [0.1, 0.2, 0.3])
    assert result.is_match
    assert result.similarity_score == 0.95


def test_face_engine_compare_reports_no_match():
    engine = FakeFaceEngine(is_match=False, similarity=0.1)
    result = engine.compare(CapturedFrame(image="a"), [0.1, 0.2, 0.3])
    assert not result.is_match
