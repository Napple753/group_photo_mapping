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
   - The user chooses face detection from the post-image overlay.
   - First detection auto-accepts all detected faces.

2. Re-detection workflow
   - Existing `faces.json` or `faces.enriched.json` has been loaded from the post-image overlay.
   - Detection starts automatically after JSON import completes.
   - Existing faces remain authoritative.
   - Newly detected faces appear as candidate overlays.
   - Candidate items require explicit accept or ignore actions.

---

## Primary Screen Structure

The Tool A screen is composed of five major regions:

1. Global Header
2. System Banner Area
3. Main Workspace
4. Stage Toolbar
5. Right Sidebar Tabs

### Layout Overview

Desktop layout:

- Header at top
- Header uses its full descriptive layout before an image is loaded
- Header collapses to a minimal width footprint after an image is loaded so the stage remains dominant
- Banner area below header
- Two-column workspace below banners
- Left column: image stage and direct editing controls
- Right column: tabbed editing and export controls

Mobile layout:

- Header stacks vertically
- Main workspace collapses into a single column
- Stage appears before sidebar tabs

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
|- Banner Area
|  |- Error Banner
|- Workspace
|  |- Stage Panel
|  |  |- Image Stage
|  |  |  |- Empty State
|  |  |  |- Photo Element
|  |  |  |- Post-Image Action Overlay
|  |  |  |  |- Run Detection CTA
|  |  |  |  |- Load Faces JSON CTA
|  |  |  |- SVG Overlay Layer
|  |  |     |- Final Face Ellipses
|  |  |     |- Candidate Ellipses
|  |  |- Stage Toolbar
|  |     |- Run Detection Button
|  |- Sidebar
|     |- Tab List
|     |  |- Face Editor Tab
|     |  |- Faces Tab
|     |  |- Export Tab
|     |- Tab Panels
|        |- Face Editor Panel
|        |- Faces Panel
|        |- Export Panel
```

---

## Global Header

### Purpose

Provide page identity and top-level file import actions.

The header must prioritize the image workspace once editing begins.

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

#### Header Density Behavior

Before an image is loaded:

- show eyebrow, title, intro copy, and import controls in the full header layout

After an image is loaded:

- reduce the header to the minimum width needed for identity and the `Load Image` action
- keep the header on a single compact row on desktop when space allows
- avoid consuming horizontal space that would materially reduce the visible stage area
- intro copy may be hidden in the compact state

#### Load Image Button

- Type: file input trigger
- Accepts: JPEG, PNG, and WebP image files
- Purpose: load or replace the active group photo

Behavior:

- clears current error banner
- clears current faces and candidates
- clears current selection
- resets the imported-JSON state to false
- initializes or refreshes the editor session
- opens the post-image action overlay on the stage after the image is ready

---

## Banner Area

### Purpose

Display global messages that apply to the entire screen when needed.

### Error Banner

- Visibility: only shown when a blocking or actionable error exists
- Position: above the workspace
- Content source: latest UI or API error
- Tone: direct and specific

Examples:

- `Load an image before running face detection.`
- `Load an image before importing face JSON.`
- `Unable to reach the backend API. Confirm the FastAPI server is running and reload the page.`

---

## Main Workspace

### Purpose

Provide a split view between direct visual editing and structured control panels.

### Layout Rules

Desktop:

- left region takes primary width
- right region contains a tabbed control surface

Mobile:

- regions stack vertically
- stage remains above sidebar tabs

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

Layout requirements:

- the visible image area must remain the dominant element on the screen after an image is loaded
- the stage must size itself so the rendered image never exceeds the available viewport height
- the image and overlay must remain fully aligned while scaling

#### Empty State

- Shown only when no image is loaded
- Required message: `Load an image to start editing face regions.`

#### Photo Element

- Displays the currently loaded group photo
- Must maintain alignment with the SVG overlay
- Must preserve aspect ratio while scaling
- Must be constrained so its rendered height does not exceed the viewport height available to the application shell
- When the viewport is short, the image should scale down before introducing page overflow from the stage itself

#### Post-Image Action Overlay

- Shown after an image finishes loading and before the first post-load action is completed
- Positioned as an overlay on top of the image stage
- Purpose: branch the workflow into direct detection or JSON-assisted editing

It contains:

- `Detect Faces` button
- `Load Face JSON` button

Behavior:

- hidden when no image is loaded
- shown immediately after each new image load
- dismissed after either action successfully completes
- a successful detection action includes a zero-result detection response
- may be shown again if the image is replaced
- detection failure after JSON import should surface through the Error Banner without reopening the overlay

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
- managed from the unified face list

### Stage Toolbar

The toolbar is visually attached to the stage and controls stage-centric actions.

#### Run Detection Button

- Purpose: invoke face detection

Behavior depends on session state:

1. No JSON imported
   - detected faces are auto-accepted immediately
   - no candidate items are added

2. JSON imported
   - detected faces appear as candidate items in the unified face list
   - user must explicitly accept or ignore them

Busy state:

- button must show a busy label while detection is running
- button must be disabled while the request is in flight

---

## Sidebar

### Purpose

Provide structured editing, inspection, and export controls through a tabbed interface.

The sidebar contains one tab list and three tab panels:

1. Face Editor Tab / Panel
2. Faces Tab / Panel
3. Export Tab / Panel

Only one tab panel is visible at a time.

### Tab List

The tab list must include:

- `Face Editor`
- `Faces`
- `Export`

Behavior:

- one tab is always active
- switching tabs changes only the visible sidebar content and must not reset editor state
- the active tab must be visually distinct
- keyboard focus order must include the tab list before the active panel content

### Default Active Tab

- Before any image is loaded, `Face Editor` is the default active tab
- After image load, the previously active tab may remain active
- After selecting a face from the stage or face list, the UI may switch to `Face Editor` if needed for immediate editing

---

## Face Editor Panel

### Purpose

Serve as the face editing field for the current selection and host manual face creation and deletion.

### States

#### No Image State

- All controls are disabled
- Message: `Load an image to start editing faces.`

#### No Selection State

- `Add Face` button is shown and enabled
- `Delete Selected` button is shown but disabled
- Message: `Select a face or add a new one to edit its ellipse.`

#### Selected Face State

Displays:

- `Add Face` button
- `Delete Selected` button
- selected `faceId`
- `Center X` slider
- `Center Y` slider
- `Radius X` slider
- `Radius Y` slider

#### Selected Candidate State

- `Add Face` button remains available
- `Delete Selected` button remains disabled
- geometry sliders remain visible but disabled
- Message: `Accept the candidate from the list before editing its ellipse.`

### Action Controls

#### Add Face Button

- Purpose: create a new manual face region
- Behavior:
   - requires an image
   - creates a new face with a new `faceId`
   - inserts a default ellipse using `cx=0.5`, `cy=0.5`, `rx=0.03`, `ry=0.05`
   - selects the newly created face

#### Delete Selected Button

- Purpose: delete the currently selected final face
- Behavior:
   - no-op when no final face is selected
   - removes the selected face from the face list
   - must not affect candidate items

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

Show accepted faces and candidates in one unified, scrollable list.

The panel uses one shared data source for both item types.

Accepted faces and candidates must not be split into separate panels.

### Header

The panel header must show:

- panel title: `Faces`
- total item count
- optional breakdown text for accepted faces and candidates

### Item Types

The list renders two item presentations:

1. Accepted face item
2. Candidate item

Accepted faces should appear before candidates by default.

### Accepted Face Item Content

Each accepted face row must display:

- `faceId`
- secondary label

Secondary label priority:

1. `profile.fullName`
2. fallback text: `No profile data`

### Accepted Face Item Behavior

- clicking a row selects that face
- selected row must be visibly highlighted
- the list must remain scrollable for large groups

### Candidate Item Content

Each candidate item must show:

- `candidateId`
- confidence as an integer percentage if available
- `Accept` button
- `Ignore` button

### Candidate Item Behavior

- clicking a candidate item highlights the candidate on the stage
- candidate items must be visually distinct from accepted faces
- candidate items must not expose direct geometry editing controls

`candidateId` only needs to be unique within the current detection result set and does not need to persist across later detections.

### Candidate Actions

#### Accept

- creates a new final face with a new `faceId`
- copies ellipse geometry from the candidate
- removes the candidate item from the unified list
- selects the newly created final face

#### Ignore

- removes only the candidate item
- must not modify final faces

### Non-Goals

This list must not:

- auto-merge candidates into existing faces in re-detection mode
- mutate existing accepted faces

### Future Extension Slots

This panel may later include:

- face count summary
- search or filter for face list
- sort controls
- warning markers for incomplete data

---

## Export Panel

### Purpose

Support output generation for Tool A deliverables.

### Elements

#### MS Forms URL Prefix Input

- Type: single-line text input
- Purpose: provide the prefix used to generate form entry URLs

Validation rule:

- expected for `form_entry.html` export
- must end with `=`
- invalid or missing values should trigger a warning message but must not block export

Placeholder example:

`https://forms.office.com/...=`

