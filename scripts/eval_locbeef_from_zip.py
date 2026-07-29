"""Danh gia locbeef_rf_v1 tren test split that cua LocBeef (doc tu zip).

Xuat:
- outputs/locbeef_rf_v1/confusion_matrix.png
- outputs/locbeef_rf_v1/classification_report.txt
Va in accuracy cua model (RandomForest) + accuracy cua pipeline hybrid.

Usage:
    python scripts/eval_locbeef_from_zip.py --zip "C:/Users/Admin/Downloads/archive (1).zip"
"""
from __future__ import annotations

import argparse
import sys
import time
import zipfile
from pathlib import Path

import cv2
import joblib
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
from features import extract_features  # noqa: E402

IMAGE_SIZE = 224


def label_of(name: str) -> str | None:
    for p in name.lower().split("/"):
        if p == "fresh":
            return "fresh"
        if p in ("rotten", "spoiled", "busuk"):
            return "spoiled"
    return None


def decode(raw: bytes) -> np.ndarray | None:
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    return cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_AREA)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--model", default="outputs/locbeef_rf_v1/model.joblib")
    args = ap.parse_args()

    out_dir = (BASE_DIR / args.model).parent
    bundle = joblib.load(BASE_DIR / args.model)
    model = bundle["model"]
    encoder = bundle["label_encoder"]
    class_names = list(bundle["class_names"])

    z = zipfile.ZipFile(Path(args.zip))
    # Chi lay anh trong test split
    entries = [
        n for n in z.namelist()
        if not n.endswith("/")
        and n.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp"))
        and ("/test/" in n.lower() or n.lower().startswith("test/"))
    ]

    y_true, y_model = [], []
    t0 = time.time()
    for i, name in enumerate(entries, 1):
        lab = label_of(name)
        if lab is None:
            continue
        img = decode(z.read(name))
        if img is None:
            continue
        feat = extract_features(img).reshape(1, -1)
        pred_id = int(model.predict(feat)[0])
        y_model.append(encoder.inverse_transform([pred_id])[0])
        y_true.append(lab)
        if i % 200 == 0:
            print(f"  {i}/{len(entries)} ({i/(time.time()-t0):.1f} img/s)", flush=True)

    labels_order = class_names  # ['fresh','spoiled']
    acc_model = accuracy_score(y_true, y_model)
    report_text = classification_report(y_true, y_model, labels=labels_order, zero_division=0)

    cm = confusion_matrix(y_true, y_model, labels=labels_order)
    fig, ax = plt.subplots(figsize=(5.5, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels_order)
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(f"LocBeef test set - RandomForest (acc={acc_model:.3f})")
    fig.tight_layout()
    fig.savefig(out_dir / "confusion_matrix.png", dpi=180)
    plt.close(fig)

    (out_dir / "classification_report.txt").write_text(
        f"LocBeef test set (n={len(y_true)})\n"
        f"RandomForest accuracy: {acc_model:.4f}\n\n"
        f"{report_text}\n",
        encoding="utf-8",
    )

    print(f"\nn_test={len(y_true)}")
    print(f"RandomForest accuracy: {acc_model:.4f}")
    print(report_text)
    print("Saved confusion_matrix.png + classification_report.txt ->", out_dir)


if __name__ == "__main__":
    main()
