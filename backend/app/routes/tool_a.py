from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    DetectRequest,
    DetectResponse,
    ExportFacesRequest,
    ExportHtmlRequest,
    ExportPayload,
    FaceIdResponse,
    ImportFacesRequest,
    ImportFacesResponse,
)
from app.services.detection import detect_faces
from app.services.exporters import build_faces_json, build_form_entry_html
from app.services.face_ids import generate_face_id


router = APIRouter()


@router.post("/detect", response_model=DetectResponse)
def detect(request: DetectRequest) -> DetectResponse:
    result = detect_faces(
        request.imageDataUrl,
        request.existingFaces if request.importedJson else [],
    )
    if not result.detections and result.warnings:
        raise HTTPException(status_code=503, detail=result.warnings[0])
    mode = "redetect" if request.importedJson else "initial"
    return DetectResponse(mode=mode, detections=result.detections, warnings=result.warnings)


@router.post("/face-id", response_model=FaceIdResponse)
def issue_face_id() -> FaceIdResponse:
    return FaceIdResponse(faceId=generate_face_id())


@router.post("/import-faces", response_model=ImportFacesResponse)
def import_faces(request: ImportFacesRequest) -> ImportFacesResponse:
    return ImportFacesResponse(
        imageWidth=request.document.imageWidth,
        imageHeight=request.document.imageHeight,
        faces=request.document.faces,
    )


@router.post("/export/faces-json", response_model=ExportPayload)
def export_faces_json(request: ExportFacesRequest) -> ExportPayload:
    content = build_faces_json(request.imageWidth, request.imageHeight, request.faces)
    return ExportPayload(
        filename="faces.json",
        mimeType="application/json",
        content=content,
    )


@router.post("/export/form-entry", response_model=ExportPayload)
def export_form_entry(request: ExportHtmlRequest) -> ExportPayload:
    warnings = []
    if not request.msFormsUrlPrefix or not request.msFormsUrlPrefix.endswith("="):
        warnings.append("MS Forms URL prefix is missing or malformed. Export was generated without a valid prefix.")

    content = build_form_entry_html(
        image_data_url=request.imageDataUrl,
        faces=request.faces,
        ms_forms_url_prefix=request.msFormsUrlPrefix,
        include_privacy_notice=request.includePrivacyNotice,
    )
    return ExportPayload(
        filename="form_entry.html",
        mimeType="text/html",
        content=content,
        warnings=warnings,
    )
