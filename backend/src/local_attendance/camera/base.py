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


def get_camera() -> CameraBase:
    from local_attendance.camera.opencv_camera import OpenCvCamera
    from local_attendance.config import get_settings

    return OpenCvCamera(camera_index=get_settings().camera_index)
