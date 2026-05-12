from __future__ import annotations

from uuid import uuid4


def generate_face_id(existing_ids: set[str]) -> str:
    while True:
        candidate = f"f_{uuid4().hex[:10]}"
        if candidate not in existing_ids:
            return candidate


def generate_candidate_id() -> str:
    return f"c_{uuid4().hex[:10]}"
