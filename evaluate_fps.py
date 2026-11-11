
import time
import cv2
from ultralytics import YOLO

# Load 50-epoch model
model = YOLO("runs/detect/ucrowdlens_50epochs/weights/best.pt")

# Test image
image_path = "datasets/CrowdHuman dataset/dataset/test/images/284193,2f44d000372d8580.jpg"
image = cv2.imread(image_path)

if image is None:
    raise FileNotFoundError("Image not found!")

# Settings
image_sizes = [640, 800, 960]
confidence = 0.25
num_runs = 30

for size in image_sizes:
    print(f"\nTesting 50 epochs | imgsz={size} | conf={confidence}")

    # Warm up
    for _ in range(3):
        model.predict(
            image,
            imgsz=size,
            conf=confidence,
            device="cpu",
            verbose=False
        )

    # FPS testing
    start = time.perf_counter()

    for _ in range(num_runs):
        model.predict(
            image,
            imgsz=size,
            conf=confidence,
            device="cpu",
            verbose=False
        )

    elapsed = time.perf_counter() - start

    fps = num_runs / elapsed

    print(f"Average time: {elapsed / num_runs * 1000:.2f} ms")
    print(f"Average FPS: {fps:.2f}")
