# Tool A UI Specification

## Document Purpose

This document defines the UI structure for Tool A: Face Region Editor + MS Forms HTML Generator.

This file is the baseline specification for future UI changes. Update this document before or together with any meaningful Tool A UI change.

The implementation must follow `en-US` UI text.

---

## Scope

This specification covers:

- screen layout
- UI components
- component responsibilities
- user interaction flows
- state-dependent UI behavior
- validation and message placement

This specification does not define:

- backend API schema in detail
- Tool B UI
- visual design tokens beyond structural needs

---

## Product Goal

Tool A allows a user to:

1. load a group photo
2. detect face regions
3. manually edit ellipse regions
4. import existing face region JSON
5. export `faces.json`
6. export standalone `form_entry.html`

The UI must support two distinct workflows:

1. Initial mapping workflow
   - No face JSON has been loaded.
   - First detection auto-accepts all detected faces.

2. Re-detection workflow
   - Existing `faces.json` or `faces.enriched.json` has been loaded.
   - Existing faces remain authoritative.
   - Newly detected faces appear as candidate overlays.
   - Candidates require explicit accept or ignore actions.

---

## Primary Screen Structure

The Tool A screen is composed of five major regions:

1. Global Header
2. System Banner Area
3. Main Workspace
4. Stage Toolbar
5. Right Sidebar Panels

### Layout Overview

Desktop layout:

- Header at top
- Banner area below header
- Two-column workspace below banners
- Left column: image stage and direct editing controls
- Right column: structured control panels

Mobile layout:

- Header stacks vertically
- Main workspace collapses into a single column
- Stage appears before sidebar panels

---

## Component Tree

```text
ToolAPage
|- Header
|  |- Title Block
|  |  |- Eyebrow Label
|  |  |- Page Title
|  |  |- Introductory Copy
|  |- Import Actions
|     |- Load Image Button
|     |- Load Faces JSON Button
|- Banner Area
|  |- Error Banner
|  |- Privacy Banner
|- Workspace
|  |- Stage Panel
|  |  |- Image Stage
|  |  |  |- Empty State
|  |  |  |- Photo Element
|  |  |  |- SVG Overlay Layer
|  |  |     |- Final Face Ellipses
|  |  |     |- Candidate Ellipses
|  |  |- Stage Toolbar
|  |     |- Add Face Button
|  |     |- Run Detection Button
|  |     |- Delete Selected Button
|  |- Sidebar
|     |- Selection Panel
|     |- Faces Panel
|     |- Candidates Panel
|     |- Export Panel
```

---

## Global Header

### Purpose

Provide page identity and top-level file import actions.

### Elements

#### Eyebrow Label

- Content: `Tool A`
- Purpose: identify the current tool in the broader system

#### Page Title

- Content: `Face Region Editor`
- Purpose: identify the screen

#### Introductory Copy

- Purpose: summarize the current workflow supported by the screen
- Must remain short and action-oriented

#### Load Image Button

- Type: file input trigger
- Accepts: image files
- Purpose: load or replace the active group photo

Behavior:

- clears current error banner
- clears candidates
- clears current selection
- resets the imported-JSON state to false
- initializes or refreshes the editor session

#### Load Faces JSON Button

- Type: file input trigger
- Accepts: `.json`
- Purpose: load existing face region data

Behavior:

- requires an image to already be loaded
- imports `faces.json` or `faces.enriched.json`
- sets imported-JSON state to true
- clears candidates
- selects the first available face after successful import

---

## Banner Area

### Purpose

Display global messages that apply to the entire screen.

### Error Banner

- Visibility: only shown when a blocking or actionable error exists
- Position: above the workspace
- Content source: latest UI or API error
- Tone: direct and specific

Examples:

- `Load an image before running face detection.`
- `Load an image before importing face JSON.`
- `Unable to reach the backend API. Confirm the FastAPI server is running and reload the page.`

### Privacy Banner

