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

from features import extract_features  # noqa: E402

# ---------------------------------------------------------------------------
# Cau hinh
# ---------------------------------------------------------------------------
DEFAULT_MODEL = os.environ.get(
    "MEAT_MODEL",
    str(BASE_DIR / "outputs" / "demo_v2" / "model.joblib"),
)
MAX_UPLOAD_MB = 10
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Nhan tieng Viet + mo ta cho tung lop
LABEL_VI = {
    "fresh": {"name": "Tuoi", "level": "good", "desc": "Thit con tuoi, mau sac binh thuong."},
    "half_fresh": {"name": "Ban tuoi", "level": "warn", "desc": "Thit bat dau xuong cap, nen dung som."},
    "spoiled": {"name": "Hong / On thiu", "level": "bad", "desc": "Co dau hieu hu hong, khong nen su dung."},
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
        features = extract_features(image).reshape(1, -1)

        model = bundle["model"]
        encoder = bundle["label_encoder"]
        class_names = bundle["class_names"]

        predicted_id = int(model.predict(features)[0])
        label = encoder.inverse_transform([predicted_id])[0]

        probabilities = {}
        confidence = None
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(features)[0]
            probabilities = {name: float(p) for name, p in zip(class_names, probs)}
            confidence = float(max(probs))

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
