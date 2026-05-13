<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { createFace, detectFaces, exportFacesJson, exportFormEntry, importSession } from './api'
import type { CandidateRegion, FaceDocument, FaceRegion } from './types'

const emptyDocument = (): FaceDocument => ({
  schemaVersion: 1,
  imageWidth: 1,
  imageHeight: 1,
  faces: [],
})

const imageDataUrl = ref('')
const documentState = reactive<FaceDocument>(emptyDocument())
const candidates = ref<CandidateRegion[]>([])
const selectedFaceId = ref<string | null>(null)
const msFormsUrlPrefix = ref('')
const errorMessage = ref('')
const isBusy = ref(false)
const stageSvg = ref<SVGSVGElement | null>(null)
const dragState = ref<{ faceId: string; dx: number; dy: number } | null>(null)

const selectedFace = computed(() => documentState.faces.find((face: FaceRegion) => face.faceId === selectedFaceId.value) ?? null)

function snapshotDocument(): FaceDocument {
  return {
    schemaVersion: documentState.schemaVersion,
    imageWidth: documentState.imageWidth,
    imageHeight: documentState.imageHeight,
    faces: documentState.faces.map((face: FaceRegion) => ({
      faceId: face.faceId,
      cx: face.cx,
      cy: face.cy,
      rx: face.rx,
      ry: face.ry,
      profile: face.profile ? { ...face.profile } : face.profile ?? null,
    })),
  }
}

function syncDocument(nextDocument: FaceDocument) {
  documentState.schemaVersion = nextDocument.schemaVersion
  documentState.imageWidth = nextDocument.imageWidth
  documentState.imageHeight = nextDocument.imageHeight
  documentState.faces = nextDocument.faces.map((face) => ({ ...face }))
}

function clearError() {
  errorMessage.value = ''
}

function setError(error: unknown) {
  errorMessage.value = error instanceof Error ? error.message : 'Unexpected error'
}

async function onImageSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) {
    return
  }

  clearError()
  candidates.value = []
  selectedFaceId.value = null

  try {
    isBusy.value = true
    imageDataUrl.value = await readAsDataUrl(file)
    const response = await importSession(imageDataUrl.value, documentState.faces.length ? snapshotDocument() : null)
    syncDocument(response.document)
  } catch (error) {
    setError(error)
  } finally {
    isBusy.value = false
  }
}

async function onJsonSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !imageDataUrl.value) {
    setError('Load an image before importing face JSON.')
    return
  }

  clearError()
  try {
    isBusy.value = true
    const raw = await file.text()
    const parsed = JSON.parse(raw) as FaceDocument
    const response = await importSession(imageDataUrl.value, parsed)
    syncDocument(response.document)
    candidates.value = []
    selectedFaceId.value = response.document.faces[0]?.faceId ?? null
  } catch (error) {
    setError(error)
  } finally {
    isBusy.value = false
  }
}

async function addManualFace() {
  if (!imageDataUrl.value) {
    setError('Load an image before adding a face.')
    return
  }

  clearError()
  try {
    const newFace = await createFace(snapshotDocument(), {
      cx: 0.5,
      cy: 0.5,
      rx: 0.05,
      ry: 0.075,
      profile: null,
    })
    documentState.faces.push(newFace)
    selectedFaceId.value = newFace.faceId
  } catch (error) {
    setError(error)
  }
}

function deleteSelectedFace() {
  if (!selectedFace.value) {
    return
  }

  const index = documentState.faces.findIndex((face: FaceRegion) => face.faceId === selectedFace.value?.faceId)
  if (index >= 0) {
    documentState.faces.splice(index, 1)
    selectedFaceId.value = documentState.faces[0]?.faceId ?? null
  }
}

async function runDetection() {
  if (!imageDataUrl.value) {
    setError('Load an image before running face detection.')
    return
  }

  clearError()
  try {
    isBusy.value = true
    const response = await detectFaces(imageDataUrl.value, snapshotDocument())
    candidates.value = response.candidates
  } catch (error) {
    setError(error)
  } finally {
    isBusy.value = false
  }
}

async function acceptCandidate(candidate: CandidateRegion) {
  clearError()
  try {
    const face = await createFace(snapshotDocument(), {
      cx: candidate.cx,
      cy: candidate.cy,
      rx: candidate.rx,
      ry: candidate.ry,
      profile: null,
    })
    documentState.faces.push(face)
    selectedFaceId.value = face.faceId
    candidates.value = candidates.value.filter((item: CandidateRegion) => item.candidateId !== candidate.candidateId)
  } catch (error) {
    setError(error)
  }
}

