from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


CLASS_COLORS = {
    "fresh": np.array([75, 35, 200], dtype=np.uint8),
    "half_fresh": np.array([105, 75, 145], dtype=np.uint8),
    "spoiled": np.array([55, 105, 85], dtype=np.uint8),
}


def make_meat_like_image(base_bgr: np.ndarray, rng: np.random.Generator, size: int = 224) -> np.ndarray:
    image = np.full((size, size, 3), base_bgr, dtype=np.uint8)
    noise = rng.normal(0, 10, image.shape).astype(np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    for _ in range(rng.integers(8, 18)):
        center = (int(rng.integers(0, size)), int(rng.integers(0, size)))
        axes = (int(rng.integers(12, 55)), int(rng.integers(8, 35)))
        angle = float(rng.integers(0, 180))
        color_shift = rng.normal(0, 12, 3)
        color = np.clip(base_bgr.astype(np.float32) + color_shift, 0, 255).astype(np.uint8).tolist()
        cv2.ellipse(image, center, axes, angle, 0, 360, color, -1, lineType=cv2.LINE_AA)

    blur = int(rng.choice([3, 5, 7]))
    return cv2.GaussianBlur(image, (blur, blur), 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create synthetic demo images for pipeline testing.")
    parser.add_argument("--output", default="data/demo_meat")
    parser.add_argument("--images-per-class", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    rng = np.random.default_rng(args.seed)
    for class_name, base_color in CLASS_COLORS.items():
        class_dir = output / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        for index in range(args.images_per_class):
            image = make_meat_like_image(base_color, rng)
            cv2.imwrite(str(class_dir / f"{class_name}_{index:03d}.png"), image)
    print(f"Da tao dataset minh hoa tai: {output.resolve()}")


if __name__ == "__main__":
    main()
