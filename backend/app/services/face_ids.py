from __future__ import annotations

import secrets


def generate_face_id() -> str:
    return f"f_{secrets.token_hex(5)}"
