# Intelligent Endoscopic Assistance System — Premium Final Version

This package contains the final premium simulation for **Medical Equipment II / SBE3220 Task 02**.

## Files

- `endoscopic_premium_tabs.html` — premium tabbed frontend with **always-on live imaging in every tab**.
- `backend.py` — Python FastAPI backend for local frame analysis and processing.
- `requirements.txt` — Python dependencies.
- `test_backend.py` — automated backend tests.

## Run

```bash
pip install -r requirements.txt
python backend.py
```

Open:

```text
http://127.0.0.1:8000/
```

## Main features

- Live endoscopic imaging simulator.
- **Always-On Live Imaging Monitor** visible across all tabs.
- Clean tab workspace: Live Imaging, Dashboard, Navigation, Processing, AI Assist, Gallery & Log.
- Illumination control: power, intensity, spectral modes.
- Imaging control: tissue type, zoom, focus, frame capture, measurement overlay.
- Navigation control: keyboard, D-pad, rotation, depth tracking, body map, 3D viewer fallback.
- Processing bonus: noise reduction, contrast enhancement, color normalization, Sobel edges, red-zone segmentation, texture map.
- Python backend analysis: brightness, contrast, shape, color, texture, risk level, recommendation.
- Exportable procedure log and printable report.
- Frontend self-test button.

## Test

```bash
pytest -q test_backend.py
python -m py_compile backend.py test_backend.py
node --check frontend_script_check.js
```

The frontend script check file can be regenerated from the HTML if needed by extracting the inline `<script>` block.
