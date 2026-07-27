from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def list_images(data_dir: str | Path) -> list[tuple[Path, str]]:
    root = Path(data_dir)
    samples: list[tuple[Path, str]] = []
    for class_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for path in sorted(class_dir.rglob("*")):
            if path.suffix.lower() in IMAGE_EXTENSIONS:
                samples.append((path, class_dir.name))
    if not samples:
        raise ValueError(f"Khong tim thay anh trong {root}")
    return samples


def read_image(path: str | Path, size: int = 224) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Khong doc duoc anh: {path}")
    image = cv2.resize(image, (size, size), interpolation=cv2.INTER_AREA)
    return image


def apply_clahe_bgr(image: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_l = clahe.apply(l_channel)
    enhanced = cv2.merge((enhanced_l, a_channel, b_channel))
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def extract_meat_mask(image: np.ndarray) -> np.ndarray | None:
    """Tao mask giu lai pixel thit, loai bo nen trang/sang/xam.

    Logic:
    - Loai pixel qua sang (V > 220, S < 30): nen trang / dia
    - Loai pixel qua toi (V < 20): bong toi
    - Giu lai pixel co mau sac (S > 20) hoac co V trung binh
    Fallback toan anh neu meat region < 3%.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1].astype(np.int32)
    v = hsv[:, :, 2].astype(np.int32)

    # Pixel thit: khong qua trang, khong qua toi
    not_white = ~((s < 30) & (v > 220))
    not_black = v > 20
    mask = (not_white & not_black).astype(np.uint8)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    min_pixels = int(image.shape[0] * image.shape[1] * 0.03)
    return mask if int(mask.sum()) >= min_pixels else None


def _channel_hist(pixels: np.ndarray, lo: float, hi: float, n_bins: int) -> np.ndarray:
    """1D histogram, normalized theo mat do (density=True)."""
    hist, _ = np.histogram(pixels, bins=n_bins, range=(lo, hi), density=True)
    # density=True cho ra NaN neu pixels rong -> xu ly an toan
    hist = np.nan_to_num(hist, nan=0.0)
    return hist.astype(np.float32)


def extract_features(image: np.ndarray) -> np.ndarray:
    """Trich xuat dac trung tu vung thit (loai bo nen).

    Vector feature:
    - HSV: 1D hist moi kenh (H:32 bins 0-180, S:16 bins, V:16 bins) = 64 dims
    - Lab: 1D hist moi kenh (L:16, a:16, b:16) = 48 dims
    - Thong ke HSV + Lab (mean, std, p10, p50, p90 x 6 kenh) = 30 dims
    - LBP texture = 32 dims
    Tong: 174 dims
    """
    image = apply_clahe_bgr(image)
    mask = extract_meat_mask(image)

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    feats: list[np.ndarray] = []

    # ---- 1D histograms per channel (meat pixels only) ----
    # HSV: H range la 0-179 trong OpenCV (khong phai 0-255!)
    channel_specs = [
        (hsv,  0,   0, 180, 32),  # Hue       0-179
        (hsv,  1,   0, 256, 16),  # Saturation 0-255
        (hsv,  2,   0, 256, 16),  # Value      0-255
        (lab,  0,   0, 256, 16),  # L          0-255
        (lab,  1,   0, 256, 16),  # a          0-255
        (lab,  2,   0, 256, 16),  # b          0-255
    ]
    for (img_arr, ch_idx, lo, hi, n_bins) in channel_specs:
        channel = img_arr[:, :, ch_idx]
        pixels = channel[mask > 0].astype(np.float32) if mask is not None else channel.flatten().astype(np.float32)
        if len(pixels) == 0:
            pixels = channel.flatten().astype(np.float32)
        feats.append(_channel_hist(pixels, lo, hi, n_bins))

    # ---- Color statistics (mean, std, p10, p50, p90) ----
    for img_arr in (hsv, lab):
        for ch_idx in range(3):
            channel = img_arr[:, :, ch_idx]
            pixels = channel[mask > 0].astype(np.float32) if mask is not None else channel.flatten().astype(np.float32)
            if len(pixels) == 0:
                pixels = channel.flatten().astype(np.float32)
            feats.append(np.array([
                float(np.mean(pixels)),
                float(np.std(pixels)),
                float(np.percentile(pixels, 10)),
                float(np.percentile(pixels, 50)),
                float(np.percentile(pixels, 90)),
            ], dtype=np.float32))

    # ---- LBP texture ----
    center = gray[1:-1, 1:-1]
    codes = np.zeros_like(center, dtype=np.uint8)
    neighbors = [
        gray[:-2, :-2], gray[:-2, 1:-1], gray[:-2, 2:],
        gray[1:-1, 2:],
        gray[2:, 2:],   gray[2:, 1:-1],  gray[2:, :-2],
        gray[1:-1, :-2],
    ]
    for bit, neighbor in enumerate(neighbors):
        codes |= ((neighbor >= center).astype(np.uint8) << bit)
    lbp_hist, _ = np.histogram(codes, bins=32, range=(0, 256), density=True)
    feats.append(np.nan_to_num(lbp_hist.astype(np.float32), nan=0.0))

    return np.concatenate(feats)


def load_feature_matrix(
    data_dir: str | Path, size: int = 224
) -> tuple[np.ndarray, np.ndarray, list[Path]]:
    samples = list_images(data_dir)
    features, labels, paths = [], [], []
    for path, label in samples:
        image = read_image(path, size=size)
        features.append(extract_features(image))
        labels.append(label)
        paths.append(path)
    return np.vstack(features), np.array(labels), paths
