import os
import sys
import torch
import numpy as np
import cv2
import random

# Import model definition
sys.path.append(BASE_DIR)
from train_multi_object_vision import get_ssdlite_model, CarlMultiObjectDataset
import os as _os
_FILE_DIR = _os.path.dirname(_os.path.abspath(__file__))
BASE_DIR = _os.path.dirname(_FILE_DIR)


def verify_predictions():
    device = torch.device("cpu")
    model = get_ssdlite_model()
    
    weights_path = os.path.join(BASE_DIR, "memory", "carl_multi_object_vision.pt")
    if not os.path.exists(weights_path):
        print(f"Error: Model weights not found at {weights_path}!")
        return
        
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.eval()
    
    dataset_dir = os.path.join(BASE_DIR, "memory", "multi_object_dataset")
    dataset = CarlMultiObjectDataset(dataset_dir)
    
    if len(dataset) == 0:
        print("Error: Dataset is empty!")
        return
        
    # Select 4 random samples
    indices = random.sample(range(len(dataset)), min(4, len(dataset)))
    
    grid_imgs = []
    class_names = ["BG", "FOOD", "OBSTACLE", "PREDATOR"]
    
    for idx in indices:
        img_tensor, target = dataset[idx]
        
        # Run inference
        with torch.no_grad():
            predictions = model([img_tensor])
            pred = predictions[0]
            
        # Convert tensor back to BGR image
        img = (img_tensor.permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        # Draw ground truth (Green boxes)
        gt_boxes = target["boxes"].numpy()
        gt_labels = target["labels"].numpy()
        for i in range(len(gt_boxes)):
            xmin, ymin, xmax, ymax = [int(x) for x in gt_boxes[i]]
            label_idx = gt_labels[i]
            cv2.rectangle(img_bgr, (xmin, ymin), (xmax, ymax), (0, 255, 0), 1)
            cv2.putText(img_bgr, f"GT:{class_names[label_idx]}", (xmin, max(12, ymin - 2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
                        
        # Draw predictions (Cyan boxes, score >= 0.5)
        pred_boxes = pred["boxes"].numpy()
        pred_labels = pred["labels"].numpy()
        pred_scores = pred["scores"].numpy()
        
        has_pred = False
        for i in range(len(pred_boxes)):
            score = pred_scores[i]
            if score >= 0.50:
                xmin, ymin, xmax, ymax = [int(x) for x in pred_boxes[i]]
                label_idx = pred_labels[i]
                cv2.rectangle(img_bgr, (xmin, ymin), (xmax, ymax), (255, 255, 0), 1)
                cv2.putText(img_bgr, f"PR:{class_names[label_idx]}({score:.2f})", (xmin, max(24, ymax + 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)
                has_pred = True
                
        if not has_pred and len(gt_boxes) == 0:
            cv2.putText(img_bgr, "PR: BG (Correct)", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
                        
        grid_imgs.append(img_bgr)
        
    # Combine into 2x2 grid
    top_row = np.hstack((grid_imgs[0], grid_imgs[1]))
    bot_row = np.hstack((grid_imgs[2], grid_imgs[3]))
    grid_all = np.vstack((top_row, bot_row))
    
    output_path = os.path.join(BASE_DIR, "multi_object_verification_result.png")
    cv2.imwrite(output_path, grid_all)
    print(f"[VERIFY] Successfully saved predictions grid to {output_path}!")

if __name__ == '__main__':
    verify_predictions()