#### Export faces.json Button

- Purpose: export accepted faces as `faces.json`
- Includes only accepted final faces

#### Export form_entry.html Button

- Purpose: export standalone HTML for form entry workflow
- Uses the current MS Forms prefix value if provided
- Warns when the prefix is missing or malformed, but does not block export

---

## UI State Model

The UI behavior depends on the following top-level states.

### Image State

- no image loaded
- image loaded

### Post-Image Action State

- overlay hidden
- overlay awaiting user choice

### Import State

- no face JSON imported
- face JSON imported

### Selection State

- no selected face
- selected final face
- selected candidate

### Detection State

- idle
- running
- candidates available

### Message State

- no error
- active error banner

### Header State

- full header
- compact header

### Sidebar Tab State

- face editor tab active
- faces tab active
- export tab active

---

## Interaction Rules

### Image Loading

When a new image is loaded:

- clear current faces
- clear current candidates
- clear current face selection
- reset imported-JSON state to false
- initialize session dimensions from the image
- show the post-image action overlay
- switch the header into its compact state

### Post-Image Action Choice

After the image is loaded, the stage overlay presents two actions:

1. `Detect Faces`
2. `Load Face JSON`

Choosing either action dismisses the overlay after successful completion.

For JSON import with automatic re-detection, a zero-result detection response still counts as successful completion.