- Visibility: always visible
- Position: directly below the error banner or in its place
- Required content: internal-use privacy warning

Required message:

`Internal company use only. Contains personal information. Do not distribute externally.`

---

## Main Workspace

### Purpose

Provide a split view between direct visual editing and structured control panels.

### Layout Rules

Desktop:

- left region takes primary width
- right region contains stacked control panels

Mobile:

- regions stack vertically
- stage remains above control panels

---

## Stage Panel

### Purpose

Provide the direct manipulation area for face ellipses.

### Subcomponents

#### Image Stage

The image stage is the main editing canvas.

It contains:

- image viewport
- SVG overlay
- empty state when no image is loaded

#### Empty State

- Shown only when no image is loaded
- Required message: `Load an image to start editing face regions.`

#### Photo Element

- Displays the currently loaded group photo
- Must maintain alignment with the SVG overlay

#### SVG Overlay Layer

- Coordinate system: normalized `0..1`
- Purpose: render final face regions and candidate regions over the photo

##### Final Face Ellipses

- Represent accepted face regions
- Clickable
- Draggable
- Selectable

States:

- default
- hover
- selected

Required behavior:

- clicking selects the face
- pointer drag moves the face ellipse
- selected face must be visually distinct

##### Candidate Ellipses

- Represent detected-but-not-finalized regions
- Visible only during re-detection workflow
- Not directly draggable in the current baseline UI

States:

- default candidate

Required behavior:

- visually distinct from final face ellipses
- managed from the Candidates Panel

### Stage Toolbar

The toolbar is visually attached to the stage and controls stage-centric actions.

#### Add Face Button

- Purpose: create a new manual face region
- Behavior:
  - requires an image
  - creates a new face with a new `faceId`
  - inserts a default ellipse at the center area
  - selects the newly created face

#### Run Detection Button

- Purpose: invoke face detection

Behavior depends on session state:

1. No JSON imported
   - detected faces are auto-accepted immediately
   - candidate list remains empty

2. JSON imported
   - detected faces appear as candidates
   - user must explicitly accept or ignore them

Busy state:

- button must show a busy label while detection is running
- button must be disabled while the request is in flight

#### Delete Selected Button

- Purpose: delete the currently selected final face
- Behavior:
  - no-op when no face is selected
  - removes the selected face from the face list
  - must not affect candidates

---

## Sidebar

### Purpose

Provide structured editing, inspection, and export controls.

The sidebar contains four panels in this order:

1. Selection Panel
2. Faces Panel
3. Candidates Panel
4. Export Panel

---

## Selection Panel

### Purpose

Edit the geometry of the currently selected final face.

### States

#### No Selection State

- Message: `Select a face to edit its ellipse.`

#### Selected Face State

Displays:

- selected `faceId`
- `Center X` slider
- `Center Y` slider
- `Radius X` slider
- `Radius Y` slider

### Control Behavior

#### Center X Slider

- Range: `0` to `1`
- Step: `0.001`
- Updates normalized `cx`

#### Center Y Slider

- Range: `0` to `1`
- Step: `0.001`
- Updates normalized `cy`

#### Radius X Slider

- Range baseline: `0.005` to `0.25`
- Step: `0.001`
- Updates normalized `rx`

#### Radius Y Slider

- Range baseline: `0.01` to `0.35`
- Step: `0.001`
- Updates normalized `ry`

### Constraint Rules

- updated faces must remain within the normalized stage bounds
- `cx` must be clamped by `rx`
- `cy` must be clamped by `ry`
- editing geometry must not change `faceId`

---

## Faces Panel

### Purpose

Show all accepted face regions in a compact list.

### Row Content

Each face row must display:

- `faceId`
- secondary label

Secondary label priority:

1. `profile.fullName`
2. fallback text: `No profile data`

### Row Behavior

- clicking a row selects that face
- selected row must be visibly highlighted
- the list must remain scrollable for large groups

### Future Extension Slots

This panel may later include:

