export type FaceProfile = Record<string, unknown> & {
  fullName?: string
  nickname?: string
  department?: string
  email?: string
}

export type FaceRegion = {
  faceId: string
  cx: number
  cy: number
  rx: number
  ry: number
  profile?: FaceProfile | null
}

export type CandidateRegion = {
  candidateId: string
  cx: number
  cy: number
  rx: number
  ry: number
  confidence?: number | null
}

export type FaceDocument = {
  schemaVersion: number
  imageWidth: number
  imageHeight: number
  faces: FaceRegion[]
}

export type ExportPayload = {
  fileName: string
  content: string
  contentType: string
}

export type SessionImportResponse = {
  image: {
    dataUrl: string
    width: number
    height: number
  }
  document: FaceDocument
}
