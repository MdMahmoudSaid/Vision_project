from local_attendance.camera.base import CameraBase, CameraCaptureError, CapturedFrame


class OpenCvCamera(CameraBase):
    """Captures a single frame from the fixed USB webcam via OpenCV.

    Frames are held in memory only for the duration of enrollment/verification
    and are never written to disk.
    """

    # Freshly opened webcams commonly return black/garbage frames until
    # auto-exposure and auto-white-balance settle. Discarding a handful of
    # warm-up reads before taking the real frame avoids spurious capture
    # failures.
    _WARMUP_FRAMES = 5

    def __init__(self, camera_index: int) -> None:
        self._camera_index = camera_index

    def capture_frame(self) -> CapturedFrame:
        import cv2

        capture = cv2.VideoCapture(self._camera_index)
        try:
            if not capture.isOpened():
                raise CameraCaptureError(f"Unable to open camera at index {self._camera_index}")

            for _ in range(self._WARMUP_FRAMES):
                capture.read()

            ok, frame = capture.read()
            if not ok or frame is None:
                raise CameraCaptureError("Unable to capture a frame from the camera")
            return CapturedFrame(image=frame)
        finally:
            capture.release()

    def encode_jpeg(self, frame: CapturedFrame) -> bytes:
        import cv2

        ok, buffer = cv2.imencode(".jpg", frame.image)
        if not ok:
            raise CameraCaptureError("Unable to encode captured frame as JPEG")
        return buffer.tobytes()
