
from pathlib import Path
import csv
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent

IMAGE_DIR = BASE_DIR / "datasets/CrowdHuman dataset/dataset/test/images"
CSV_PATH = BASE_DIR / "manual_counts.csv"
MODEL_PATH = "runs/detect/ucrowdlens_50epochs/weights/best.pt"
OUTPUT_PATH = "count_evaluation_50epochs_015_960.csv"

model = YOLO(str(MODEL_PATH))

if not CSV_PATH.exists():
    with open(CSV_PATH, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["image_name", "actual_count"])

    print("Created manual_counts.csv")
    print("Fill in image names and manually counted people first.")

else:
    results = []

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            image_name = row["image_name"]
            actual_count = int(row["actual_count"])
            image_path = IMAGE_DIR / image_name

            if not image_path.exists():
                print(f"Image not found: {image_name}")
                continue

            prediction = model.predict(
                source=str(image_path),
                conf=0.15,
                imgsz=960,
                verbose=False
            )[0]

            predicted_count = len(prediction.boxes)
            error = abs(actual_count - predicted_count)

            results.append([
                image_name,
                actual_count,
                predicted_count,
                error
            ])

            print(
                f"{image_name}: "
                f"Actual={actual_count}, "
                f"Predicted={predicted_count}, "
                f"Error={error}"
            )

    if results:
        mae = sum(row[3] for row in results) / len(results)

        with open(OUTPUT_PATH, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "image_name",
                "actual_count",
                "predicted_count",
                "absolute_error"
            ])
            writer.writerows(results)

        print(f"\nImages evaluated: {len(results)}")
        print(f"Mean Absolute Error (MAE): {mae:.3f}")
        print(f"Results saved to: {OUTPUT_PATH}")
    else:
        print("No valid images evaluated.")
