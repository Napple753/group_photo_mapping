from __future__ import annotations

import json
from app.models.schemas import FaceRegion


def build_faces_json(image_width: int, image_height: int, faces: list[FaceRegion]) -> str:
    payload = {
        "schemaVersion": 1,
        "imageWidth": image_width,
        "imageHeight": image_height,
        "faces": [face.model_dump(exclude_none=True) for face in faces],
    }
    return json.dumps(payload, indent=2)


def build_form_entry_html(
    image_data_url: str,
    faces: list[FaceRegion],
    ms_forms_url_prefix: str,
    include_privacy_notice: bool,
) -> str:
    face_payload = json.dumps([face.model_dump(exclude_none=True) for face in faces])
    privacy_markup = ""
    if include_privacy_notice:
        privacy_markup = (
            '<aside class="privacy-notice">Internal company use only. '
            "Contains personal information. Do not distribute externally.</aside>"
        )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Group Photo Form Entry</title>
    <style>
      body {{ margin: 0; font-family: Helvetica, Arial, sans-serif; background: #f4efe5; color: #1d1a16; }}
      .page {{ display: grid; gap: 16px; padding: 16px; }}
      .frame {{ position: relative; width: min(100%, 1200px); margin: 0 auto; background: #fffdf8; border-radius: 16px; overflow: hidden; box-shadow: 0 24px 80px rgba(0,0,0,0.12); }}
      img {{ display: block; width: 100%; height: auto; }}
      svg {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
      ellipse {{ fill: rgba(216, 98, 64, 0.14); stroke: #d86240; stroke-width: 2; cursor: pointer; transition: fill 120ms ease, stroke 120ms ease; }}
      ellipse:hover {{ fill: rgba(216, 98, 64, 0.24); stroke: #8b2f18; }}
      .privacy-notice {{ width: min(100%, 1200px); margin: 0 auto; padding: 12px 16px; border-radius: 12px; background: #fff2cc; color: #4b3a04; }}
    </style>
  </head>
  <body>
    <main class=\"page\">
      {privacy_markup}
      <section class=\"frame\">
        <img src=\"{image_data_url}\" alt=\"Group photo\" />
        <svg viewBox=\"0 0 1000 1000\" preserveAspectRatio=\"none\"></svg>
      </section>
    </main>
    <script>
      const faces = {face_payload};
      const prefix = {json.dumps(ms_forms_url_prefix)};
      const svg = document.querySelector('svg');
      faces.forEach((face) => {{
        const ellipse = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        ellipse.setAttribute('cx', String(face.cx * 1000));
        ellipse.setAttribute('cy', String(face.cy * 1000));
        ellipse.setAttribute('rx', String(face.rx * 1000));
        ellipse.setAttribute('ry', String(face.ry * 1000));
        ellipse.setAttribute('tabindex', '0');
        const openForm = () => {{
          if (!prefix) {{
            return;
          }}
          const confirmed = window.confirm(`Open form for ${{face.faceId}}?`);
          if (confirmed) {{
            window.open(`${{prefix}}${{face.faceId}}`, '_blank', 'noopener,noreferrer');
          }}
        }};
        ellipse.addEventListener('click', openForm);
        ellipse.addEventListener('keydown', (event) => {{
          if (event.key === 'Enter' || event.key === ' ') {{
            event.preventDefault();
            openForm();
          }}
        }});
        svg.appendChild(ellipse);
      }});
    </script>
  </body>
</html>
"""
