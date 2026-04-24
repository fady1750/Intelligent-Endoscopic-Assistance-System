import base64
import io

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from backend import app, decode_image, extract_features


def make_test_image(as_data_url: bool = False) -> str:
    image = Image.new("RGB", (128, 128), (70, 24, 28))
    draw = ImageDraw.Draw(image)
    draw.ellipse((38, 34, 92, 88), fill=(185, 42, 45), outline=(245, 190, 170), width=3)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}" if as_data_url else encoded


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "online"
    assert body["version"]


def test_analyze_frame_endpoint_returns_required_features():
    client = TestClient(app)
    response = client.post(
        "/api/analyze-frame",
        json={"image_base64": make_test_image(), "tissue_hint": "Lesion", "metadata": {"depth_cm": 18}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["classification"] == "Lesion"
    assert body["risk_level"] in {"low", "medium", "high"}
    assert "shape" in body["features"]
    assert "color" in body["features"]
    assert "texture" in body["features"]
    assert body["image"]["width"] == 128


def test_process_frame_endpoint_accepts_data_url_and_returns_png():
    client = TestClient(app)
    response = client.post(
        "/api/process-frame",
        json={
            "image_base64": make_test_image(as_data_url=True),
            "noise_strength": 2,
            "contrast_strength": 35,
            "color_norm": 12,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mime_type"] == "image/png"
    assert len(body["processed_image_base64"]) > 100
    decoded = decode_image(body["processed_image_base64"])
    assert decoded.size == (128, 128)


def test_report_endpoint_returns_submission_ready_status():
    client = TestClient(app)
    response = client.post(
        "/api/report",
        json={
            "operator": "Dr. Nader Ahmed",
            "procedure": "Diagnostic Colonoscopy",
            "patient_id": "PID-TEST",
            "elapsed_time": "00:01:00",
            "findings": "No critical finding.",
            "metrics": {"depth_cm": 18},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready_for_submission"
    assert body["metrics"]["depth_cm"] == 18


def test_invalid_image_payload_is_rejected():
    client = TestClient(app)
    response = client.post("/api/analyze-frame", json={"image_base64": "not-valid-base64"})
    assert response.status_code == 422 or response.status_code == 400


def test_extract_features_without_hint_classifies_safely():
    image = decode_image(make_test_image())
    features = extract_features(image)
    assert features["classification"] in {"Normal", "Polyp", "Lesion", "Bleeding"}
    assert features["features"]["color"]["red_ratio"] >= 0
