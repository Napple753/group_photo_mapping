# Group Photo Mapping

Group Photo Mapping is a local toolchain for building an interactive people directory from a large group photo.

The system scope is split into two tools:

- Tool A: face region editing and `form_entry.html` generation
- Tool B: CSV merge and final `index.html` / `faces.enriched.json` generation

## Repository Contents

- `backend/`: FastAPI backend for Tool A and Tool B APIs
- `frontend/`: Vue frontend for Tool A
- `group_photo_face_mapping_spec.md`: primary product specification for Tool A and Tool B
- `tool_a_ui_spec.md`: Tool A UI structure, state model, and interaction rules
- `README.md`: repository overview and local run guide

## Current Status

The repository now contains a runnable initial implementation of Tool A plus the supporting specifications.

Implemented in the current branch:

- Tool A frontend shell and editor layout
- local backend API with health endpoint and Tool A routes
- backend-driven face detection flow for Tool A
- bundled OpenCV YuNet model for backend face detection
- image load flow
- manual face creation and deletion
- accepted/candidate unified list behavior
- `faces.json` export
- standalone `form_entry.html` export
- Python 3.11 backend runtime with OpenCV support

Current limitation:

- detection quality still depends on image quality, scale, and face visibility
- Tool A treats backend detection failures as errors instead of silently falling back to a browser-side detector

## Python Version

The backend now targets Python 3.11.

VS Code is configured to use:

- `backend/.venv311/bin/python`

If the Python extension still shows unresolved imports, reload the window or reselect the interpreter for the workspace.

## Backend Setup

```bash
cd backend
python3.11 -m venv .venv311
source .venv311/bin/activate
pip install -r requirements.txt
```

Run the backend:

```bash
cd backend
.venv311/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

- `http://127.0.0.1:8000/api/health`

## Frontend Setup

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

- `http://127.0.0.1:5173/`

The Vite dev server proxies `/api` to the backend at `http://127.0.0.1:8000`.

## Spec References

Read the specifications in this order:

1. `group_photo_face_mapping_spec.md`
2. `tool_a_ui_spec.md`

The specifications remain the source of truth for behavior and file contracts.

## Scope Notes

- UI language is `en-US`
- outputs are intended to be portable static HTML files
- face detection provides suggestions only; human-edited regions are authoritative
- Tool A uses backend-side face detection only in the current implementation
- the backend detector uses a bundled local YuNet model through OpenCV
- if backend detection fails or is unavailable, the UI shows the failure as an error banner
- Tool A preserves `profile` data from `faces.enriched.json` but does not edit those fields
