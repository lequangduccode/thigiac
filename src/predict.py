from __future__ import annotations

import argparse
from pathlib import Path

import joblib

from features import extract_features, read_image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict meat freshness from an image.")
    parser.add_argument("--model", required=True, help="Duong dan file model.joblib")
    parser.add_argument("--image", required=True, help="Duong dan anh can du doan")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundle = joblib.load(args.model)
    image = read_image(args.image, size=bundle["image_size"])
    features = extract_features(image).reshape(1, -1)
    model = bundle["model"]
    encoder = bundle["label_encoder"]

    predicted_id = model.predict(features)[0]
    label = encoder.inverse_transform([predicted_id])[0]
    print(f"Anh: {Path(args.image).name}")
    print(f"Du doan: {label}")

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features)[0]
        for class_name, probability in zip(bundle["class_names"], probabilities):
            print(f"{class_name}: {probability:.3f}")


if __name__ == "__main__":
    main()

