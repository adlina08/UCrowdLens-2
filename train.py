
from pathlib import Path
import torch
from ultralytics import YOLO

def main():
    BASE_DIR = Path(__file__).resolve().parent
    DATA_YAML = BASE_DIR / "crowdhuman.yaml"

    # Check GPU
    print("CUDA available:", torch.cuda.is_available())

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA not available. Check PyTorch installation."
        )

    print("GPU:", torch.cuda.get_device_name(0))

    # Start fresh from pretrained YOLOv8 nano
    model = YOLO("yolov8n.pt")

    # Train for 50 epochs
    results = model.train(
        data=str(DATA_YAML),
        epochs=50,
        imgsz=640,
        batch=8,
        device=0,
        workers=0,
        patience=50,
        project=str(BASE_DIR / "runs" / "detect"),
        name="ucrowdlens_50epochs",
        exist_ok=False,
        plots=True
    )

    print("50-epoch training completed!")

if __name__ == "__main__":
    main()
