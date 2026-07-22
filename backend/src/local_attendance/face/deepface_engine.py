import logging

from local_attendance.camera.base import CapturedFrame
from local_attendance.face.engine import ComparisonResult, FaceEngineBase, FaceEngineError

logger = logging.getLogger(__name__)


class DeepFaceEngine(FaceEngineBase):
    """Face engine backed by DeepFace, behind the FaceEngineBase interface.

    Kept as a thin adapter so DeepFace/model internals never leak into services;
    automated tests use a fake engine instead of loading real models.
    """

    # DeepFace's own default ('opencv', a Haar-cascade) is not reliably packaged
    # across environments and raises rather than "no face found" when its cascade
    # data file is missing. retinaface is a real dependency of deepface already
    # and detects faces far more reliably across angles/lighting.
    _DETECTOR_BACKEND = "retinaface"

    # retinaface's own detector already applies a 0.9 score cutoff before a
    # region is reported at all; this is a second, independent floor on top
    # of that, so a borderline detection (e.g. on a hand, a poster, a
    # reflection) that just clears the detector's own threshold still gets
    # rejected here rather than silently becoming someone's face reference.
    _MIN_FACE_CONFIDENCE = 0.95

    # A correctly-detected face from an employee standing in front of the
    # fixed camera occupies a clear fraction of the frame. A "face" this
    # small relative to the frame is far more likely a spurious detection on
    # background clutter than an employee's actual face, even if the
    # detector reported high confidence for it.
    _MIN_FACE_AREA_RATIO = 0.03

    # Confidence and size alone are not enough: an anchor-based detector can
    # report high confidence on a non-face pattern (a light fixture, a
    # picture frame, a textured wall) that happens to match learned features.
    # A real face's 5 landmarks (both eyes, nose, mouth corners) always fall
    # in a specific geometric arrangement — eyes above the nose, nose above
    # the mouth, and the eyes a plausible distance apart relative to the face
    # box. Landmarks from a spurious detection are frequently nonsensical
    # under this test even when the raw detection score is high, so this
    # catches a class of false positive the confidence/size floors miss.
    _MIN_EYE_DISTANCE_RATIO = 0.20
    _MAX_EYE_DISTANCE_RATIO = 0.70
    _MIN_EYE_TO_MOUTH_RATIO = 0.12
    _MAX_EYE_TO_MOUTH_RATIO = 0.65

    def __init__(self, model_name: str = "ArcFace", distance_threshold: float = 4.15) -> None:
        self._model_name = model_name
        self._distance_threshold = distance_threshold

    def _has_plausible_face_geometry(self, area: dict) -> bool:
        left_eye, right_eye = area.get("left_eye"), area.get("right_eye")
        mouth_left, mouth_right = area.get("mouth_left"), area.get("mouth_right")
        nose = area.get("nose")
        face_w, face_h = area.get("w", 0), area.get("h", 0)

        if not (left_eye and right_eye and nose and face_w and face_h):
            # Some detector backends don't return landmarks at all; without
            # them we can't run this check, so fall back to the
            # confidence/size floors alone rather than rejecting outright.
            return True

        eye_distance = ((left_eye[0] - right_eye[0]) ** 2 + (left_eye[1] - right_eye[1]) ** 2) ** 0.5
        eye_ratio = eye_distance / face_w
        if not (self._MIN_EYE_DISTANCE_RATIO <= eye_ratio <= self._MAX_EYE_DISTANCE_RATIO):
            logger.info("Rejected face with implausible eye spacing (ratio=%.3f)", eye_ratio)
            return False

        eyes_y = (left_eye[1] + right_eye[1]) / 2
        if mouth_left and mouth_right:
            mouth_y = (mouth_left[1] + mouth_right[1]) / 2
        else:
            mouth_y = None

        # Eyes must sit above the nose, which must sit above the mouth (in
        # image coordinates, y grows downward) — a real face is never
        # upside-down or with landmarks out of order relative to the camera.
        if not (eyes_y < nose[1]):
            logger.info("Rejected face with implausible landmark ordering (eyes not above nose)")
            return False
        if mouth_y is not None:
            if not (nose[1] < mouth_y):
                logger.info("Rejected face with implausible landmark ordering (nose not above mouth)")
                return False
            eye_to_mouth_ratio = (mouth_y - eyes_y) / face_h
            if not (self._MIN_EYE_TO_MOUTH_RATIO <= eye_to_mouth_ratio <= self._MAX_EYE_TO_MOUTH_RATIO):
                logger.info("Rejected face with implausible eye-to-mouth span (ratio=%.3f)", eye_to_mouth_ratio)
                return False

        return True

    def _represent_one(self, image) -> dict | None:
        """Run detection+embedding on a single image, applying the confidence,
        face-size, and landmark-geometry floors. Returns the raw DeepFace
        result dict, or None if no sufficiently clear face was found."""
        from deepface import DeepFace

        try:
            represented = DeepFace.represent(
                img_path=image,
                model_name=self._model_name,
                detector_backend=self._DETECTOR_BACKEND,
                enforce_detection=True,
            )
        except ValueError:
            logger.info("No face region found by the detector at all")
            return None

        if not represented:
            logger.info("Detector returned no results")
            return None

        result = represented[0]
        confidence = result.get("face_confidence", 0.0)
        if confidence < self._MIN_FACE_CONFIDENCE:
            logger.info("Rejected low-confidence face detection (confidence=%.3f)", confidence)
            return None

        area = result.get("facial_area") or {}
        face_w, face_h = area.get("w", 0), area.get("h", 0)
        frame_h, frame_w = image.shape[0], image.shape[1]
        if frame_w and frame_h:
            area_ratio = (face_w * face_h) / (frame_w * frame_h)
            if area_ratio < self._MIN_FACE_AREA_RATIO:
                logger.info("Rejected undersized face detection (area_ratio=%.4f)", area_ratio)
                return None

        if not self._has_plausible_face_geometry(area):
            return None

        logger.info(
            "Accepted face detection (confidence=%.3f, area_ratio=%.4f)",
            confidence,
            (face_w * face_h) / (frame_w * frame_h) if frame_w and frame_h else -1,
        )
        return result

    def enroll_sample(self, frame: CapturedFrame) -> list[float] | None:
        result = self._represent_one(frame.image)
        if result is None:
            return None
        return result["embedding"]

    def compare(self, capture: CapturedFrame, reference_embedding: list[float]) -> ComparisonResult:
        import numpy as np

        result = self._represent_one(capture.image)
        if result is None:
            raise FaceEngineError("No usable face detected in capture")

        candidate = np.array(result["embedding"])
        reference = np.array(reference_embedding)
        distance = float(np.linalg.norm(candidate - reference))
        similarity = 1.0 / (1.0 + distance)
        return ComparisonResult(is_match=distance <= self._distance_threshold, similarity_score=similarity)
