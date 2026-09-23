"""
tools/p1_r2/p1r2_visual_pipeline.py — HD 720p 30 FPS Video Recorder & Visual HUD Telemetry for P1-R2

Renders high-fidelity 1280x720 30 FPS MP4 video with real-time overlay showing:
- Tick, Time (s), Condition, Seed, Episode
- Selected Multi-Step Sequence [a1 -> a2]
- Predicted EFE & Prediction Error
- Position & Distance to Food Target
- HDC Memory Writes / Retrievals / Episodes
- Target Acquisition Status
"""

import os
import cv2
import numpy as np
from typing import Dict, Any, Optional


class P1R2VisualPipeline:
    """
    Renders HD 720p 30 FPS MP4 videos with real-time cognitive HUD telemetry.
    """
    def __init__(self, output_filepath: str, width: int = 1280, height: int = 720, fps: int = 30):
        self.output_filepath = os.path.abspath(output_filepath)
        os.makedirs(os.path.dirname(self.output_filepath), exist_ok=True)
        self.width = width
        self.height = height
        self.fps = fps
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.output_filepath, fourcc, fps, (width, height))
        self.frame_count = 0

    def add_frame(
        self,
        rgb_frame: np.ndarray,
        tick: int,
        sim_time: float,
        condition: str,
        seed: int,
        episode: int,
        action: str,
        sequence: str,
        efe: float,
        dist_food: float,
        pred_error: float,
        memory_episodes: int,
        memory_writes: int,
        memory_retrievals: int,
        acquired: bool
    ):
        """
        Draws semi-transparent HUD overlay on top of 1280x720 frame and writes to MP4.
        """
        # Convert RGB to BGR for OpenCV
        bgr = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
        overlay = bgr.copy()
        
        # 1. Top HUD Banner (Dark translucent glassmorphism)
        cv2.rectangle(overlay, (20, 15), (1260, 115), (15, 20, 25), -1)
        # 2. Bottom Right Telemetry Box
        cv2.rectangle(overlay, (820, 560), (1260, 700), (15, 20, 25), -1)
        
        # Alpha blend overlay
        cv2.addWeighted(overlay, 0.72, bgr, 0.28, 0, bgr)
        
        # Top HUD Border
        cv2.rectangle(bgr, (20, 15), (1260, 115), (0, 220, 255), 1)
        cv2.rectangle(bgr, (820, 560), (1260, 700), (0, 220, 255), 1)
        
        # Title & Episode Info
        cv2.putText(bgr, f"CARL-DX P1-R2 | COND: {condition} | SEED: {seed} | EPISODE: {episode}/5", (35, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.70, (255, 255, 255), 2)
        cv2.putText(bgr, f"TIME: {sim_time:.2f}s (TICK {tick:03d}) | STATUS: {'[ACQUIRED]' if acquired else '[SEARCHING]'}", (35, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 255, 120) if acquired else (200, 200, 200), 2)
        cv2.putText(bgr, f"SEQUENCE: [{sequence}]  |  ACTION: {action}  |  EFE: {efe:.1f}", (35, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 200, 50), 1)
        
        # Bottom Right Telemetry
        cv2.putText(bgr, f"TARGET DIST: {dist_food:.2f} m", (835, 590),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 220, 255), 2)
        cv2.putText(bgr, f"PRED ERROR:  {pred_error:.3f}", (835, 620),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(bgr, f"MEMORY WRITES: {memory_writes} | RETRIEVALS: {memory_retrievals}", (835, 650),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (200, 200, 200), 1)
        cv2.putText(bgr, f"EPISODES IN MEMORY: {memory_episodes}", (835, 680),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (120, 255, 120), 1)
                    
        # Big Acquisition Banner
        if acquired:
            cv2.rectangle(bgr, (400, 320), (880, 400), (0, 180, 60), -1)
            cv2.rectangle(bgr, (400, 320), (880, 400), (255, 255, 255), 2)
            cv2.putText(bgr, "GOAL BEACON ACQUIRED!", (430, 370),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
                        
        self.writer.write(bgr)
        self.frame_count += 1

    def close(self):
        """Finalizes and releases video writer."""
        if self.writer is not None:
            self.writer.release()
            self.writer = None
