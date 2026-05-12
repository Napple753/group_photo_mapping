import type { CandidateRegion, ExportPayload, FaceDocument, FaceRegion, SessionImportResponse } from './types'

const API_BASE = 'http://127.0.0.1:8000/api'

async function requestJson<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail ?? 'Request failed')
  }

  return response.json() as Promise<T>
}

export function importSession(imageDataUrl: string, document: FaceDocument | null) {
  return requestJson<SessionImportResponse>('/tool-a/session/import', { imageDataUrl, document })
}

export function createFace(document: FaceDocument, face: Omit<FaceRegion, 'faceId'>) {
  return requestJson<FaceRegion>('/tool-a/faces/create', {
    document,
    cx: face.cx,
    cy: face.cy,
    rx: face.rx,
    ry: face.ry,
  })
}

export function detectFaces(imageDataUrl: string, document: FaceDocument) {
  return requestJson<{ candidates: CandidateRegion[] }>('/tool-a/detect', { imageDataUrl, document })
}

export function exportFacesJson(imageDataUrl: string, document: FaceDocument) {
  return requestJson<ExportPayload>('/tool-a/export/faces-json', { imageDataUrl, document })
}

export function exportFormEntry(imageDataUrl: string, document: FaceDocument, msFormsUrlPrefix: string) {
  return requestJson<ExportPayload>('/tool-a/export/form-entry', {
    imageDataUrl,
    document,
    msFormsUrlPrefix,
  })
}
