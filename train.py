
# Fine-tune YOLOv8n on the filtered CrowdHuman dataset
# Run: python3 train.py

import shutil
from pathlib import Path

import torch
from ultralytics import YOLO

# Project directory
project_dir = Path(__file__).resolve().parent

# Use the filtered dataset (original dataset remains untouched)
dataset_dir = (
    project_dir
    / "datasets"
    / "CrowdHuman dataset"
    / "dataset_filtered"
)

# Check dataset folders
for split in ["train", "val", "test"]:
    images_dir = dataset_dir / split / "images"
    labels_dir = dataset_dir / split / "labels"

    if not images_dir.is_dir() or not labels_dir.is_dir():
        raise FileNotFoundError(
            f"Missing images or labels folder for {split}"
        )

# Use the YAML created during dataset preparation
yaml_path = dataset_dir / "crowdhuman.yaml"

if not yaml_path.is_file():
    raise FileNotFoundError(f"Dataset YAML not found: {yaml_path}")

# Choose Apple GPU if available; otherwise use CPU
device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Training device:", device)
print("Dataset YAML:", yaml_path)

# Load pretrained YOLOv8n
model = YOLO("yolov8n.pt")

# Train the model
model.train(
    data=str(yaml_path),
    epochs=30,
    imgsz=640,
    batch=2,
    workers=2,
    device=device,
    patience=8,
    project=str(project_dir / "runs" / "ucrowdlens"),
    name="crowdhuman_yolov8n",
    seed=42
)

# Save best weights into models/best.pt
best_weights = (
    project_dir
    / "runs"
    / "ucrowdlens"
    / "crowdhuman_yolov8n"
    / "weights"
    / "best.pt"
)

models_dir = project_dir / "models"
models_dir.mkdir(exist_ok=True)

if best_weights.exists():
    destination = models_dir / "best.pt"
    shutil.copy2(best_weights, destination)
    print("Best model saved to:", destination)
else:
    raise FileNotFoundError(
        f"Best weights not found: {best_weights}"
    )

# Evaluate on the held-out test split
best_model = YOLO(str(models_dir / "best.pt"))
metrics = best_model.val(
    data=str(yaml_path),
    split="test",
    imgsz=640,
    batch=2,
    workers=2,
    device=device
)

print("mAP@0.5     :", round(metrics.box.map50, 3))
print("mAP@0.5:0.95:", round(metrics.box.map, 3))
print("Training and evaluation complete!")
