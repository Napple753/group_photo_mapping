from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FaceRegion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    faceId: str = Field(min_length=3)
    cx: float = Field(ge=0.0, le=1.0)
    cy: float = Field(ge=0.0, le=1.0)
    rx: float = Field(gt=0.0, le=1.0)
    ry: float = Field(gt=0.0, le=1.0)
    profile: dict[str, str] | None = None


class CandidateRegion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidateId: str = Field(min_length=3)
    cx: float = Field(ge=0.0, le=1.0)
    cy: float = Field(ge=0.0, le=1.0)
    rx: float = Field(gt=0.0, le=1.0)
    ry: float = Field(gt=0.0, le=1.0)
    confidencePct: int | None = Field(default=None, ge=0, le=100)


class DetectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    imageDataUrl: str = Field(min_length=32)
    importedJson: bool = False
    existingFaces: list[FaceRegion] = Field(default_factory=list)


class DetectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["initial", "redetect"]
    detections: list[CandidateRegion]
    warnings: list[str] = Field(default_factory=list)


class FaceIdResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    faceId: str


class ExportFacesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    imageWidth: int = Field(gt=0)
    imageHeight: int = Field(gt=0)
    faces: list[FaceRegion]


class ExportHtmlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    imageDataUrl: str = Field(min_length=32)
    faces: list[FaceRegion]
    msFormsUrlPrefix: str = ""
    includePrivacyNotice: bool = False

    @field_validator("msFormsUrlPrefix")
    @classmethod
    def normalize_prefix(cls, value: str) -> str:
        return value.strip()


class ExportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    mimeType: str
    content: str
    warnings: list[str] = Field(default_factory=list)


class ImportedFacesDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: int
    imageWidth: int = Field(gt=0)
    imageHeight: int = Field(gt=0)
    faces: list[FaceRegion]


class ImportFacesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: ImportedFacesDocument


class ImportFacesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    imageWidth: int
    imageHeight: int
    faces: list[FaceRegion]


class UiWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: Literal["warning", "error"]
    message: str
