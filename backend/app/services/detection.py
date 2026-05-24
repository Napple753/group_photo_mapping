from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.models.schemas import CandidateRegion, FaceRegion


MODEL_PATH = Path(__file__).resolve().parent.parent / "assets" / "face_detector" / "face_detection_yunet.onnx"
MAX_DETECTION_DIMENSION = 1600
IOU_THRESHOLD = 0.35


@dataclass(slots=True)
class DetectionResult:
    detections: list[CandidateRegion]
    warnings: list[str]


def _decode_image(image_data_url: str) -> Image.Image:
    _, encoded = image_data_url.split(",", 1)
    image_bytes = base64.b64decode(encoded)
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _iou(region_a: CandidateRegion, region_b: FaceRegion) -> float:
    left = max(region_a.cx - region_a.rx, region_b.cx - region_b.rx)
    right = min(region_a.cx + region_a.rx, region_b.cx + region_b.rx)
    top = max(region_a.cy - region_a.ry, region_b.cy - region_b.ry)
    bottom = min(region_a.cy + region_a.ry, region_b.cy + region_b.ry)
    intersection_width = max(0.0, right - left)
    intersection_height = max(0.0, bottom - top)
    intersection = intersection_width * intersection_height
    area_a = region_a.rx * 2 * region_a.ry * 2
    area_b = region_b.rx * 2 * region_b.ry * 2
    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0


def _filter_existing_faces(detections: list[CandidateRegion], existing_faces: list[FaceRegion]) -> list[CandidateRegion]:
    if not existing_faces:
        return detections

    return [
        candidate
        for candidate in detections
        if not any(_iou(candidate, face) >= IOU_THRESHOLD for face in existing_faces)
    ]


def _resize_for_detection(image_bgr: np.ndarray) -> tuple[np.ndarray, float]:
    height, width = image_bgr.shape[:2]
    largest_side = max(width, height)
    if largest_side <= MAX_DETECTION_DIMENSION:
        return image_bgr, 1.0

    scale = MAX_DETECTION_DIMENSION / largest_side
    resized = cv2.resize(image_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return resized, scale


@lru_cache(maxsize=1)
def _create_detector() -> cv2.FaceDetectorYN:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"YuNet model file is missing: {MODEL_PATH}")

    return cv2.FaceDetectorYN.create(
        str(MODEL_PATH),
        "",
        (320, 320),
        score_threshold=0.78,
        nms_threshold=0.3,
        top_k=5000,
    )


def _to_candidate_region(index: int, detection_row: np.ndarray, width: int, height: int, scale: float) -> CandidateRegion:
    x, y, box_width, box_height = [float(value) / scale for value in detection_row[:4]]
    score = float(detection_row[-1])

    x1 = _clamp(x / width)
    y1 = _clamp(y / height)
    x2 = _clamp((x + box_width) / width)
    y2 = _clamp((y + box_height) / height)

    normalized_width = max(x2 - x1, 0.01)
    normalized_height = max(y2 - y1, 0.01)
    padded_width = _clamp(normalized_width * 1.1, 0.02, 1.0)
    padded_height = _clamp(normalized_height * 1.2, 0.02, 1.0)

    return CandidateRegion(
        candidateId=f"c_{index + 1:03d}",
        cx=_clamp((x1 + x2) / 2),
        cy=_clamp((y1 + y2) / 2),
        rx=_clamp(padded_width / 2, 0.01, 0.25),
        ry=_clamp(padded_height / 2, 0.01, 0.35),
        confidencePct=max(0, min(100, int(round(score * 100)))),
    )


def detect_faces(image_data_url: str, existing_faces: list[FaceRegion] | None = None) -> DetectionResult:
    existing_faces = existing_faces or []

    try:
        image = _decode_image(image_data_url)
        image_rgb = np.asarray(image)
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        detection_image, scale = _resize_for_detection(image_bgr)
        detector = _create_detector()
        detector.setInputSize((detection_image.shape[1], detection_image.shape[0]))
        _, raw_detections = detector.detect(detection_image)
    except Exception as error:
        return DetectionResult(detections=[], warnings=[f"Backend face detection failed: {error}"])

    if raw_detections is None or len(raw_detections) == 0:
        return DetectionResult(detections=[], warnings=[])

    detections = [
        _to_candidate_region(index, row, image.width, image.height, scale)
        for index, row in enumerate(sorted(raw_detections, key=lambda row: float(row[-1]), reverse=True))
    ]

    return DetectionResult(
        detections=_filter_existing_faces(detections, existing_faces),
        warnings=[],
    )
