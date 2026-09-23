# Walkthrough: Vision Pipelines & Object Detection
### *SSD-Lite Training, Dataset Collection & Verification Scripts*

This walkthrough covers the 6 vision training, collection, and evaluation scripts in `brain/` that build and test the SSD-Lite MobileNet-V3 multi-object vision system used by CARL to detect food, obstacles, and sibling bodies.

---

## 1. Dataset Collection Scripts

### `brain/collect_vision_dataset.py` & `brain/collect_multi_object_dataset.py`
* **Purpose:** Automates data collection inside MuJoCo. Spins CARL's head camera, captures rendered RGB frames, and computes exact 2D bounding boxes $(x_{min}, y_{min}, x_{max}, y_{max})$ from 3D geom coordinates.
* **Output:** Saves image frames (`.png`) and bounding box annotations (`.json`) into `memory/vision_dataset/` and `memory/multi_object_dataset/`.

---

## 2. SSD-Lite Training Scripts

### `brain/train_vision.py` & `brain/train_multi_object_vision.py`
* **Model:** PyTorch `SSDLite320_MobileNet_V3_Large` modified with a 4-class classification head:
  * Class 0: Background
  * Class 1: Food (Red geoms)
  * Class 2: Obstacle (Gray/Blue walls)
  * Class 3: Sibling Robot
* **Training Loop:** Loads dataset images, applies random augmentation (brightness, contrast, flipping), runs PyTorch Adam optimizer over 20 epochs, and saves trained model weights to `memory/carl_multi_object_vision.pt`.

---

## 3. Visual Verification Scripts

### `brain/verify_vision_predictions.py` & `brain/verify_multi_object_predictions.py`
* **Purpose:** Runs trained PyTorch weights against test images. Draws colored detection bounding boxes, confidence scores, and class labels onto test frames.
* **Output:** Saves visualization proof images `vision_verification_result.png` and `multi_object_verification_result.png` to verify object detection accuracy before deployment into `carl_simulation.py`.
