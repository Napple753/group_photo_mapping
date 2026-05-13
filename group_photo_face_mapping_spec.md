# Group Photo Face Mapping Tool - Specification

## Overview

This project is an internal IT department tool for creating an interactive people directory from a large group photo (~100 people).

The system consists of two tools:

- Tool A: Face Region Editor + MS Forms HTML Generator
- Tool B: Final Interactive Directory Generator

The tool runs locally:

- Local web server
- Browser-based UI
- No cloud dependency except Microsoft Forms
- UI language: `en-US`

The final deliverables are:

- `form_entry.html`
- `index.html`
- `faces.json`
- `faces.enriched.json`

Both HTML outputs must be standalone single-file HTML documents.

---

# General Requirements

## Technology Stack (Recommended)

- Python 3.11+
- FastAPI
- OpenCV
- MediaPipe Face Detection
- Vanilla JavaScript or Vue.js
- SVG overlay for face regions

## Design Principles

- Face detection only
- No identity recognition
- Human-edited regions are authoritative
- Everything works locally
- Outputs must be portable static files

---

# Tool A - Face Region Editor

## Purpose

Create and edit face regions on a group photo and generate an MS Forms entry page.

---

# Tool A Inputs

## Required

- Group photo image

## Optional

- `faces.json`
- `faces.enriched.json`

## Required when exporting `form_entry.html`

- MS Forms URL prefix

Example:

```text
https://forms.office.com/...&rxxxxxxxx=
```

The URL MUST end with `=`.

The generated URL will be:

```text
msFormsUrlPrefix + faceId
```

---

# Tool A Features

## Face Detection

Use MediaPipe Face Detection to generate initial face candidates.

The detection is only used for initial suggestions.

Manual editing is expected.

When no `faces.json` or `faces.enriched.json` has been loaded, the first detection pass should auto-accept all detected faces into the editable face list.

When existing JSON has been loaded, detection must follow the re-detection workflow below and show new regions as candidates.

---

## Face Region Shape

Use ellipse regions.

Each region stores:

- center x/y
- radius x/y

Coordinates are stored as normalized relative values (0.0 - 1.0).

---

## Editing Features

Users can:

- Move ellipse
- Resize ellipse
- Add ellipse manually
- Delete ellipse
- Select ellipse

Keyboard shortcuts are recommended.

---

## Face IDs

Each face has a stable unique ID.

Format example:

```text
f_8a3c91d2a4
```

Requirements:

- Generated only when a new face is created
- Never regenerated during edits
- Never reused after deletion
- Existing IDs must remain unchanged

Use UUID/random-based generation.

Do NOT derive IDs from coordinates.

---

## Re-Detection Workflow

When existing JSON is loaded and face detection is run again:

- Existing regions remain unchanged
- Newly detected faces appear as candidate overlays
- Candidate regions are NOT auto-merged
- Candidate regions are NOT auto-added
- User manually accepts or ignores candidates

This supports workflows like:

- Editing the original photo
- Adding absent members later
- Running detection again safely

---

# Tool A Outputs

## faces.json

Example:

```json
{
  "schemaVersion": 1,
  "imageWidth": 6000,
  "imageHeight": 4000,
  "faces": [
    {
      "faceId": "f_8a3c91d2a4",
      "cx": 0.345,
      "cy": 0.412,
      "rx": 0.018,
      "ry": 0.032
    }
  ]
}
```

---

## form_entry.html

Requirements:

- Single standalone HTML file
- Image embedded as Base64
- Face overlays rendered with SVG
- Clicking a face opens:

```text
msFormsUrlPrefix + faceId
```

Recommended:

- Confirmation dialog before navigation
- Hover highlight
- Click feedback

---

# Tool B - Final Directory Generator

## Purpose

Combine:

- Face region data
- MS Forms responses
- Group photo

to generate the final interactive people directory.

---

# Tool B Inputs

## Required

- Group photo image
- `faces.json` or `faces.enriched.json`
- MS Forms CSV export
- CSV column mapping

---

# CSV Column Mapping

Column names must NOT be hardcoded.

Example mapping:

```json
{
  "faceId": "Face ID",
  "fullName": "Full Name",
  "nickname": "Nickname",
  "department": "Department",
  "email": "Email"
}
```

Required mapping keys:

- `faceId`
- `fullName`

Other fields are optional.

MS Forms itself handles required-field validation.

---

# CSV Handling Requirements

Support:

- UTF-8
- UTF-8 BOM
- CP932 / Shift_JIS if possible
- Excel-generated CSV files
- Quoted fields
- Embedded commas
- Embedded newlines

Trim whitespace from:

- `faceId`
- text fields

---

# Tool B Validation Rules

## Errors

Fail generation when:

- Duplicate `faceId` exists in CSV
- `faceId` is empty
- CSV `faceId` does not exist in JSON
- Required mapped columns are missing
- CSV parsing fails

## Warnings

Warnings only:

- Face exists in JSON but has no response
- Extra CSV columns exist

Unanswered faces are excluded from the final output.

---

# Tool B Outputs

## index.html

Requirements:

- Single standalone HTML file
- No external dependencies
- Image embedded as Base64
- Embedded face/profile data
- Search UI
- Interactive face selection

---

## faces.enriched.json

Purpose:

Reusable enriched data for future editing and re-detection.

Example:

```json
{
  "schemaVersion": 1,
  "imageWidth": 6000,
  "imageHeight": 4000,
  "faces": [
    {
      "faceId": "f_8a3c91d2a4",
      "cx": 0.345,
      "cy": 0.412,
      "rx": 0.018,
      "ry": 0.032,
      "profile": {
        "fullName": "Taro Yamada",
        "nickname": "Taro",
        "department": "Sales",
        "email": "taro@example.com"
      }
    }
  ]
}
```

Tool A must preserve `profile` data when reloading this file.

---

# index.html Features

## Face Interaction

- Click face → show profile
- Hover highlight
- Selected face highlight

---

## Search

Search targets:

- Full name
- Nickname
- Department
- Email

Requirements:

- Partial match
- Case-insensitive
- Multiple matches supported

Recommended:

- Search results list
- Clicking result focuses face
- Auto-scroll to selected face

---

# Privacy Notice

The final HTML contains embedded personal information.

Display a warning such as:

```text
Internal company use only.
Contains personal information.
Do not distribute externally.
```

---

# UI Language

All UI labels, dialogs, buttons, warnings, and messages must use:

```text
en-US
```

Examples:

- Export
- Generate
- Delete
- Add Face
- Duplicate Face ID
- Missing CSV Column
- Open Form
- Search

---

# Recommended UI Layout

## Tool A

Left:

- Group photo canvas

Right:

- Face list
- Selected face info
- Controls

---

## Tool B

Top:

- Search bar

Center:

- Group photo

Right:

- Profile panel
- Search results

---

# Recommended Architecture

## Backend

- FastAPI

## Frontend

- Vanilla JS or Vue.js

## Graphics

- SVG overlays

## Detection

- MediaPipe Face Detection

## HTML Export

- Jinja2 templates
- Inline CSS/JS
- Base64 image embedding

---

# Important Non-Goals

The project must NOT:

- Perform facial identity recognition
- Use cloud face APIs
- Require internet access
- Depend on external CDN assets in final HTML
