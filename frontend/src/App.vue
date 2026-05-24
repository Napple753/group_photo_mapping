<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import { apiRequest } from './lib/api'
import { downloadTextFile } from './lib/download'

const imageDataUrl = ref('')
const imageWidth = ref(0)
const imageHeight = ref(0)
const faces = ref([])
const candidates = ref([])
const importedJson = ref(false)
const overlayOpen = ref(false)
const activeTab = ref('editor')
const selectedFaceId = ref('')
const selectedCandidateId = ref('')
const loadingDetection = ref(false)
const message = ref({ severity: '', text: '' })
const msFormsUrlPrefix = ref('')
const includePrivacyNotice = ref(false)
const imageInput = ref(null)
const jsonInput = ref(null)
const stageMedia = ref(null)
const stageRect = ref({ width: 1, height: 1 })
const dragState = ref(null)
let resizeObserver = null

const selectedFace = computed(() => faces.value.find((face) => face.faceId === selectedFaceId.value) ?? null)
const selectedCandidate = computed(() => candidates.value.find((candidate) => candidate.candidateId === selectedCandidateId.value) ?? null)
const compactHeader = computed(() => Boolean(imageDataUrl.value))
const hasImage = computed(() => Boolean(imageDataUrl.value))
const unifiedItems = computed(() => [
  ...faces.value.map((face) => ({ kind: 'face', key: face.faceId, data: face })),
  ...candidates.value.map((candidate) => ({ kind: 'candidate', key: candidate.candidateId, data: candidate })),
])

function setMessage(severity, text) {
  message.value = { severity, text }
}

function clearMessage() {
  message.value = { severity: '', text: '' }
}

function resetEditorSession() {
  faces.value = []
  candidates.value = []
  importedJson.value = false
  selectedFaceId.value = ''
  selectedCandidateId.value = ''
  overlayOpen.value = false
  activeTab.value = 'editor'
}

function openImagePicker() {
  imageInput.value?.click()
}

function openJsonPicker() {
  if (!hasImage.value) {
    setMessage('error', 'Load an image before importing face JSON.')
    return
  }
  jsonInput.value?.click()
}

async function onImageSelected(event) {
  const [file] = event.target.files ?? []
  if (!file) {
    return
  }

  clearMessage()
  resetEditorSession()

  const dataUrl = await readFileAsDataUrl(file)
  const metadata = await readImageMetadata(dataUrl)
  imageDataUrl.value = dataUrl
  imageWidth.value = metadata.width
  imageHeight.value = metadata.height
  overlayOpen.value = true
}

async function onFacesJsonSelected(event) {
  const [file] = event.target.files ?? []
  if (!file) {
    return
  }

  clearMessage()

  try {
    const text = await file.text()
    const document = JSON.parse(text)
    const response = await apiRequest('/api/tool-a/import-faces', {
      method: 'POST',
      body: JSON.stringify({ document }),
    })

    faces.value = response.faces
    importedJson.value = true
    candidates.value = []
    selectedFaceId.value = ''
    selectedCandidateId.value = ''

    await runDetection()
  } catch (error) {
    setMessage('error', error.message || 'Unable to import face JSON.')
  } finally {
    event.target.value = ''
  }
}

async function runDetection() {
  if (!hasImage.value) {
    setMessage('error', 'Load an image before running face detection.')
    return
  }

  loadingDetection.value = true
  clearMessage()

  try {
    const response = await apiRequest('/api/tool-a/detect', {
      method: 'POST',
      body: JSON.stringify({
        imageDataUrl: imageDataUrl.value,
        importedJson: importedJson.value,
        existingFaces: faces.value,
      }),
    })

    if (response.mode === 'initial') {
      const createdFaces = []
      for (const detection of response.detections) {
        const faceIdPayload = await apiRequest('/api/tool-a/face-id', { method: 'POST', body: '{}' })
        createdFaces.push({
          faceId: faceIdPayload.faceId,
          cx: detection.cx,
          cy: detection.cy,
          rx: detection.rx,
          ry: detection.ry,
        })
      }
      faces.value = createdFaces
      candidates.value = []
      selectedFaceId.value = createdFaces[0]?.faceId ?? ''
      selectedCandidateId.value = ''
    } else {
      candidates.value = response.detections
      selectedCandidateId.value = response.detections[0]?.candidateId ?? ''
      selectedFaceId.value = ''
    }

    if (response.warnings.length > 0) {
      setMessage('warning', response.warnings.join(' '))
    }
    overlayOpen.value = false
    activeTab.value = response.mode === 'initial' ? 'editor' : 'faces'
  } catch (error) {
    setMessage('error', error.message || 'Unable to run detection.')
  } finally {
    loadingDetection.value = false
  }
}

