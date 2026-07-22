import threading

from local_attendance.camera.base import CameraBase, CameraCaptureError, CapturedFrame

# A single physical webcam is shared by the preview endpoint (polled every
# ~800 ms while the guard/admin looks at the camera circle) and the real
# verify/enroll capture. Each capture_frame() call opens and releases its own
# cv2.VideoCapture, and a capture (15 warm-up grabs + a read) can take close
# to a second — long enough that two calls can legitimately overlap in time.
# Two threads opening the same camera index concurrently is not safe: OpenCV
# does not serialize this, and depending on the OS driver the second open can
# reset exposure/focus mid-read, handing back a corrupted or transitional
# frame instead of erroring out. That frame can still contain something a
# detector mistakes for a face. This lock makes every capture_frame() call
# process-wide mutually exclusive, so the preview and the real capture (and
# overlapping preview polls) can never touch the device at the same instant.
_camera_lock = threading.Lock()

# Bounds how long a caller waits for the camera if another capture is already
# in progress, rather than queuing indefinitely under sustained preview
# polling. A normal capture completes in well under this window.
_LOCK_TIMEOUT_SECONDS = 5.0


class OpenCvCamera(CameraBase):
    """Captures a single frame from the fixed USB webcam via OpenCV.

    Frames are held in memory only for the duration of enrollment/verification
    and are never written to disk.
    """

    # The camera preview polls the webcam every ~800 ms; when the guard
    # confirms and the real verification capture starts, the OS camera
    # driver (and OpenCV's own ring-buffer) may still contain frames from
    # the *previous* session where a face was visible.  At 15 FPS a
    # 5-frame flush only covers ~333 ms — not enough to guarantee a live
    # frame.  15 frames ≈ 1 s at 15 FPS, which reliably drains both the
    # driver buffer and any auto-exposure warm-up artefacts.
    _WARMUP_FRAMES = 15

    def __init__(self, camera_index: int) -> None:
        self._camera_index = camera_index

    def capture_frame(self) -> CapturedFrame:
        import cv2

        if not _camera_lock.acquire(timeout=_LOCK_TIMEOUT_SECONDS):
            raise CameraCaptureError("Camera is busy with another capture")
        try:
            capture = cv2.VideoCapture(self._camera_index)
            try:
                if not capture.isOpened():
                    raise CameraCaptureError(f"Unable to open camera at index {self._camera_index}")

                # Tell OpenCV to keep at most 1 frame in its internal ring-
                # buffer so that every read() returns the most recent frame
                # the driver has, rather than a queued stale one.
                capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                # grab() is cheaper than read(): it pulls the frame out of the
                # driver buffer without decoding it, so flushing is faster.
                for _ in range(self._WARMUP_FRAMES):
                    capture.grab()

                ok, frame = capture.read()
                if not ok or frame is None:
                    raise CameraCaptureError("Unable to capture a frame from the camera")
                return CapturedFrame(image=frame)
            finally:
                capture.release()
        finally:
            _camera_lock.release()

    def encode_jpeg(self, frame: CapturedFrame) -> bytes:
        import cv2

        ok, buffer = cv2.imencode(".jpg", frame.image)
        if not ok:
            raise CameraCaptureError("Unable to encode captured frame as JPEG")
        return buffer.tobytes()
