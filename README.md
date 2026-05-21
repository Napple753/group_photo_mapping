# Group Photo Mapping

This repository currently contains the product specifications for the Group Photo Mapping tool.

The project defines a local workflow for preparing an interactive people directory from a large group photo.

The system scope is split into two tools:

- Tool A: face region editing and `form_entry.html` generation
- Tool B: CSV merge and final `index.html` / `faces.enriched.json` generation

## Repository Contents

- `group_photo_face_mapping_spec.md`: primary product specification for Tool A and Tool B
- `tool_a_ui_spec.md`: Tool A UI structure, state model, and interaction rules
- `README.md`: repository overview and navigation guide

## Current Status

The current tracked content in this branch is specification-focused.

Recent specification decisions already reflected in the documents include:

- Tool A supports JPEG, PNG, and WebP input images
- JSON import triggers automatic re-detection
- zero-result re-detection is still treated as success
- re-detection failures surface as errors without reopening the post-image overlay
- candidate rows must highlight the candidate on the stage
- manual face creation uses fixed default ellipse geometry
- malformed MS Forms prefixes warn but do not block `form_entry.html` export
- Tool B uses user-selected CSV column mapping from the CSV header row
- unanswered CSV rows are excluded from final output and reported before generation

## How To Read The Specs

Read the documents in this order:

1. `group_photo_face_mapping_spec.md`
2. `tool_a_ui_spec.md`

The main specification defines product behavior and file contracts.

The Tool A UI specification defines screen structure, control behavior, and interaction states.

## Scope Notes

- UI language is `en-US`
- Outputs are intended to be portable static HTML files
- Face detection provides suggestions only; human-edited regions are authoritative
- Tool A preserves `profile` data from `faces.enriched.json` but does not edit those fields

## Implementation Note

If implementation code is added later, keep product behavior in the specification files and use this README as a lightweight overview rather than a second source of truth for feature rules.