async function addFace() {
  if (!hasImage.value) {
    setMessage('error', 'Load an image to start editing faces.')
    return
  }

  try {
    const response = await apiRequest('/api/tool-a/face-id', { method: 'POST', body: '{}' })
    const face = { faceId: response.faceId, cx: 0.5, cy: 0.5, rx: 0.03, ry: 0.05 }
    faces.value = [...faces.value, face]
    selectedFaceId.value = face.faceId
    selectedCandidateId.value = ''
    activeTab.value = 'editor'
  } catch (error) {
    setMessage('error', error.message || 'Unable to create a new face.')
  }
}

function deleteSelectedFace() {
  if (!selectedFace.value) {
    return
  }

  faces.value = faces.value.filter((face) => face.faceId !== selectedFace.value.faceId)
  selectedFaceId.value = faces.value[0]?.faceId ?? ''
}

function updateSelectedFace(field, value) {
  if (!selectedFace.value) {
    return
  }

  faces.value = faces.value.map((face) => {
    if (face.faceId !== selectedFace.value.faceId) {
      return face
    }

    const nextFace = { ...face, [field]: Number(value) }
    nextFace.cx = clamp(nextFace.cx, nextFace.rx, 1 - nextFace.rx)
    nextFace.cy = clamp(nextFace.cy, nextFace.ry, 1 - nextFace.ry)
    nextFace.rx = clamp(nextFace.rx, 0.005, 0.25)
    nextFace.ry = clamp(nextFace.ry, 0.01, 0.35)
    return nextFace
  })
}

async function acceptCandidate(candidate) {
  try {
    await addFaceFromCandidate(candidate)
    candidates.value = candidates.value.filter((item) => item.candidateId !== candidate.candidateId)
    selectedCandidateId.value = ''
  } catch (error) {
    setMessage('error', error.message || 'Unable to accept the selected candidate.')
  }
}

async function addFaceFromCandidate(candidate) {
  const response = await apiRequest('/api/tool-a/face-id', { method: 'POST', body: '{}' })
  const face = {
    faceId: response.faceId,
    cx: candidate.cx,
    cy: candidate.cy,
    rx: candidate.rx,
    ry: candidate.ry,
  }
  faces.value = [...faces.value, face]
  selectedFaceId.value = face.faceId
  selectedCandidateId.value = ''
  activeTab.value = 'editor'
}

function ignoreCandidate(candidateId) {
  candidates.value = candidates.value.filter((item) => item.candidateId !== candidateId)
  if (selectedCandidateId.value === candidateId) {
    selectedCandidateId.value = candidates.value[0]?.candidateId ?? ''
  }
}

function selectFace(faceId) {
  selectedFaceId.value = faceId
  selectedCandidateId.value = ''
  activeTab.value = 'editor'
}

function selectCandidate(candidateId) {
  selectedCandidateId.value = candidateId
  selectedFaceId.value = ''
  activeTab.value = 'faces'
}

async function exportFacesJson() {
  try {
    const response = await apiRequest('/api/tool-a/export/faces-json', {
      method: 'POST',
      body: JSON.stringify({
        imageWidth: imageWidth.value,
        imageHeight: imageHeight.value,
        faces: faces.value,
      }),
    })
    downloadTextFile(response.filename, response.content, response.mimeType)
  } catch (error) {
    setMessage('error', error.message || 'Unable to export faces.json.')
  }
}

async function exportFormEntry() {
  try {
    const response = await apiRequest('/api/tool-a/export/form-entry', {
      method: 'POST',
      body: JSON.stringify({
        imageDataUrl: imageDataUrl.value,
        faces: faces.value,
        msFormsUrlPrefix: msFormsUrlPrefix.value,
        includePrivacyNotice: includePrivacyNotice.value,
      }),
    })

    if (response.warnings?.length) {
      setMessage('warning', response.warnings.join(' '))
    }

    downloadTextFile(response.filename, response.content, response.mimeType)
  } catch (error) {
    setMessage('error', error.message || 'Unable to export form_entry.html.')
  }
}

function syncStageRect() {
  if (!stageMedia.value) {
    return
  }

  const rect = stageMedia.value.getBoundingClientRect()
  stageRect.value = {
    width: rect.width || 1,
    height: rect.height || 1,
  }
}

async function onImageLoaded() {
  await nextTick()
  syncStageRect()
}

function onFacePointerDown(face, event) {
  if (event.button !== 0) {
    return
  }

  selectFace(face.faceId)
  dragState.value = {
    faceId: face.faceId,
    startX: event.clientX,
    startY: event.clientY,
    originCx: face.cx,
    originCy: face.cy,
  }

  event.target.setPointerCapture(event.pointerId)
}

