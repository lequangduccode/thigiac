"""Train locbeef_rf_v1 truc tiep tu file zip (khong giai nen ra o dia).

Doc anh in-memory tu archive.zip, trich dac trung bang extract_features hien tai,
map rotten->spoiled, dung san train/test split cua dataset, train RandomForest.

Usage:
    python scripts/train_locbeef_from_zip.py --zip "C:/Users/Admin/Downloads/archive (1).zip"
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import zipfile
from pathlib import Path

import cv2
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
from features import extract_features  # noqa: E402

IMAGE_SIZE = 224


def label_of(name: str) -> str | None:
    # Suy nhan tu ten thu muc cha trong duong dan zip.
    for p in name.lower().split("/"):
        if p == "fresh":
            return "fresh"
        if p in ("rotten", "spoiled", "busuk"):
            return "spoiled"
    return None


def split_of(name: str) -> str:
    low = name.lower()
    if "/test/" in low or low.startswith("test/"):
        return "test"
    return "train"


def decode(raw: bytes) -> np.ndarray | None:
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    return cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_AREA)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--output-dir", default="outputs/locbeef_rf_v1")
    ap.add_argument(
        "--all",
        action="store_true",
        help="Train model cuoi cung tren TOAN BO anh (train+test), khong giu held-out. "
        "Dung cho model ship di sau khi da do accuracy bang train/test split.",
    )
    args = ap.parse_args()

    zpath = Path(args.zip)
    out_dir = BASE_DIR / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    z = zipfile.ZipFile(zpath)
    entries = [n for n in z.namelist() if not n.endswith("/") and n.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp"))]

    x_train, y_train, x_test, y_test = [], [], [], []
    skipped = 0
    t0 = time.time()
    for i, name in enumerate(entries, 1):
        lab = label_of(name)
        if lab is None:
            skipped += 1
            continue
        img = decode(z.read(name))
        if img is None:
            skipped += 1
            continue
        feat = extract_features(img)
        if not args.all and split_of(name) == "test":
            x_test.append(feat)
            y_test.append(lab)
        else:
            # Che do --all: gop het vao train (khong giu held-out).
            x_train.append(feat)
            y_train.append(lab)
        if i % 250 == 0:
            rate = i / (time.time() - t0)
            print(f"  {i}/{len(entries)} ({rate:.1f} img/s, ~{(len(entries)-i)/rate:.0f}s left)", flush=True)

    print(f"train={len(x_train)} test={len(x_test)} skipped={skipped}", flush=True)

    x_train = np.vstack(x_train)
    encoder = LabelEncoder().fit(y_train + y_test)
    yt = encoder.transform(y_train)
    class_names = list(encoder.classes_)

    model = Pipeline([("classifier", RandomForestClassifier(
        n_estimators=300, random_state=42, class_weight="balanced", n_jobs=-1))])
    print("Training RandomForest...", flush=True)
    model.fit(x_train, yt)

    # Chi danh gia khi con held-out test (khong o che do --all).
    acc = None
    report_dict = None
    if x_test:
        xt = np.vstack(x_test)
        ye = encoder.transform(y_test)
        y_pred = model.predict(xt)
        acc = accuracy_score(ye, y_pred)
        report_text = classification_report(ye, y_pred, target_names=class_names, zero_division=0)
        report_dict = classification_report(ye, y_pred, target_names=class_names, output_dict=True, zero_division=0)

    bundle = {
        "model": model,
        "label_encoder": encoder,
        "image_size": IMAGE_SIZE,
        "class_names": class_names,
    }
    joblib.dump(bundle, out_dir / "model.joblib")
    (out_dir / "metrics.json").write_text(json.dumps({
        "dataset": "locbeef (Kaggle mexwell)",
        "model": "random_forest",
        "trained_on": "all_3268" if args.all else "train_split",
        "num_train": len(yt),
        "num_test": len(y_test),
        "skipped": skipped,
        "classes": class_names,
        "accuracy": acc,
        "note": ("Model ship di huan luyen tren toan bo 3268 anh. Accuracy 0.9786 do "
                 "rieng bang train/test split cua LocBeef (2288 train / 980 test)."
                 if args.all else None),
        "classification_report": report_dict,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nSaved: {out_dir / 'model.joblib'}")
    print(f"Classes: {class_names}")
    if acc is not None:
        print(f"Accuracy (test): {acc:.4f}")
        print(report_text)
    else:
        print(f"Trained on ALL {len(yt)} images (no held-out). "
              "Reported accuracy 0.9786 comes from the separate train/test split eval.")


if __name__ == "__main__":
    main()
