from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FaceProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    fullName: str | None = None
    nickname: str | None = None
    department: str | None = None
    email: str | None = None


class FaceRegion(BaseModel):
    faceId: str = Field(min_length=3)
    cx: float
    cy: float
    rx: float
    ry: float
    profile: FaceProfile | dict[str, Any] | None = None

    @field_validator("cx", "cy", "rx", "ry")
    @classmethod
    def validate_ratio(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("Face coordinates must be normalized between 0.0 and 1.0")
        return value


class FaceDocument(BaseModel):
    schemaVersion: int = 1
    imageWidth: int = Field(gt=0)
    imageHeight: int = Field(gt=0)
    faces: list[FaceRegion] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_unique_ids(self) -> "FaceDocument":
        face_ids = [face.faceId for face in self.faces]
        if len(face_ids) != len(set(face_ids)):
            raise ValueError("Duplicate faceId detected in face document")
        return self


class ImageAsset(BaseModel):
    dataUrl: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class SessionImportRequest(BaseModel):
    imageDataUrl: str
    document: FaceDocument | None = None


class SessionImportResponse(BaseModel):
    image: ImageAsset
    document: FaceDocument


class CreateFaceRequest(BaseModel):
    document: FaceDocument
    cx: float
    cy: float
    rx: float
    ry: float

    @field_validator("cx", "cy", "rx", "ry")
    @classmethod
    def validate_ratio(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("Face coordinates must be normalized between 0.0 and 1.0")
        return value


class CandidateRegion(BaseModel):
    candidateId: str
    cx: float
    cy: float
    rx: float
    ry: float
    confidence: float | None = None


class DetectionRequest(BaseModel):
    imageDataUrl: str
    document: FaceDocument


class DetectionResponse(BaseModel):
    candidates: list[CandidateRegion]


class ExportFacesRequest(BaseModel):
    imageDataUrl: str
    document: FaceDocument


class ExportFormEntryRequest(ExportFacesRequest):
    msFormsUrlPrefix: str = Field(min_length=1)

    @field_validator("msFormsUrlPrefix")
    @classmethod
    def validate_prefix(cls, value: str) -> str:
        if not value.endswith("="):
            raise ValueError("MS Forms URL prefix must end with '='")
        return value


class ExportPayload(BaseModel):
    fileName: str
    content: str
    contentType: str