function onFacePointerMove(event) {
  if (!dragState.value) {
    return
  }

  const face = faces.value.find((item) => item.faceId === dragState.value.faceId)
  if (!face) {
    return
  }

  const dx = (event.clientX - dragState.value.startX) / stageRect.value.width
  const dy = (event.clientY - dragState.value.startY) / stageRect.value.height
  updateSelectedFace('cx', dragState.value.originCx + dx)
  updateSelectedFace('cy', dragState.value.originCy + dy)
}

function onFacePointerUp() {
  dragState.value = null
}

onMounted(() => {
  window.addEventListener('resize', syncStageRect)

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      syncStageRect()
    })
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncStageRect)
  resizeObserver?.disconnect()
})

function warningClass(severity) {
  return severity ? `banner banner--${severity}` : 'banner'
}

function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, Number(value)))
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(new Error('Unable to read the selected image.'))
    reader.readAsDataURL(file)
  })
}

function readImageMetadata(src) {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight })
    image.onerror = () => reject(new Error('Unable to decode the selected image.'))
    image.src = src
  })
}
</script>

<template>
  <div class="page-shell">
    <header :class="['page-header', { 'page-header--compact': compactHeader }]">
      <div class="title-block">
        <h1>Face Region Editor</h1>
        <p v-if="!compactHeader" class="intro-copy">
          Load a group photo, review detected regions, edit ellipse geometry, and export standalone outputs.
        </p>
      </div>
      <div class="header-actions">
        <button class="primary-button" type="button" @click="openImagePicker">Load Image</button>
        <input ref="imageInput" accept="image/jpeg,image/png,image/webp" class="hidden-input" type="file" @change="onImageSelected" />
        <input ref="jsonInput" accept="application/json" class="hidden-input" type="file" @change="onFacesJsonSelected" />
      </div>
    </header>

    <div v-if="message.text" :class="warningClass(message.severity)">
      {{ message.text }}
    </div>

    <main class="workspace">
      <section class="stage-panel">
        <div v-if="!hasImage" class="empty-state">Load an image to start editing face regions.</div>

        <div v-else class="stage-frame">
          <div ref="stageMedia" class="stage-media">
            <img class="photo" :src="imageDataUrl" alt="Loaded group photo" @load="onImageLoaded" />

            <div v-if="overlayOpen" class="overlay-card">
              <button class="primary-button" type="button" :disabled="loadingDetection" @click="runDetection">
                {{ loadingDetection ? 'Running Detection...' : 'Detect Faces' }}
              </button>
              <button class="secondary-button" type="button" @click="openJsonPicker">Load Face JSON</button>
            </div>

            <svg class="stage-svg" :viewBox="`0 0 ${imageWidth || 1} ${imageHeight || 1}`" preserveAspectRatio="none">
              <ellipse
                v-for="face in faces"
                :key="face.faceId"
                class="face-ellipse"
                :class="{ 'face-ellipse--selected': selectedFaceId === face.faceId }"
                :cx="face.cx * imageWidth"
                :cy="face.cy * imageHeight"
                :rx="face.rx * imageWidth"
                :ry="face.ry * imageHeight"
                @click.stop="selectFace(face.faceId)"
                @pointerdown="onFacePointerDown(face, $event)"
                @pointermove="onFacePointerMove"
                @pointerup="onFacePointerUp"
              />
              <ellipse
                v-for="candidate in candidates"
                :key="candidate.candidateId"
                class="candidate-ellipse"
                :class="{ 'candidate-ellipse--selected': selectedCandidateId === candidate.candidateId }"
                :cx="candidate.cx * imageWidth"
                :cy="candidate.cy * imageHeight"
                :rx="candidate.rx * imageWidth"
                :ry="candidate.ry * imageHeight"
                @click.stop="selectCandidate(candidate.candidateId)"
              />
            </svg>
          </div>
        </div>

        <div class="stage-toolbar">
          <button class="secondary-button" type="button" :disabled="loadingDetection || !hasImage" @click="runDetection">
            {{ loadingDetection ? 'Detecting...' : 'Run Detection' }}
          </button>
        </div>
      </section>

      <aside class="sidebar">
        <div class="tab-list">
          <button :class="['tab-button', { 'tab-button--active': activeTab === 'editor' }]" type="button" @click="activeTab = 'editor'">Face Editor</button>
          <button :class="['tab-button', { 'tab-button--active': activeTab === 'faces' }]" type="button" @click="activeTab = 'faces'">Faces</button>
          <button :class="['tab-button', { 'tab-button--active': activeTab === 'export' }]" type="button" @click="activeTab = 'export'">Export</button>
        </div>

        <section v-if="activeTab === 'editor'" class="panel">
          <h2>Face Editor</h2>
          <template v-if="!hasImage">
            <p class="muted-copy">Load an image to start editing faces.</p>
          </template>
          <template v-else-if="selectedCandidate">
            <div class="editor-actions">
              <button class="secondary-button" type="button" @click="addFace">Add Face</button>
              <button class="ghost-button" type="button" disabled>Delete Selected</button>
            </div>
            <p class="muted-copy">Accept the candidate from the list before editing its ellipse.</p>
            <div class="slider-group slider-group--disabled">
              <label>Center X <input disabled type="range" min="0" max="1" step="0.001" /></label>
              <label>Center Y <input disabled type="range" min="0" max="1" step="0.001" /></label>
              <label>Radius X <input disabled type="range" min="0.005" max="0.25" step="0.001" /></label>
              <label>Radius Y <input disabled type="range" min="0.01" max="0.35" step="0.001" /></label>
            </div>
          </template>
          <template v-else-if="selectedFace">
            <div class="editor-actions">
              <button class="secondary-button" type="button" @click="addFace">Add Face</button>
              <button class="ghost-button" type="button" @click="deleteSelectedFace">Delete Selected</button>
            </div>
            <p class="face-id">{{ selectedFace.faceId }}</p>
            <div class="slider-group">
              <label>
                Center X
                <input :value="selectedFace.cx" type="range" min="0" max="1" step="0.001" @input="updateSelectedFace('cx', $event.target.value)" />
              </label>
              <label>
                Center Y
                <input :value="selectedFace.cy" type="range" min="0" max="1" step="0.001" @input="updateSelectedFace('cy', $event.target.value)" />
              </label>
              <label>
                Radius X
                <input :value="selectedFace.rx" type="range" min="0.005" max="0.25" step="0.001" @input="updateSelectedFace('rx', $event.target.value)" />
              </label>
              <label>
                Radius Y
                <input :value="selectedFace.ry" type="range" min="0.01" max="0.35" step="0.001" @input="updateSelectedFace('ry', $event.target.value)" />
              </label>
            </div>
          </template>
          <template v-else>
            <div class="editor-actions">
              <button class="secondary-button" type="button" @click="addFace">Add Face</button>
              <button class="ghost-button" type="button" disabled>Delete Selected</button>
            </div>
            <p class="muted-copy">Select a face or add a new one to edit its ellipse.</p>
          </template>
        </section>

        <section v-else-if="activeTab === 'faces'" class="panel">
          <div class="panel-header">
            <h2>Faces</h2>
            <p class="muted-copy">{{ unifiedItems.length }} items</p>
          </div>
          <div class="face-list">
            <article
              v-for="item in unifiedItems"
              :key="item.key"
              :class="['list-item', `list-item--${item.kind}`, {
                'list-item--selected': item.kind === 'face' ? selectedFaceId === item.data.faceId : selectedCandidateId === item.data.candidateId,
              }]"
              @click="item.kind === 'face' ? selectFace(item.data.faceId) : selectCandidate(item.data.candidateId)"
            >
              <template v-if="item.kind === 'face'">
                <strong>{{ item.data.faceId }}</strong>
                <span>{{ item.data.profile?.fullName ?? 'No profile data' }}</span>
              </template>
              <template v-else>
                <strong>{{ item.data.candidateId }}</strong>
                <span>{{ item.data.confidencePct != null ? `${item.data.confidencePct}% confidence` : 'No confidence data' }}</span>
                <div class="candidate-actions">
                  <button class="primary-button" type="button" @click.stop="acceptCandidate(item.data)">Accept</button>
                  <button class="ghost-button" type="button" @click.stop="ignoreCandidate(item.data.candidateId)">Ignore</button>
                </div>
              </template>
            </article>
          </div>
        </section>

        <section v-else class="panel">
          <h2>Export</h2>
          <label class="text-field">
            MS Forms URL Prefix
            <input v-model="msFormsUrlPrefix" placeholder="https://forms.office.com/...=" type="text" />
          </label>
          <label class="toggle-row">
            <input v-model="includePrivacyNotice" type="checkbox" />
            Include privacy notice
          </label>
          <div class="export-actions">
            <button class="secondary-button" type="button" :disabled="!faces.length" @click="exportFacesJson">Export faces.json</button>
            <button class="primary-button" type="button" :disabled="!faces.length || !hasImage" @click="exportFormEntry">Export form_entry.html</button>
          </div>
        </section>
      </aside>
    </main>
  </div>
</template>
