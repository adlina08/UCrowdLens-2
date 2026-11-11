
from pathlib import Path
import shutil

BASE = Path("datasets/CrowdHuman dataset/dataset")

for split in ["train", "val", "test"]:
    labels_dir = BASE / split / "labels"
    backup_dir = BASE / split / "labels_backup"

    if backup_dir.exists():
        raise RuntimeError(
            f"Backup already exists: {backup_dir}. "
            "Stop to avoid overwriting original labels."
        )

    shutil.copytree(labels_dir, backup_dir)

    removed = 0
    kept = 0

    for file in labels_dir.glob("*.txt"):
        lines = file.read_text(encoding="utf-8").splitlines()

        person_lines = []

        for line in lines:
            parts = line.split()

            if not parts:
                continue

            if parts[0] == "0":
                person_lines.append(line)
                kept += 1
            else:
                removed += 1

        file.write_text(
            "\n".join(person_lines) +
            ("\n" if person_lines else ""),
            encoding="utf-8"
        )

    print(f"\n{split.upper()}")
    print(f"Person annotations kept: {kept}")
    print(f"Other annotations removed: {removed}")
    print(f"Original labels backed up to: {backup_dir}")

print("\nCleaning completed!")
