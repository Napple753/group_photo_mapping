from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    CandidateRegion,
    CreateFaceRequest,
    DetectionRequest,
    DetectionResponse,
    ExportFacesRequest,
    ExportFormEntryRequest,
    ExportPayload,
    FaceDocument,
    FaceRegion,
    SessionImportRequest,
    SessionImportResponse,
)
from app.services.detection import detect_face_candidates
from app.services.exporter import build_form_entry_html
from app.services.ids import generate_face_id
from app.services.images import ImageDecodeError, decode_data_url, get_image_size

app = FastAPI(title="Group Photo Mapping Tool", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/tool-a/session/import", response_model=SessionImportResponse)
def import_session(payload: SessionImportRequest) -> SessionImportResponse:
    try:
        _, image_bytes = decode_data_url(payload.imageDataUrl)
        width, height = get_image_size(image_bytes)
    except ImageDecodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if payload.document is None:
        document = FaceDocument(schemaVersion=1, imageWidth=width, imageHeight=height, faces=[])
    else:
        document = payload.document.model_copy(deep=True)
        document.imageWidth = width
        document.imageHeight = height

    return SessionImportResponse(
        image={"dataUrl": payload.imageDataUrl, "width": width, "height": height},
        document=document,
    )


@app.post("/api/tool-a/faces/create", response_model=FaceRegion)
def create_face(payload: CreateFaceRequest) -> FaceRegion:
    existing_ids = {face.faceId for face in payload.document.faces}
    face_id = generate_face_id(existing_ids)
    return FaceRegion(faceId=face_id, cx=payload.cx, cy=payload.cy, rx=payload.rx, ry=payload.ry)


@app.post("/api/tool-a/detect", response_model=DetectionResponse)
def detect_faces(payload: DetectionRequest) -> DetectionResponse:
    try:
        _, image_bytes = decode_data_url(payload.imageDataUrl)
        candidates = detect_face_candidates(image_bytes, payload.document.faces)
    except (ImageDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DetectionResponse(candidates=candidates)


@app.post("/api/tool-a/export/faces-json", response_model=ExportPayload)
def export_faces_json(payload: ExportFacesRequest) -> ExportPayload:
    try:
        _, image_bytes = decode_data_url(payload.imageDataUrl)
        width, height = get_image_size(image_bytes)
    except ImageDecodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    document = payload.document.model_copy(deep=True)
    document.imageWidth = width
    document.imageHeight = height
    content = document.model_dump_json(indent=2)
    return ExportPayload(fileName="faces.json", content=content, contentType="application/json")


@app.post("/api/tool-a/export/form-entry", response_model=ExportPayload)
def export_form_entry(payload: ExportFormEntryRequest) -> ExportPayload:
    try:
        _, image_bytes = decode_data_url(payload.imageDataUrl)
        width, height = get_image_size(image_bytes)
    except ImageDecodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    document = payload.document.model_copy(deep=True)
    document.imageWidth = width
    document.imageHeight = height
    html = build_form_entry_html(document, payload.imageDataUrl, payload.msFormsUrlPrefix)
    return ExportPayload(fileName="form_entry.html", content=html, contentType="text/html")