### JSON Import

When face JSON is imported:

- require an already loaded image
- replace editor face data with imported data
- preserve profile data if provided
- expose `profile.fullName` in accepted-face list rows when available
- do not expose profile fields for editing in Tool A
- mark the session as imported-JSON mode
- immediately run detection after the import completes
- show newly detected regions as candidate items in the unified face list
- keep the post-image action overlay closed even if the automatic detection request fails

### Initial Detection

Condition:

- image loaded
- no face JSON imported
- detection triggered from the post-image overlay or the stage toolbar

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
- user must accept or ignore each candidate item from the unified face list

### Manual Face Creation

Result:

- a new accepted final face is created
- creation is triggered from the Face Editor Panel
- the default geometry is `cx=0.5`, `cy=0.5`, `rx=0.03`, `ry=0.05`
- the face is immediately selectable and editable
- the `Face Editor` tab may become active if another tab was open

### Face Editing

Allowed operations:

- drag on stage
- slider-based geometry update

Constraints:

- accepted faces only
- keep ellipse within bounds
- do not regenerate IDs

### Tab Switching

Result:

- the user can move between `Face Editor`, `Faces`, and `Export` without leaving the current image session
- tab changes must preserve the current face list, candidates, selection state, and unsaved form prefix input
- tab changes must not re-run detection or import actions

### Face Deletion

Result:

- deletion is triggered from the Face Editor Panel
- only the selected accepted face can be deleted
- candidate items are unaffected

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

Warnings may be shown inline when they do not block the user action, such as a malformed MS Forms prefix before export.

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