function ignoreCandidate(candidateId: string) {
  candidates.value = candidates.value.filter((item: CandidateRegion) => item.candidateId !== candidateId)
}

async function downloadFacesJson() {
  if (!imageDataUrl.value) {
    setError('Load an image before exporting faces.json.')
    return
  }

  clearError()
  try {
    const payload = await exportFacesJson(imageDataUrl.value, snapshotDocument())
    downloadFile(payload.fileName, payload.content, payload.contentType)
  } catch (error) {
    setError(error)
  }
}

async function downloadFormEntry() {
  if (!imageDataUrl.value) {
    setError('Load an image before exporting form_entry.html.')
    return
  }

  clearError()
  try {
    const payload = await exportFormEntry(imageDataUrl.value, snapshotDocument(), msFormsUrlPrefix.value)
    downloadFile(payload.fileName, payload.content, payload.contentType)
  } catch (error) {
    setError(error)
  }
}

function beginDrag(face: FaceRegion, event: PointerEvent) {
  if (!stageSvg.value) {
    return
  }

  const point = getSvgPoint(stageSvg.value, event)
  dragState.value = {
    faceId: face.faceId,
    dx: face.cx - point.x,
    dy: face.cy - point.y,
  }
  selectedFaceId.value = face.faceId
}

function onPointerMove(event: PointerEvent) {
  if (!dragState.value || !stageSvg.value) {
    return
  }

  const point = getSvgPoint(stageSvg.value, event)
  const face = documentState.faces.find((item: FaceRegion) => item.faceId === dragState.value?.faceId)
  if (!face) {
    return
  }

  face.cx = clamp(point.x + dragState.value.dx, face.rx, 1 - face.rx)
  face.cy = clamp(point.y + dragState.value.dy, face.ry, 1 - face.ry)
}

function endDrag() {
  dragState.value = null
}

function updateSelectedFace(axis: 'cx' | 'cy' | 'rx' | 'ry', value: number) {
  if (!selectedFace.value) {
    return
  }

  selectedFace.value[axis] = clamp(value, axis === 'rx' ? 0.005 : axis === 'ry' ? 0.01 : 0, 1)
  selectedFace.value.cx = clamp(selectedFace.value.cx, selectedFace.value.rx, 1 - selectedFace.value.rx)
  selectedFace.value.cy = clamp(selectedFace.value.cy, selectedFace.value.ry, 1 - selectedFace.value.ry)
}

function handleRangeInput(axis: 'cx' | 'cy' | 'rx' | 'ry', event: Event) {
  const target = event.target as HTMLInputElement | null
  if (!target) {
    return
  }

  updateSelectedFace(axis, Number(target.value))
}

function faceClass(faceId: string) {
  return faceId === selectedFaceId.value ? 'face face--selected' : 'face'
}

async function readAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(new Error('Unable to read the selected file.'))
    reader.readAsDataURL(file)
  })
}

function downloadFile(fileName: string, content: string, contentType: string) {
  const blob = new Blob([content], { type: contentType })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = fileName
  anchor.click()
  URL.revokeObjectURL(url)
}

function getSvgPoint(svg: SVGSVGElement, event: PointerEvent) {
  const rect = svg.getBoundingClientRect()
  return {
    x: (event.clientX - rect.left) / rect.width,
    y: (event.clientY - rect.top) / rect.height,
  }
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}
</script>

