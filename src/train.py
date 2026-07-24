from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC

from features import load_feature_matrix


def build_model(model_name: str) -> Pipeline:
    if model_name == "svm":
        classifier = SVC(kernel="rbf", C=10.0, gamma="scale", probability=True, class_weight="balanced")
        return Pipeline([("scaler", StandardScaler()), ("classifier", classifier)])
    if model_name == "random_forest":
        classifier = RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced")
        return Pipeline([("classifier", classifier)])
    raise ValueError(f"Model khong hop le: {model_name}")


def save_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, labels: list[str], output_path: Path) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=np.arange(len(labels)))
    fig, ax = plt.subplots(figsize=(7, 6))
    display = ConfusionMatrixDisplay(confusion_matrix=matrix, display_labels=labels)
    display.plot(ax=ax, cmap="Blues", colorbar=False, xticks_rotation=30)
    ax.set_title("Confusion matrix")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train meat freshness classifier.")
    parser.add_argument("--data", required=True, help="Thu muc dataset co cac thu muc con la ten lop.")
    parser.add_argument("--model", choices=["svm", "random_forest"], default="svm")
    parser.add_argument("--output-dir", default="outputs/meat_freshness")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--image-size", type=int, default=224)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    x, labels, paths = load_feature_matrix(args.data, size=args.image_size)
    encoder = LabelEncoder()
    y = encoder.fit_transform(labels)

    x_train, x_test, y_train, y_test, paths_train, paths_test = train_test_split(
        x,
        y,
        paths,
        test_size=args.test_size,
        random_state=42,
        stratify=y,
    )

    model = build_model(args.model)
    model.fit(x_train, y_train)
    y_pred = model.predict(x_test)

    class_names = list(encoder.classes_)
    report = classification_report(y_test, y_pred, target_names=class_names, output_dict=True, zero_division=0)
    report_text = classification_report(y_test, y_pred, target_names=class_names, zero_division=0)
    accuracy = accuracy_score(y_test, y_pred)

    bundle = {
        "model": model,
        "label_encoder": encoder,
        "image_size": args.image_size,
        "class_names": class_names,
    }
    joblib.dump(bundle, output_dir / "model.joblib")
    save_confusion_matrix(y_test, y_pred, class_names, output_dir / "confusion_matrix.png")

    result = {
        "model": args.model,
        "data_dir": str(Path(args.data).resolve()),
        "num_images": len(paths),
        "num_train": len(paths_train),
        "num_test": len(paths_test),
        "classes": class_names,
        "accuracy": accuracy,
        "classification_report": report,
    }
    (output_dir / "metrics.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "classification_report.txt").write_text(report_text, encoding="utf-8")

    print(f"Da luu model: {output_dir / 'model.joblib'}")
    print(f"Accuracy: {accuracy:.4f}")
    print(report_text)


if __name__ == "__main__":
    main()

