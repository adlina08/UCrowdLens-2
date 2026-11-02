# UCrowdLens (simple version)

## Folder
```
UCrowdLens/
├── app.py            <- the whole system (run this)
├── train.py          <- train YOLOv8 on CrowdHuman
├── requirements.txt
├── datasets/crowdhuman/     <<< PUT THE DATASET HERE
│   ├── images/train  images/val  images/test
│   └── labels/train  labels/val  labels/test
├── models/           <- best.pt appears here after training
├── templates/  static/
```

## Steps
1. `pip install -r requirements.txt`
2. Download the dataset from Kaggle (menhari / crowd-human-crowd-detection) and put the
   images and the .txt labels into `datasets/crowdhuman/` as shown above.
   (If your folders are named differently, just rename them to match, or edit the 3 lines in `train.py`.)
3. `python train.py`   (50 epochs - slow on CPU; use a GPU / Google Colab if you can, then copy best.pt to `models/`)
4. `python app.py`  then open http://127.0.0.1:5000
   - If there is no `models/best.pt`, it uses plain `yolov8n.pt` so you can still demo.

Admin login (click LOGIN):  `admin` / `admin123`
