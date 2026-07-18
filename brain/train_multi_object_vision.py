import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import cv2
import functools
import torchvision
from torchvision.models.detection.ssdlite import SSDLite320_MobileNet_V3_Large_Weights, SSDLiteClassificationHead

class CarlMultiObjectDataset(Dataset):
    def __init__(self, dataset_dir, W=160, H=120):
        self.dataset_dir = dataset_dir
        self.images_dir = os.path.join(dataset_dir, "images")
        self.labels_dir = os.path.join(dataset_dir, "labels")
        self.W = W
        self.H = H
        
        self.filenames = [f[:-4] for f in os.listdir(self.images_dir) if f.endswith(".jpg")]
        
    def __len__(self):
        return len(self.filenames)
        
    def __getitem__(self, idx):
        name = self.filenames[idx]
        img_path = os.path.join(self.images_dir, name + ".jpg")
        label_path = os.path.join(self.labels_dir, name + ".txt")
        
        # Load image
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Normalize and transpose (H, W, C) -> (C, H, W)
        img_tensor = torch.tensor(img, dtype=torch.float32).permute(2, 0, 1) / 255.0
        
        boxes_list = []
        labels_list = []
        
        if os.path.exists(label_path) and os.path.getsize(label_path) > 0:
            with open(label_path, "r") as lf:
                for line in lf:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        class_id = int(parts[0])
                        xc, yc, w, h = [float(x) for x in parts[1:]]
                        
                        # Convert normalized YOLO center coords to absolute xmin, ymin, xmax, ymax
                        xmin = (xc - w/2.0) * self.W
                        ymin = (yc - h/2.0) * self.H
                        xmax = (xc + w/2.0) * self.W
                        ymax = (yc + h/2.0) * self.H
                        
                        # Ensure bounding boxes are valid
                        xmin = max(0.0, min(self.W - 1.0, xmin))
                        xmax = max(xmin + 1.0, min(self.W, xmax))
                        ymin = max(0.0, min(self.H - 1.0, ymin))
                        ymax = max(ymin + 1.0, min(self.H, ymax))
                        
                        boxes_list.append([xmin, ymin, xmax, ymax])
                        
                        # torchvision detection is 1-indexed: 0 is background, 1=Food, 2=Obstacle, 3=Predator
                        labels_list.append(class_id + 1)
                        
        if len(boxes_list) > 0:
            boxes = torch.tensor(boxes_list, dtype=torch.float32)
            labels = torch.tensor(labels_list, dtype=torch.int64)
            area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        else:
            boxes = torch.zeros((0, 4), dtype=torch.float32)
            labels = torch.zeros((0,), dtype=torch.int64)
            area = torch.zeros((0,), dtype=torch.float32)
            
        target = {}
        target["boxes"] = boxes
        target["labels"] = labels
        target["image_id"] = torch.tensor([idx])
        target["area"] = area
        target["iscrowd"] = torch.zeros((len(boxes),), dtype=torch.int64)
        
        return img_tensor, target

def collate_fn(batch):
    return tuple(zip(*batch))

def get_ssdlite_model():
    # Load pretrained SSD-Lite MobileNetV3
    model = torchvision.models.detection.ssdlite320_mobilenet_v3_large(
        weights=SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
    )
    
    # Extract structural config to build our custom head
    in_channels = [layer[0][0].in_channels for layer in model.head.classification_head.module_list]
    num_anchors = model.anchor_generator.num_anchors_per_location()
    
    # Define norm layer
    norm_layer = functools.partial(nn.BatchNorm2d, eps=0.001, momentum=0.03)
    
    # Swap out the classification head (4 classes: 0=BG, 1=Food, 2=Obstacle, 3=Predator)
    model.head.classification_head = SSDLiteClassificationHead(
        in_channels=in_channels,
        num_anchors=num_anchors,
        num_classes=4,
        norm_layer=norm_layer
    )
    return model

def train_model():
    dataset_dir = "D:/ebca/memory/multi_object_dataset"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[MULTI-VISION-TRAIN] Using training device: {device}")
    
    # Load Dataset & DataLoader
    dataset = CarlMultiObjectDataset(dataset_dir)
    train_loader = DataLoader(dataset, batch_size=16, shuffle=True, num_workers=0, collate_fn=collate_fn)
    
    # Initialize Model, Optimizer
    model = get_ssdlite_model().to(device)
    
    # Fine-tune all parameters
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)
    
    epochs = 30
    print(f"[MULTI-VISION-TRAIN] Starting training for {epochs} epochs on SSD-Lite MobileNetV3...")
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        running_class_loss = 0.0
        running_box_loss = 0.0
        
        for images, targets in train_loader:
            # Move list of tensors to device
            images = [img.to(device) for img in images]
            
            # Move list of dicts to device
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            
            optimizer.zero_grad()
            
            # In train mode, torchvision SSD model returns dictionary of losses
            loss_dict = model(images, targets)
            
            total_loss = sum(loss for loss in loss_dict.values())
            
            total_loss.backward()
            optimizer.step()
            
            running_loss += total_loss.item()
            running_class_loss += loss_dict['classification'].item()
            running_box_loss += loss_dict['bbox_regression'].item()
            
        scheduler.step()
        epoch_loss = running_loss / len(train_loader)
        epoch_cls = running_class_loss / len(train_loader)
        epoch_box = running_box_loss / len(train_loader)
        
        print(f"Epoch {epoch+1:02d}/{epochs:02d} - Loss: {epoch_loss:.4f} (Cls: {epoch_cls:.4f}, Bbox: {epoch_box:.4f})")
        
    save_path = "D:/ebca/memory/carl_multi_object_vision.pt"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(model.state_dict(), save_path)
    print(f"[MULTI-VISION-TRAIN] Successfully saved model to {save_path}!")

if __name__ == '__main__':
    train_model()
