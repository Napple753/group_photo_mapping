# Group Photo Mapping

This repository now contains the initial implementation of Tool A from the specification.

## Structure

- `backend/`: FastAPI application for image import, face ID generation, face detection, and export
- `frontend/`: Vue.js application for editing face regions and exporting outputs
- `group_photo_face_mapping_spec.md`: source specification

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend starts on `http://127.0.0.1:8000`.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The frontend starts on `http://127.0.0.1:5173`.

## Implemented in this first pass

- Image load and project import
- Stable face ID generation from the backend
- Manual face creation and deletion
- SVG overlay rendering with drag-to-move
- Slider-based ellipse resizing
- Face re-detection with candidate overlays
- Candidate accept and ignore flows
- `faces.json` export
- Standalone `form_entry.html` export

## Not implemented yet

- Persisted project sessions on disk
- Full keyboard shortcuts
- Resize handles directly on the canvas
- Tool B CSV ingestion and final directory generation
