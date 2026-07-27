from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import joblib
from flask import Flask, jsonify, render_template, request

# Cho phep import module trong src/
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from features import extract_features, extract_meat_mask  # noqa: E402

# ---------------------------------------------------------------------------
# Cau hinh
# ---------------------------------------------------------------------------
DEFAULT_MODEL = os.environ.get(
    "MEAT_MODEL",
    str(BASE_DIR / "outputs" / "locbeef_rf_v1" / "model.joblib"),
)
MAX_UPLOAD_MB = 10
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Nhan tieng Viet + mo ta cho tung lop
LABEL_VI = {
    "fresh": {"name": "Tươi", "level": "good", "desc": "Thịt còn tươi, màu sắc hồng/đỏ bình thường."},
    "half_fresh": {"name": "Bán tươi", "level": "warn", "desc": "Thịt bắt đầu xuống cấp, nên dùng sớm."},
    "spoiled": {"name": "Hỏng / Ôi thiu", "level": "bad", "desc": "Có dấu hiệu hư hỏng hoặc biến màu, không nên sử dụng."},
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

_bundle = None


def get_bundle():
    """Tai model 1 lan roi cache lai."""
    global _bundle
    if _bundle is None:
        model_path = Path(DEFAULT_MODEL)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Khong tim thay model: {model_path}. "
                "Hay train model truoc (xem README) hoac dat bien moi truong MEAT_MODEL."
            )
        _bundle = joblib.load(model_path)
    return _bundle


def decode_image(file_bytes: bytes, size: int) -> np.ndarray:
    arr = np.frombuffer(file_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Khong doc duoc anh (dinh dang khong hop le).")
    image = cv2.resize(image, (size, size), interpolation=cv2.INTER_AREA)
    return image


def predict_hybrid(image: np.ndarray, bundle: dict) -> tuple[str, dict[str, float], float]:
    features = extract_features(image).reshape(1, -1)
    model = bundle["model"]
    encoder = bundle["label_encoder"]
    class_names = bundle["class_names"]

    # 1. ML Model probability
    probs_raw = model.predict_proba(features)[0]
    p_fresh_ml = float(probs_raw[class_names.index("fresh")])
    p_spoiled_ml = float(probs_raw[class_names.index("spoiled")])

    # 2. Color domain analysis on segmented meat region
    mask = extract_meat_mask(image)
    if mask is None or mask.sum() < 50:
        mask = np.ones((image.shape[0], image.shape[1]), dtype=bool)
    else:
        mask = mask > 0

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    h = hsv[:, :, 0][mask].astype(float)
    s = hsv[:, :, 1][mask].astype(float)
    v = hsv[:, :, 2][mask].astype(float)
    a = lab[:, :, 1][mask].astype(float) # CIELAB a* (Redness)
    l = lab[:, :, 0][mask].astype(float) # CIELAB L* (Lightness)

    # 1. White/Cream Fat Detection (Loại trừ vân mỡ / lớp mỡ trắng tươi khỏi phép đo hỏng)
    fat_mask = (s < 50) & ((v > 160) | (l > 160))

    # 2. Vivid Fresh Red Meat Region (Thịt đỏ tươi sáng)
    vivid_red_mask = (~fat_mask) & ((a > 155) & (l > 115) & (s > 60) & ((h < 18) | (h > 165)))
    vivid_red_ratio = float(vivid_red_mask.mean())

    # 3. Real Spoiled / Discolored / Dark Oxidized Meat (Thịt ôi thiu / hoại tử / ngả màu nâu tím tái xẫm)
    # Greenish/brownish (20 <= H <= 110) OR low redness (a* <= 134) OR dark dull oxidized (L* < 112 & a* < 155)
    spoil_mask = (~fat_mask) & (
        ((h >= 20) & (h <= 110)) | 
        (a <= 134) | 
        ((l < 112) & (a < 155)) |
        ((s < 40) & (v < 155))
    )
    spoil_ratio = float(spoil_mask.mean())

    meat_a = a[~fat_mask] if (~fat_mask).sum() > 20 else a
    mean_a = float(meat_a.mean())

    # Domain color score:
    color_score = 1.0 / (1.0 + np.exp(-((mean_a - 150.0)*0.25 + (vivid_red_ratio - 0.25)*6.0 - (spoil_ratio - 0.15)*8.0)))
    color_score = float(np.clip(color_score, 0.01, 0.99))

    # Fusion strategy
    ml_margin = abs(p_fresh_ml - 0.5) * 2.0
    w_ml = 0.80 if ml_margin > 0.85 else 0.10
    w_color = 1.0 - w_ml

    final_fresh = w_ml * p_fresh_ml + w_color * color_score
    final_fresh = float(np.clip(final_fresh, 0.01, 0.99))

    # Force spoiled if spoil_ratio >= 0.18 OR vivid_red_ratio < 0.20 on non-fat meat
    if spoil_ratio >= 0.18 or (vivid_red_ratio < 0.20 and mean_a < 152):
        final_fresh = min(final_fresh, 0.15)

    final_spoiled = 1.0 - final_fresh
    predicted_label = "fresh" if final_fresh >= 0.50 else "spoiled"

    probabilities = {
        "fresh": float(round(final_fresh, 3)),
        "spoiled": float(round(final_spoiled, 3)),
    }
    confidence = float(max(final_fresh, final_spoiled))
    return predicted_label, probabilities, confidence


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    try:
        bundle = get_bundle()
        return jsonify({"ok": True, "classes": bundle["class_names"], "model": DEFAULT_MODEL})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "Chua chon file anh."}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Ten file rong."}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Dinh dang '{ext}' khong ho tro."}), 400

    try:
        bundle = get_bundle()
        image = decode_image(file.read(), size=bundle["image_size"])
        
        label, probabilities, confidence = predict_hybrid(image, bundle)
        meta = LABEL_VI.get(label, {"name": label, "level": "warn", "desc": ""})

        return jsonify(
            {
                "label": label,
                "label_vi": meta["name"],
                "level": meta["level"],
                "description": meta["desc"],
                "confidence": confidence,
                "probabilities": probabilities,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    # use_reloader=False: tranh reloader theo doi site-packages gay restart lien tuc tren Windows.
    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=False)
