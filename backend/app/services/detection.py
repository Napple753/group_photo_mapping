from __future__ import annotations

from typing import Iterable

import cv2
import numpy as np

from app.models import CandidateRegion, FaceRegion
from app.services.ids import generate_candidate_id


def detect_face_candidates(image_bytes: bytes, existing_faces: Iterable[FaceRegion]) -> list[CandidateRegion]:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image for face detection")

    image_height, image_width = image.shape[:2]
    detections = _detect_with_mediapipe(image)
    if not detections:
        detections = _detect_with_haar(image)

    existing = list(existing_faces)
    candidates: list[CandidateRegion] = []
    for x, y, width, height, confidence in detections:
        candidate = CandidateRegion(
            candidateId=generate_candidate_id(),
            cx=(x + width / 2) / image_width,
            cy=(y + height / 2) / image_height,
            rx=(width / 2) / image_width,
            ry=(height * 0.62) / image_height,
            confidence=confidence,
        )
        if _overlaps_existing(candidate, existing):
            continue
        candidates.append(candidate)

    return candidates


def _detect_with_mediapipe(image: np.ndarray) -> list[tuple[float, float, float, float, float | None]]:
    try:
        import mediapipe as mp
    except ImportError:
        return []

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    detector = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.45)
    results = detector.process(rgb_image)
    detector.close()
    if not results.detections:
        return []

    image_height, image_width = image.shape[:2]
    faces: list[tuple[float, float, float, float, float | None]] = []
    for detection in results.detections:
        bbox = detection.location_data.relative_bounding_box
        x = max(bbox.xmin * image_width, 0)
        y = max(bbox.ymin * image_height, 0)
        width = min(bbox.width * image_width, image_width - x)
        height = min(bbox.height * image_height, image_height - y)
        confidence = float(detection.score[0]) if detection.score else None
        faces.append((x, y, width, height, confidence))

    return faces


def _detect_with_haar(image: np.ndarray) -> list[tuple[int, int, int, int, float | None]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    detections = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(32, 32))
    return [(int(x), int(y), int(width), int(height), None) for x, y, width, height in detections]


def _overlaps_existing(candidate: CandidateRegion, existing_faces: list[FaceRegion]) -> bool:
    candidate_box = _to_bounds(candidate.cx, candidate.cy, candidate.rx, candidate.ry)
    for face in existing_faces:
        overlap = _intersection_over_union(candidate_box, _to_bounds(face.cx, face.cy, face.rx, face.ry))
        if overlap >= 0.25:
            return True
    return False


def _to_bounds(cx: float, cy: float, rx: float, ry: float) -> tuple[float, float, float, float]:
    return (cx - rx, cy - ry, cx + rx, cy + ry)


def _intersection_over_union(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    left = max(a[0], b[0])
    top = max(a[1], b[1])
    right = min(a[2], b[2])
    bottom = min(a[3], b[3])
    if left >= right or top >= bottom:
        return 0.0

    intersection = (right - left) * (bottom - top)
    area_a = max(a[2] - a[0], 0) * max(a[3] - a[1], 0)
    area_b = max(b[2] - b[0], 0) * max(b[3] - b[1], 0)
    union = area_a + area_b - intersection
    if union <= 0:
        return 0.0
    return intersection / union