- face count summary
- search or filter for face list
- sort controls
- warning markers for incomplete data

---

## Candidates Panel

### Purpose

Review re-detected faces before accepting them into the final list.

### Visibility Rules

- always present structurally
- contents may be empty
- normally populated only when JSON has been imported and detection has been run

### Header

The panel header must show:

- panel title: `Candidates`
- current candidate count

### Candidate Card Content

Each candidate card must show:

- `candidateId`
- confidence text if available
- `Accept` button
- `Ignore` button

### Candidate Actions

#### Accept

- creates a new final face with a new `faceId`
- copies ellipse geometry from the candidate
- removes the candidate from the candidate list
- selects the newly created final face

#### Ignore

- removes only the candidate
- must not modify final faces

### Non-Goals

This panel must not:

- auto-merge candidates into existing faces in re-detection mode
- mutate existing accepted faces

---

## Export Panel

### Purpose

Support output generation for Tool A deliverables.

### Elements

#### MS Forms URL Prefix Input

- Type: single-line text input
- Purpose: provide the prefix used to generate form entry URLs

Validation rule:

- required for `form_entry.html` export
- must end with `=`

Placeholder example:

`https://forms.office.com/...=`

#### Export faces.json Button

- Purpose: export accepted faces as `faces.json`
- Includes only accepted final faces

#### Export form_entry.html Button

- Purpose: export standalone HTML for form entry workflow
- Requires a valid MS Forms prefix

---

## UI State Model

The UI behavior depends on the following top-level states.

### Image State

- no image loaded
- image loaded

### Import State

- no face JSON imported
- face JSON imported

### Selection State

- no selected face
- selected final face

### Detection State

- idle
- running
- candidates available

### Message State

- no error
- active error banner

---

## Interaction Rules

### Image Loading

When a new image is loaded:

- clear current candidates
- clear current face selection
- reset imported-JSON state to false
- initialize session dimensions from the image

### JSON Import

When face JSON is imported:

- require an already loaded image
- replace editor face data with imported data
- preserve profile data if provided
- mark the session as imported-JSON mode

### Initial Detection

Condition:

- image loaded
- no face JSON imported

Result:

- all detected faces are immediately turned into accepted final faces
- no candidate review step is shown for that detection pass

### Re-Detection

Condition:

- image loaded
- face JSON imported

Result:

- existing faces stay unchanged
- new detections appear as candidates
- user must accept or ignore each candidate

### Manual Face Creation

Result:

- a new accepted final face is created
- the face is immediately selectable and editable

### Face Editing

Allowed operations:

- drag on stage
- slider-based geometry update

Constraints:

- accepted faces only
- keep ellipse within bounds
- do not regenerate IDs

---

## Message and Validation Placement

### Global Errors

Use the Error Banner for:

- missing image prerequisites
- import failures
- export failures
- backend connectivity failures

### Inline Validation

The baseline UI currently favors banner-level error feedback.

Future inline validation may be added for:

- invalid MS Forms prefix
- export prerequisites
- malformed imported JSON

---

## Accessibility Baseline

Minimum requirements:

- all interactive controls must be keyboard focusable
- buttons must use clear text labels
- selected state must be visually distinguishable
- color alone should not be the only indicator of state where practical
- file input triggers must remain operable through their labels

Future improvements recommended:

- keyboard shortcuts for face operations
- explicit focus rings for stage and list items
- ARIA descriptions for candidate actions and face rows

---

## Change Management Rules

When changing Tool A UI, update this document if the change affects any of the following:

- layout regions
- component responsibilities
- control names
- visibility rules
- state behavior
- interaction rules
- validation placement

Preferred update order:

1. revise this UI specification
2. implement the UI change
3. verify that the implementation matches the updated document

---

## Current Baseline Mapping to Implementation

Current reference implementation:

- `frontend/src/App.vue`

Current supporting product specification:

- `group_photo_face_mapping_spec.md`

This document is the UI-specific layer between those two.
