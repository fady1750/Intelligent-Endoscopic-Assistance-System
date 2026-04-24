"""
Premium backend for the Intelligent Endoscopic Assistance System.

Run:
    pip install -r requirements.txt
    python backend.py

Then open:
    http://127.0.0.1:8000/
"""
from __future__ import annotations

import base64
import io
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pydantic import BaseModel, Field

try:  # OpenCV gives better contour and edge metrics, but the backend still works without it.
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional runtime fallback
    cv2 = None

APP_DIR = Path(__file__).resolve().parent
FRONTEND_FILE = APP_DIR / "endoscopic_premium_tabs.html"

app = FastAPI(
    title="Intelligent Endoscopic Assistance System Backend",
    version="3.0.0-premium-live-all-tabs",
    description="Local Python analysis API for simulated endoscopic frames.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    """Request body for local frame analysis."""

    image_base64: str = Field(..., min_length=32, description="PNG/JPEG base64, with or without data URL prefix")
    tissue_hint: Optional[str] = Field(default=None, description="Optional frontend tissue mode hint")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessRequest(AnalyzeRequest):
    """Request body for frame preprocessing."""

    noise_strength: int = Field(default=2, ge=0, le=8)
    contrast_strength: int = Field(default=35, ge=0, le=100)
    color_norm: int = Field(default=12, ge=0, le=100)


class ReportRequest(BaseModel):
    """Small endpoint for saving/exporting structured session reports."""

    operator: str = "—"
    procedure: str = "—"
    patient_id: str = "—"
    elapsed_time: str = "00:00:00"
    findings: str = "No findings recorded."
    metrics: Dict[str, Any] = Field(default_factory=dict)


def _clean_base64(data: str) -> str:
    if "," in data and data.strip().lower().startswith("data:"):
        return data.split(",", 1)[1]
    return data.strip()


def decode_image(image_base64: str) -> Image.Image:
    """Decode user-provided base64 into a safe RGB PIL image."""

    try:
        raw = base64.b64decode(_clean_base64(image_base64), validate=True)
        image = Image.open(io.BytesIO(raw))
        image.load()
        return image.convert("RGB")
    except Exception as exc:  # noqa: BLE001 - return user-safe API error
        raise HTTPException(status_code=400, detail=f"Invalid image_base64 payload: {exc}") from exc


def encode_png(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _gray_array(rgb: np.ndarray) -> np.ndarray:
    return (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]).astype(np.uint8)


def _edge_density(gray: np.ndarray) -> tuple[float, int, float]:
    """Return edge density, contour count, largest contour area ratio."""

    if cv2 is not None:
        edges = cv2.Canny(gray, threshold1=45, threshold2=120)
        density = float(np.mean(edges > 0))
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour_count = int(len(contours))
        largest = max((cv2.contourArea(c) for c in contours), default=0.0)
        area_ratio = float(largest / max(1, gray.shape[0] * gray.shape[1]))
        return density, contour_count, area_ratio

    pil_edges = Image.fromarray(gray).filter(ImageFilter.FIND_EDGES)
    edge_arr = np.asarray(pil_edges)
    density = float(np.mean(edge_arr > 24))
    return density, -1, 0.0


def _laplacian_variance(gray: np.ndarray) -> float:
    if cv2 is not None:
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())
    # Pure NumPy fallback: second derivative approximation.
    center = gray[1:-1, 1:-1].astype(float) * 4
    lap = center - gray[:-2, 1:-1] - gray[2:, 1:-1] - gray[1:-1, :-2] - gray[1:-1, 2:]
    return float(np.var(lap))


def extract_features(image: Image.Image, tissue_hint: Optional[str] = None) -> Dict[str, Any]:
    rgb = np.asarray(image, dtype=np.uint8)
    gray = _gray_array(rgb)

    brightness = float(gray.mean())
    contrast = float(gray.std())
    mean_rgb = [float(v) for v in rgb.reshape(-1, 3).mean(axis=0)]

    red_mask = (rgb[:, :, 0] > 95) & (rgb[:, :, 0] > rgb[:, :, 1] * 1.16) & (rgb[:, :, 0] > rgb[:, :, 2] * 1.12)
    red_ratio = float(np.mean(red_mask))

    edge_density, contour_count, largest_contour_area = _edge_density(gray)
    lap_var = _laplacian_variance(gray)

    hint = (tissue_hint or "").strip().lower()
    if hint in {"polyp", "lesion", "bleeding", "normal"}:
        classification = hint.title()
    elif red_ratio > 0.085:
        classification = "Bleeding"
    elif edge_density > 0.18 and lap_var > 500:
        classification = "Lesion"
    elif largest_contour_area > 0.055:
        classification = "Polyp"
    else:
        classification = "Normal"

    risk_score = 0
    if classification in {"Bleeding", "Lesion"}:
        risk_score += 2
    if classification == "Polyp":
        risk_score += 1
    if red_ratio > 0.06:
        risk_score += 2
    elif red_ratio > 0.025:
        risk_score += 1
    if edge_density > 0.16:
        risk_score += 1
    if brightness < 45 or brightness > 210:
        risk_score += 1

    risk_level = "high" if risk_score >= 4 else "medium" if risk_score >= 2 else "low"

    if risk_level == "high":
        recommendation = "Pause advancement, clean lens if needed, document the frame, and request senior/clinical review."
    elif risk_level == "medium":
        recommendation = "Capture extra views, adjust illumination/contrast, and inspect the region carefully."
    else:
        recommendation = "Continue routine navigation while maintaining stable visualization and patient monitoring."

    return {
        "classification": classification,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "metrics": {
            "brightness": round(brightness, 3),
            "contrast": round(contrast, 3),
            "mean_rgb": [round(v, 3) for v in mean_rgb],
        },
        "features": {
            "shape": {
                "edge_density": round(edge_density, 5),
                "contour_count": contour_count,
                "largest_contour_area_percent": round(largest_contour_area * 100, 4),
            },
            "color": {
                "red_ratio": round(red_ratio, 5),
                "mean_red": round(mean_rgb[0], 3),
                "mean_green": round(mean_rgb[1], 3),
                "mean_blue": round(mean_rgb[2], 3),
            },
            "texture": {
                "laplacian_variance": round(lap_var, 3),
                "texture_level": "high" if lap_var > 900 else "medium" if lap_var > 250 else "low",
            },
        },
    }


def preprocess_image(image: Image.Image, noise_strength: int, contrast_strength: int, color_norm: int) -> Image.Image:
    """Apply safe local preprocessing close to the frontend pipeline."""

    processed = image.copy()
    if noise_strength > 0:
        processed = processed.filter(ImageFilter.GaussianBlur(radius=noise_strength / 3.0))

    if color_norm > 0:
        cutoff = min(8, max(0, color_norm // 12))
        processed = ImageOps.autocontrast(processed, cutoff=cutoff)

    if contrast_strength > 0:
        factor = 1.0 + contrast_strength / 90.0
        processed = ImageEnhance.Contrast(processed).enhance(factor)
        processed = ImageEnhance.Sharpness(processed).enhance(1.0 + contrast_strength / 160.0)

    return processed


@app.get("/")
def index() -> FileResponse:
    if not FRONTEND_FILE.exists():
        raise HTTPException(status_code=404, detail="endoscopic_premium_tabs.html was not found next to backend.py")
    return FileResponse(FRONTEND_FILE)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "online",
        "version": app.version,
        "opencv": cv2 is not None,
        "timestamp": time.time(),
    }


@app.post("/api/analyze-frame")
def analyze_frame(payload: AnalyzeRequest) -> Dict[str, Any]:
    image = decode_image(payload.image_base64)
    result = extract_features(image, payload.tissue_hint)
    result.update(
        {
            "image": {"width": image.width, "height": image.height, "mode": image.mode},
            "metadata": payload.metadata,
            "analysis_engine": "opencv" if cv2 is not None else "pillow-numpy",
        }
    )
    return result


@app.post("/api/process-frame")
def process_frame(payload: ProcessRequest) -> Dict[str, Any]:
    image = decode_image(payload.image_base64)
    processed = preprocess_image(image, payload.noise_strength, payload.contrast_strength, payload.color_norm)
    features = extract_features(processed, payload.tissue_hint)
    return {
        "processed_image_base64": encode_png(processed),
        "mime_type": "image/png",
        "features": features["features"],
        "metrics": features["metrics"],
    }


@app.post("/api/report")
def create_report(payload: ReportRequest) -> Dict[str, Any]:
    return {
        "title": "Intelligent Endoscopic Assistance System Report",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "operator": payload.operator,
        "procedure": payload.procedure,
        "patient_id": payload.patient_id,
        "elapsed_time": payload.elapsed_time,
        "findings": payload.findings,
        "metrics": payload.metrics,
        "status": "ready_for_submission",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=False)