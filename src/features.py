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


def normalized_histogram(image: np.ndarray, color_space: int, channels: list[int], bins: list[int]) -> np.ndarray:
    converted = cv2.cvtColor(image, color_space)
    hist = cv2.calcHist([converted], channels, None, bins, [0, 256] * len(channels))
    hist = cv2.normalize(hist, hist).flatten()
    return hist.astype(np.float32)


def color_statistics(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    stats = []
    for converted in (hsv, lab):
        for channel in cv2.split(converted):
            stats.extend(
                [
                    float(np.mean(channel)),
                    float(np.std(channel)),
                    float(np.percentile(channel, 10)),
                    float(np.percentile(channel, 50)),
                    float(np.percentile(channel, 90)),
                ]
            )
    return np.array(stats, dtype=np.float32)


def local_binary_pattern(gray: np.ndarray) -> np.ndarray:
    center = gray[1:-1, 1:-1]
    codes = np.zeros_like(center, dtype=np.uint8)
    neighbors = [
        gray[:-2, :-2],
        gray[:-2, 1:-1],
        gray[:-2, 2:],
        gray[1:-1, 2:],
        gray[2:, 2:],
        gray[2:, 1:-1],
        gray[2:, :-2],
        gray[1:-1, :-2],
    ]
    for bit, neighbor in enumerate(neighbors):
        codes |= ((neighbor >= center).astype(np.uint8) << bit)
    hist, _ = np.histogram(codes, bins=32, range=(0, 256), density=True)
    return hist.astype(np.float32)


def extract_features(image: np.ndarray) -> np.ndarray:
    image = apply_clahe_bgr(image)
    hsv_hist = normalized_histogram(image, cv2.COLOR_BGR2HSV, [0, 1, 2], [16, 8, 8])
    lab_hist = normalized_histogram(image, cv2.COLOR_BGR2LAB, [0, 1, 2], [8, 8, 8])
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    texture = local_binary_pattern(gray)
    stats = color_statistics(image)
    return np.concatenate([hsv_hist, lab_hist, stats, texture])


def load_feature_matrix(data_dir: str | Path, size: int = 224) -> tuple[np.ndarray, np.ndarray, list[Path]]:
    samples = list_images(data_dir)
    features = []
    labels = []
    paths = []
    for path, label in samples:
        image = read_image(path, size=size)
        features.append(extract_features(image))
        labels.append(label)
        paths.append(path)
    return np.vstack(features), np.array(labels), paths

