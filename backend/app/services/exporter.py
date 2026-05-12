from __future__ import annotations

import json

from app.models import FaceDocument


def build_form_entry_html(document: FaceDocument, image_data_url: str, ms_forms_url_prefix: str) -> str:
    payload = {
        "imageDataUrl": image_data_url,
        "faces": [face.model_dump(mode="json") for face in document.faces],
        "msFormsUrlPrefix": ms_forms_url_prefix,
    }
    state_json = json.dumps(payload)

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Group Photo Form Entry</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #eef3f2;
      --panel: rgba(255, 255, 255, 0.84);
      --ink: #13211d;
      --muted: #5f6f6a;
      --accent: #006b5f;
      --accent-soft: rgba(0, 107, 95, 0.14);
      --stroke: rgba(19, 33, 29, 0.16);
      --highlight: #d95f02;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: \"Avenir Next\", \"Segoe UI\", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(0, 107, 95, 0.12), transparent 36%),
        linear-gradient(180deg, #f5f9f8 0%, var(--bg) 100%);
      min-height: 100vh;
    }}
    .shell {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 24px;
    }}
    .notice {{
      margin-bottom: 16px;
      padding: 14px 18px;
      border-radius: 16px;
      background: #fff0d9;
      border: 1px solid rgba(217, 95, 2, 0.22);
      color: #6f3904;
      font-weight: 600;
    }}
    .stage {{
      position: relative;
      background: var(--panel);
      border: 1px solid var(--stroke);
      border-radius: 24px;
      overflow: hidden;
      box-shadow: 0 24px 60px rgba(19, 33, 29, 0.12);
    }}
    .stage img {{ display: block; width: 100%; height: auto; }}
    .overlay {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
    .face {{
      fill: rgba(0, 107, 95, 0.16);
      stroke: var(--accent);
      stroke-width: 0.004;
      cursor: pointer;
      transition: fill 120ms ease, stroke 120ms ease, opacity 120ms ease;
    }}
    .face:hover, .face.active {{
      fill: rgba(217, 95, 2, 0.24);
      stroke: var(--highlight);
    }}
    .caption {{ margin-top: 14px; color: var(--muted); }}
  </style>
</head>
<body>
  <div class=\"shell\">
    <div class=\"notice\">Internal company use only. Contains personal information. Do not distribute externally.</div>
    <div class=\"stage\">
      <img id=\"photo\" alt=\"Group photo\" />
      <svg class=\"overlay\" id=\"overlay\" viewBox=\"0 0 1 1\" preserveAspectRatio=\"none\"></svg>
    </div>
    <div class=\"caption\">Click a face to open the associated Microsoft Forms entry.</div>
  </div>
  <script>
    const state = {state_json};
    const image = document.getElementById('photo');
    const overlay = document.getElementById('overlay');
    image.src = state.imageDataUrl;

    let activeFaceId = null;
    const render = () => {{
      overlay.innerHTML = '';
      for (const face of state.faces) {{
        const ellipse = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        ellipse.setAttribute('cx', String(face.cx));
        ellipse.setAttribute('cy', String(face.cy));
        ellipse.setAttribute('rx', String(face.rx));
        ellipse.setAttribute('ry', String(face.ry));
        ellipse.setAttribute('class', face.faceId === activeFaceId ? 'face active' : 'face');
        ellipse.addEventListener('mouseenter', () => {{
          activeFaceId = face.faceId;
          render();
        }});
        ellipse.addEventListener('mouseleave', () => {{
          activeFaceId = null;
          render();
        }});
        ellipse.addEventListener('click', () => {{
          const url = state.msFormsUrlPrefix + face.faceId;
          const confirmed = window.confirm(`Open Form for ${{face.faceId}}?`);
          if (confirmed) {{
            window.open(url, '_blank', 'noopener,noreferrer');
          }}
        }});
        overlay.appendChild(ellipse);
      }}
    }};

    render();
  </script>
</body>
</html>
"""
