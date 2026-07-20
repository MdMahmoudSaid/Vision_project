import logging

from local_attendance.camera.base import CapturedFrame
from local_attendance.face.engine import ComparisonResult, EnrollmentResult, FaceEngineBase, FaceEngineError

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

    def __init__(self, model_name: str = "ArcFace", distance_threshold: float = 4.15) -> None:
        self._model_name = model_name
        self._distance_threshold = distance_threshold

    def enroll(self, samples: list[CapturedFrame]) -> EnrollmentResult:
        import numpy as np
        from deepface import DeepFace

        embeddings: list[list[float]] = []
        for sample in samples:
            try:
                represented = DeepFace.represent(
                    img_path=sample.image,
                    model_name=self._model_name,
                    detector_backend=self._DETECTOR_BACKEND,
                    enforce_detection=True,
                )
            except ValueError:
                logger.warning("No face detected in an enrollment sample", exc_info=True)
                continue
            if represented:
                embeddings.append(represented[0]["embedding"])

        if not embeddings:
            return EnrollmentResult(usable=False, embedding=None, sample_count=0)

        averaged = np.mean(np.array(embeddings), axis=0).tolist()
        return EnrollmentResult(usable=True, embedding=averaged, sample_count=len(embeddings))

    def compare(self, capture: CapturedFrame, reference_embedding: list[float]) -> ComparisonResult:
        import numpy as np
        from deepface import DeepFace

        try:
            represented = DeepFace.represent(
                img_path=capture.image,
                model_name=self._model_name,
                detector_backend=self._DETECTOR_BACKEND,
                enforce_detection=True,
            )
        except ValueError as exc:
            logger.warning("No face detected in a verification capture", exc_info=True)
            raise FaceEngineError("No usable face detected in capture") from exc

        if not represented:
            raise FaceEngineError("No usable face detected in capture")

        candidate = np.array(represented[0]["embedding"])
        reference = np.array(reference_embedding)
        distance = float(np.linalg.norm(candidate - reference))
        similarity = 1.0 / (1.0 + distance)
        return ComparisonResult(is_match=distance <= self._distance_threshold, similarity_score=similarity)