<template>
  <div class="app-shell">
    <header class="hero">
      <div>
        <p class="eyebrow">Tool A</p>
        <h1>Face Region Editor</h1>
        <p class="hero-copy">
          Load a group photo, create stable face regions, review re-detection candidates, and export a standalone form entry page.
        </p>
      </div>
      <div class="hero-actions">
        <label class="file-input">
          <span>Load Image</span>
          <input type="file" accept="image/*" @change="onImageSelected" />
        </label>
        <label class="file-input file-input--secondary">
          <span>Load Faces JSON</span>
          <input type="file" accept=".json,application/json" @change="onJsonSelected" />
        </label>
      </div>
    </header>

    <p v-if="errorMessage" class="banner banner--error">{{ errorMessage }}</p>
    <p class="banner banner--privacy">Internal company use only. Contains personal information. Do not distribute externally.</p>

    <main class="workspace">
      <section class="stage-panel">
        <div
          class="stage"
          :class="{ 'stage--empty': !imageDataUrl }"
          @pointermove="onPointerMove"
          @pointerup="endDrag"
          @pointerleave="endDrag"
        >
          <template v-if="imageDataUrl">
            <img class="stage-image" :src="imageDataUrl" alt="Loaded group photo" />
            <svg ref="stageSvg" class="stage-overlay" viewBox="0 0 1 1" preserveAspectRatio="none">
              <ellipse
                v-for="face in documentState.faces"
                :key="face.faceId"
                :class="faceClass(face.faceId)"
                :cx="face.cx"
                :cy="face.cy"
                :rx="face.rx"
                :ry="face.ry"
                @pointerdown.stop="beginDrag(face, $event)"
                @click.stop="selectedFaceId = face.faceId"
              />
              <ellipse
                v-for="candidate in candidates"
                :key="candidate.candidateId"
                class="candidate"
                :cx="candidate.cx"
                :cy="candidate.cy"
                :rx="candidate.rx"
                :ry="candidate.ry"
              />
            </svg>
          </template>
          <div v-else class="stage-empty">Load an image to start editing face regions.</div>
        </div>
        <div class="toolbar">
          <button class="action" type="button" @click="addManualFace">Add Face</button>
          <button class="action action--secondary" type="button" :disabled="isBusy" @click="runDetection">
            {{ isBusy ? 'Working...' : 'Run Detection' }}
          </button>
          <button class="action action--ghost" type="button" @click="deleteSelectedFace">Delete Selected</button>
        </div>
      </section>

      <aside class="side-panel">
        <section class="panel">
          <h2>Selection</h2>
          <template v-if="selectedFace">
            <p class="meta">{{ selectedFace.faceId }}</p>
            <label>
              <span>Center X</span>
              <input :value="selectedFace.cx" type="range" min="0" max="1" step="0.001" @input="handleRangeInput('cx', $event)" />
            </label>
            <label>
              <span>Center Y</span>
              <input :value="selectedFace.cy" type="range" min="0" max="1" step="0.001" @input="handleRangeInput('cy', $event)" />
            </label>
            <label>
              <span>Radius X</span>
              <input :value="selectedFace.rx" type="range" min="0.005" max="0.25" step="0.001" @input="handleRangeInput('rx', $event)" />
            </label>
            <label>
              <span>Radius Y</span>
              <input :value="selectedFace.ry" type="range" min="0.01" max="0.35" step="0.001" @input="handleRangeInput('ry', $event)" />
            </label>
          </template>
          <p v-else class="muted">Select a face to edit its ellipse.</p>
        </section>

        <section class="panel">
          <h2>Faces</h2>
          <ul class="entity-list">
            <li v-for="face in documentState.faces" :key="face.faceId">
              <button type="button" class="entity" :class="{ 'entity--active': face.faceId === selectedFaceId }" @click="selectedFaceId = face.faceId">
                <strong>{{ face.faceId }}</strong>
                <span>{{ face.profile?.fullName ?? 'No profile data' }}</span>
              </button>
            </li>
          </ul>
        </section>

        <section class="panel">
          <div class="panel-heading">
            <h2>Candidates</h2>
            <span class="meta">{{ candidates.length }}</span>
          </div>
          <ul class="entity-list">
            <li v-for="candidate in candidates" :key="candidate.candidateId">
              <div class="candidate-card">
                <div>
                  <strong>{{ candidate.candidateId }}</strong>
                  <span>Confidence: {{ candidate.confidence?.toFixed(2) ?? 'n/a' }}</span>
                </div>
                <div class="candidate-actions">
                  <button type="button" class="mini" @click="acceptCandidate(candidate)">Accept</button>
                  <button type="button" class="mini mini--ghost" @click="ignoreCandidate(candidate.candidateId)">Ignore</button>
                </div>
              </div>
            </li>
          </ul>
        </section>

        <section class="panel">
          <h2>Export</h2>
          <label>
            <span>MS Forms URL Prefix</span>
            <input v-model="msFormsUrlPrefix" type="text" placeholder="https://forms.office.com/...=" />
          </label>
          <div class="export-actions">
            <button class="action" type="button" @click="downloadFacesJson">Export faces.json</button>
            <button class="action action--secondary" type="button" @click="downloadFormEntry">Export form_entry.html</button>
          </div>
        </section>
      </aside>
    </main>
  </div>
</template>
