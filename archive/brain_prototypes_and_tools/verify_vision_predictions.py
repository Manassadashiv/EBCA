import os
import sys
import torch
import torch.nn as nn
import numpy as np
import cv2
import random

# Import model definition from train_vision.py
sys.path.append(BASE_DIR)
from train_vision import CarlVisionNet, CarlVisionDataset
import os as _os
_FILE_DIR = _os.path.dirname(_os.path.abspath(__file__))
BASE_DIR = _os.path.dirname(_FILE_DIR)


def verify_predictions():
    device = torch.device("cpu")
    model = CarlVisionNet()
    
    weights_path = os.path.join(BASE_DIR, "memory", "carl_vision.pt")
    if not os.path.exists(weights_path):
        print(f"Error: Trained model weights not found at {weights_path}!")
        return
        
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.eval()
    
    dataset_dir = os.path.join(BASE_DIR, "memory", "vision_dataset")
    dataset = CarlVisionDataset(dataset_dir)
    
    if len(dataset) == 0:
        print("Error: Vision dataset is empty!")
        return
        
    # Pick 4 random indices to showcase
    indices = random.sample(range(len(dataset)), min(4, len(dataset)))
    
    grid_imgs = []
    class_names = ["FOOD", "OBSTACLE", "PREDATOR", "BACKGROUND"]
    
    for idx in indices:
        img_tensor, class_id, bbox = dataset[idx]
        
        # Run inference
        with torch.no_grad():
            # Add batch dimension
            cls_out, bbox_out = model(img_tensor.unsqueeze(0))
            
            # Get predicted class (argmax)
            probs = torch.softmax(cls_out, dim=1).numpy()[0]
            pred_class = np.argmax(probs)
            pred_conf = probs[pred_class]
            
            # Get predicted bbox
            pred_bbox = bbox_out.squeeze(0).numpy() # [x_c, y_c, w, h]
            
        # Convert tensor back to BGR image for drawing
        img = (img_tensor.permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        W, H = img_bgr.shape[1], img_bgr.shape[0]
        
        # Draw ground truth (green box) if not background
        if class_id != 3:
            gt_xc, gt_yc, gt_w, gt_h = bbox.numpy()
            gt_u1 = int((gt_xc - gt_w/2) * W)
            gt_v1 = int((gt_yc - gt_h/2) * H)
            gt_u2 = int((gt_xc + gt_w/2) * W)
            gt_v2 = int((gt_yc + gt_h/2) * H)
            cv2.rectangle(img_bgr, (gt_u1, gt_v1), (gt_u2, gt_v2), (0, 255, 0), 1) # Green line
            cv2.putText(img_bgr, f"GT: {class_names[class_id]}", (gt_u1, max(12, gt_v1 - 2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
                        
        # Draw prediction (cyan/blue box) if not background
        if pred_class != 3:
            pr_xc, pr_yc, pr_w, pr_h = pred_bbox
            pr_u1 = int((pr_xc - pr_w/2) * W)
            pr_v1 = int((pr_yc - pr_h/2) * H)
            pr_u2 = int((pr_xc + pr_w/2) * W)
            pr_v2 = int((pr_yc + pr_h/2) * H)
            cv2.rectangle(img_bgr, (pr_u1, pr_v1), (pr_u2, pr_v2), (255, 255, 0), 1) # Cyan line
            cv2.putText(img_bgr, f"PR: {class_names[pred_class]} ({pred_conf:.2f})", (pr_u1, max(24, pr_v2 + 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)
        else:
            cv2.putText(img_bgr, "PR: BG", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
                        
        grid_imgs.append(img_bgr)
        
    # Combine the 4 images into a 2x2 grid
    top_row = np.hstack((grid_imgs[0], grid_imgs[1]))
    bot_row = np.hstack((grid_imgs[2], grid_imgs[3]))
    grid_all = np.vstack((top_row, bot_row))
    
    output_path = os.path.join(BASE_DIR, "vision_verification_result.png")
    cv2.imwrite(output_path, grid_all)
    print(f"[VERIFY] Successfully saved predictions grid to {output_path}!")

if __name__ == '__main__':
    verify_predictions()
