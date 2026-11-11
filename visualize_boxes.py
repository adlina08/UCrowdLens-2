
from ultralytics import YOLO
import cv2
import os

# Load 50-epoch model
model = YOLO("runs/detect/ucrowdlens_50epochs/weights/best.pt")

# Select crowded image
image_path = "datasets/CrowdHuman dataset/dataset/test/images/284193,2f44d000372d8580.jpg"

# Run prediction
results = model.predict(
    source=image_path,
    conf=0.15,
    imgsz=960,
    verbose=False
)

# Count detected people
count = len(results[0].boxes)
print("Predicted people:", count)

# Draw bounding boxes
image = results[0].plot()

# Save image in project folder
output_dir = os.path.join(os.path.dirname(__file__), "box_results")
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "crowd_boxes_960.jpg")

saved = cv2.imwrite(output_path, image)

print("Predicted people:", len(results[0].boxes))
print("Saved successfully:", saved)
print("Image location:", output_path)