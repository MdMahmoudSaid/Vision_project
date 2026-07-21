from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class CameraCaptureError(Exception):
    pass


@dataclass
class CapturedFrame:
    image: Any


class CameraBase(ABC):
    @abstractmethod
    def capture_frame(self) -> CapturedFrame:
        """Capture a single frame from the fixed camera.

        Raises CameraCaptureError if the camera cannot produce a usable frame.
        Implementations must not persist the raw frame to disk.
        """
        raise NotImplementedError

    @abstractmethod
    def encode_jpeg(self, frame: CapturedFrame) -> bytes:
        """Encode a captured frame as JPEG bytes, for the camera-preview endpoint.

        This is a display-only snapshot for the guard's UI (confirming the
        camera can see a face before verification) — never persisted to disk
        and never used for face comparison.
        """
        raise NotImplementedError


def get_camera() -> CameraBase:
    from local_attendance.camera.opencv_camera import OpenCvCamera
    from local_attendance.config import get_settings

    return OpenCvCamera(camera_index=get_settings().camera_index)
