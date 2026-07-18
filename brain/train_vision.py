import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import cv2

class CarlVisionDataset(Dataset):
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
        
        # Default label (Background)
        class_id = 3
        bbox = torch.tensor([0.5, 0.5, 0.0, 0.0], dtype=torch.float32)
        
        if os.path.exists(label_path) and os.path.getsize(label_path) > 0:
            with open(label_path, "r") as lf:
                line = lf.readline().strip()
                if line:
                    parts = line.split()
                    class_id = int(parts[0])
                    bbox = torch.tensor([float(x) for x in parts[1:]], dtype=torch.float32)
                    
        return img_tensor, class_id, bbox

class CarlVisionNet(nn.Module):
    def __init__(self):
        super(CarlVisionNet, self).__init__()
        # Input shape: (3, 120, 160)
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # shape: (16, 60, 80)
            
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # shape: (32, 30, 40)
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # shape: (64, 15, 20)
        )
        
        self.flat_dim = 64 * 15 * 20 # 19200
        
        # Classifier Head: 4 classes
        self.classifier = nn.Sequential(
            nn.Linear(self.flat_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 4)
        )
        
        # Bounding Box Head: 4 values [x_c, y_c, w, h] normalized [0, 1]
        self.bbox_regressor = nn.Sequential(
            nn.Linear(self.flat_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 4),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        cls_out = self.classifier(x)
        bbox_out = self.bbox_regressor(x)
        return cls_out, bbox_out

def train_model():
    dataset_dir = "D:/ebca/memory/vision_dataset"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[VISION-TRAIN] Using training device: {device}")
    
    # Initialize DataLoader
    dataset = CarlVisionDataset(dataset_dir)
    train_loader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=0)
    
    # Initialize Model, Loss, Optimizer
    model = CarlVisionNet().to(device)
    cls_criterion = nn.CrossEntropyLoss()
    bbox_criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    epochs = 15
    print(f"[VISION-TRAIN] Starting training for {epochs} epochs...")
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        running_cls_loss = 0.0
        running_bbox_loss = 0.0
        
        for images, classes, bboxes in train_loader:
            images = images.to(device)
            classes = classes.to(device)
            bboxes = bboxes.to(device)
            
            optimizer.zero_grad()
            
            cls_out, bbox_out = model(images)
            
            # Classification Loss
            loss_cls = cls_criterion(cls_out, classes)
            
            # Bounding Box Loss (only count for class 0, 1, 2)
            # Mask out background loss to prevent zero-bbox bias during active targets
            active_mask = (classes != 3).float().unsqueeze(1)
            loss_bbox = bbox_criterion(bbox_out * active_mask, bboxes * active_mask)
            
            # Combine losses
            total_loss = loss_cls + 2.0 * loss_bbox
            
            total_loss.backward()
            optimizer.step()
            
            running_loss += total_loss.item()
            running_cls_loss += loss_cls.item()
            running_bbox_loss += loss_bbox.item()
            
        epoch_loss = running_loss / len(train_loader)
        epoch_cls = running_cls_loss / len(train_loader)
        epoch_bbox = running_bbox_loss / len(train_loader)
        
        print(f"Epoch {epoch+1:02d}/{epochs:02d} - Loss: {epoch_loss:.4f} (Cls: {epoch_cls:.4f}, Bbox: {epoch_bbox:.4f})")
        
    # Save model weights
    save_path = "D:/ebca/memory/carl_vision.pt"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(model.state_dict(), save_path)
    print(f"[VISION-TRAIN] Successfully saved model to {save_path}!")

if __name__ == '__main__':
    train_model()
