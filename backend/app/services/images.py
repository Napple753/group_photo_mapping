from __future__ import annotations

import base64
from io import BytesIO

from PIL import Image


class ImageDecodeError(ValueError):
    pass


def decode_data_url(data_url: str) -> tuple[str, bytes]:
    if not data_url.startswith("data:image/") or "," not in data_url:
        raise ImageDecodeError("Expected an image data URL")

    header, encoded = data_url.split(",", 1)
    mime_type = header.split(";", 1)[0].replace("data:", "", 1)

    try:
        image_bytes = base64.b64decode(encoded)
    except ValueError as exc:
        raise ImageDecodeError("Invalid base64 image data") from exc

    return mime_type, image_bytes


def get_image_size(image_bytes: bytes) -> tuple[int, int]:
    with Image.open(BytesIO(image_bytes)) as image:
        return image.size
