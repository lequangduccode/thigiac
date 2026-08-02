"""Tao cac hinh minh hoa cho bao cao tu file zip LocBeef + model da train.

Xuat PNG vao outputs/report_figures/:
- dataset_samples.png     : luoi anh mau fresh vs rotten
- preprocessing.png       : original -> CLAHE -> mask -> vung thit
- color_distribution.png  : histogram a* (do do) fresh vs rotten tren vung thit
- demo_predictions.png    : du doan cua model tren anh test (phan demo)
- feature_importance.png  : do quan trong dac trung cua RandomForest theo nhom

Usage:
    python scripts/make_report_figures.py --zip "C:/Users/Admin/Downloads/archive (1).zip"
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import cv2
import joblib
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
from features import apply_clahe_bgr, extract_features, extract_meat_mask  # noqa: E402

IMAGE_SIZE = 224
OUT = BASE_DIR / "outputs" / "report_figures"


def decode(raw: bytes, size: int = IMAGE_SIZE) -> np.ndarray:
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)


def rgb(img_bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


def collect(z: zipfile.ZipFile, split: str, cls: str, n: int) -> list[str]:
    names = [
        x for x in z.namelist()
        if x.lower().endswith(".jpg") and f"/{split}/" in x.lower() and f"/{cls}/" in x.lower()
    ]
    return sorted(names)[:n]


def fig_dataset_samples(z: zipfile.ZipFile) -> None:
    fresh = collect(z, "test", "fresh", 4)
    rotten = collect(z, "test", "rotten", 4)
    fig, axes = plt.subplots(2, 4, figsize=(11, 6))
    for j, name in enumerate(fresh):
        axes[0, j].imshow(rgb(decode(z.read(name))))
        axes[0, j].set_title("fresh", color="#2fbf71", fontsize=11)
        axes[0, j].axis("off")
    for j, name in enumerate(rotten):
        axes[1, j].imshow(rgb(decode(z.read(name))))
        axes[1, j].set_title("rotten (spoiled)", color="#ef4d5b", fontsize=11)
        axes[1, j].axis("off")
    fig.suptitle("Anh mau bo LocBeef: hang tren = tuoi, hang duoi = hong", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "dataset_samples.png", dpi=150)
    plt.close(fig)


def fig_preprocessing(z: zipfile.ZipFile) -> None:
    name = collect(z, "test", "fresh", 1)[0]
    img = decode(z.read(name))
    clahe = apply_clahe_bgr(img)
    mask = extract_meat_mask(clahe)
    if mask is None:
        mask = np.ones(clahe.shape[:2], dtype=np.uint8)
    masked = clahe.copy()
    masked[mask == 0] = 0

    panels = [
        (rgb(img), "1. Anh goc (224x224)"),
        (rgb(clahe), "2. Sau CLAHE"),
        (mask * 255, "3. Mask vung thit"),
        (rgb(masked), "4. Vung thit giu lai"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6))
    for ax, (im, title) in zip(axes, panels):
        ax.imshow(im, cmap="gray" if im.ndim == 2 else None)
        ax.set_title(title, fontsize=10)
        ax.axis("off")
    fig.suptitle("Quy trinh tien xu ly va tach vung thit", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "preprocessing.png", dpi=150)
    plt.close(fig)


def fig_color_distribution(z: zipfile.ZipFile) -> None:
    def mean_a_hist(cls: str, n: int = 60) -> np.ndarray:
        vals = []
        for name in collect(z, "train", cls, n):
            img = apply_clahe_bgr(decode(z.read(name)))
            mask = extract_meat_mask(img)
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            a = lab[:, :, 1]
            a = a[mask > 0] if mask is not None else a.flatten()
            vals.append(float(np.mean(a)))
        return np.array(vals)

    fresh_a = mean_a_hist("fresh")
    rotten_a = mean_a_hist("rotten")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bins = np.linspace(120, 180, 30)
    ax.hist(fresh_a, bins=bins, alpha=0.65, label="fresh", color="#2fbf71")
    ax.hist(rotten_a, bins=bins, alpha=0.65, label="rotten (spoiled)", color="#ef4d5b")
    ax.set_xlabel("Gia tri trung binh kenh a* (do do CIELAB) tren vung thit")
    ax.set_ylabel("So anh")
    ax.set_title("Phan bo do do a*: thit tuoi do hon thit hong")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "color_distribution.png", dpi=150)
    plt.close(fig)


def fig_demo_predictions(z: zipfile.ZipFile, bundle: dict) -> None:
    model = bundle["model"]
    encoder = bundle["label_encoder"]
    class_names = list(bundle["class_names"])
    names = collect(z, "test", "fresh", 3) + collect(z, "test", "rotten", 3)
    truths = ["fresh"] * 3 + ["spoiled"] * 3

    fig, axes = plt.subplots(2, 3, figsize=(11, 9.2))
    for ax, name, truth in zip(axes.ravel(), names, truths):
        img = decode(z.read(name))
        feat = extract_features(img).reshape(1, -1)
        pid = int(model.predict(feat)[0])
        pred = encoder.inverse_transform([pid])[0]
        probs = model.predict_proba(feat)[0]
        conf = float(max(probs))
        ok = (pred == truth)
        ax.imshow(rgb(img))
        ax.axis("off")
        color = "#2fbf71" if ok else "#ef4d5b"
        mark = "\u2713" if ok else "\u2717"
        ax.set_title(
            f"{mark} du doan: {pred} ({conf*100:.0f}%)\nthuc te: {truth}",
            color=color, fontsize=10,
        )
    fig.suptitle("Demo du doan cua model tren anh test LocBeef", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.subplots_adjust(hspace=0.28)
    fig.savefig(OUT / "demo_predictions.png", dpi=150)
    plt.close(fig)


def fig_feature_importance(bundle: dict) -> None:
    rf = bundle["model"].named_steps["classifier"]
    imp = rf.feature_importances_  # 174
    groups = [
        ("Histogram HSV", 0, 64),
        ("Histogram Lab", 64, 112),
        ("Thong ke mau", 112, 142),
        ("LBP texture", 142, 174),
    ]
    labels = [g[0] for g in groups]
    sums = [float(imp[a:b].sum()) for _, a, b in groups]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(labels, sums, color=["#4f8cff", "#8b5cf6", "#f4a935", "#2fbf71"])
    for bar, v in zip(bars, sums):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.005, f"{v*100:.1f}%",
                ha="center", fontsize=10)
    ax.set_ylabel("Tong do quan trong (RandomForest)")
    ax.set_title("Dong gop cua tung nhom dac trung vao mo hinh")
    ax.set_ylim(0, max(sums) * 1.25)
    fig.tight_layout()
    fig.savefig(OUT / "feature_importance.png", dpi=150)
    plt.close(fig)


def fig_pipeline_diagram() -> None:
    steps = [
        ("Anh dau vao\n(RGB)", "#4f8cff"),
        ("Resize 224x224\n+ CLAHE", "#4f8cff"),
        ("Tach vung thit\n(masking)", "#8b5cf6"),
        ("Trich dac trung\nHSV/Lab/LBP\n(174 chieu)", "#f4a935"),
        ("RandomForest", "#2fbf71"),
        ("Nhan + xac suat\nfresh / spoiled", "#2fbf71"),
    ]
    fig, ax = plt.subplots(figsize=(12, 2.6))
    ax.axis("off")
    n = len(steps)
    w, h, gap = 1.5, 1.1, 0.55
    for i, (text, color) in enumerate(steps):
        x = i * (w + gap)
        box = plt.Rectangle((x, 0), w, h, facecolor=color, alpha=0.18,
                            edgecolor=color, linewidth=2, zorder=2)
        ax.add_patch(box)
        ax.text(x + w / 2, h / 2, text, ha="center", va="center", fontsize=9, zorder=3)
        if i < n - 1:
            ax.annotate("", xy=(x + w + gap, h / 2), xytext=(x + w, h / 2),
                        arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.8))
    ax.set_xlim(-0.2, n * (w + gap))
    ax.set_ylim(-0.2, h + 0.2)
    fig.suptitle("So do khoi pipeline nhan biet thit tuoi", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "pipeline_diagram.png", dpi=150)
    plt.close(fig)


def fig_eda_scatter(z: zipfile.ZipFile) -> None:
    def stats(cls: str, n: int = 80):
        aa, ll = [], []
        for name in collect(z, "train", cls, n):
            img = apply_clahe_bgr(decode(z.read(name)))
            mask = extract_meat_mask(img)
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            a = lab[:, :, 1]; l = lab[:, :, 0]
            sel = mask > 0 if mask is not None else np.ones(a.shape, bool)
            aa.append(float(a[sel].mean())); ll.append(float(l[sel].mean()))
        return np.array(aa), np.array(ll)

    fa, fl = stats("fresh")
    ra, rl = stats("rotten")
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.scatter(fa, fl, c="#2fbf71", label="fresh", alpha=0.7, edgecolors="none")
    ax.scatter(ra, rl, c="#ef4d5b", label="rotten (spoiled)", alpha=0.7, edgecolors="none")
    ax.set_xlabel("Trung binh a* (do do)")
    ax.set_ylabel("Trung binh L* (do sang)")
    ax.set_title("Phan bo mau vung thit: tuoi vs hong tach biet kha ro")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "eda_scatter.png", dpi=150)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--model", default="outputs/locbeef_rf_v1/model.joblib")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(Path(args.zip))
    bundle = joblib.load(BASE_DIR / args.model)

    print("dataset_samples...", flush=True)
    fig_dataset_samples(z)
    print("preprocessing...", flush=True)
    fig_preprocessing(z)
    print("color_distribution...", flush=True)
    fig_color_distribution(z)
    print("demo_predictions...", flush=True)
    fig_demo_predictions(z, bundle)
    print("feature_importance...", flush=True)
    fig_feature_importance(bundle)
    print("pipeline_diagram...", flush=True)
    fig_pipeline_diagram()
    print("eda_scatter...", flush=True)
    fig_eda_scatter(z)
    print("Done ->", OUT)


if __name__ == "__main__":
    main()
