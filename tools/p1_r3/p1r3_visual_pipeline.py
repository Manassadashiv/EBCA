"""
tools/p1_r3/p1r3_visual_pipeline.py — Video Recorder & Real-Time HUD Overlay for P1-R3

Renders 1280x720 30 FPS MP4 videos using OpenCV with tracking camera (distance 2.9m, elevation -30 deg, azimuth 140 deg)
and comprehensive scientific HUD overlay.
"""

import os
import cv2
import numpy as np
from typing import Dict, Any, Optional


class CarlP1R3VisualPipeline:
    """
    HD 720p 30 FPS Video Recorder with Scientific Telemetry HUD Overlay.
    """
    def __init__(self, output_path: str, fps: int = 30, width: int = 1280, height: int = 720):
        self.output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        self.fps = fps
        self.width = width
        self.height = height
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.output_path, fourcc, self.fps, (self.width, self.height))
        self.frame_count = 0

    def add_frame(self, rgb_frame: np.ndarray, telemetry: Dict[str, Any]):
        """
        Draws HUD overlay onto the rendered frame and writes to the MP4 file.
        """
        bgr = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
        
        # 1. Semi-transparent Top Header Bar
        overlay = bgr.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, 95), (15, 18, 24), -1)
        cv2.addWeighted(overlay, 0.85, bgr, 0.15, 0, bgr)
        
        # 2. Header Text
        title = f"CARL-DX P1-R3: {telemetry.get('condition', 'FULL')} | SEED {telemetry.get('seed', 42)} | EPISODE {telemetry.get('episode', 1)}"
        cv2.putText(bgr, title, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 240, 255), 2, cv2.LINE_AA)
        
        # Telemetry columns
        tick = telemetry.get('tick', 0)
        t_sec = tick * 0.0333
        action = telemetry.get('best_action', 'NONE')
        seq = telemetry.get('best_sequence', 'NONE')
        px = telemetry.get('pos_x', 0.0)
        py = telemetry.get('pos_y', 0.0)
        route = telemetry.get('route_choice', 'UNDECIDED')
        
        line1 = f"TICK: {tick:04d} ({t_sec:5.2f}s) | POS: ({px:+.2f}, {py:+.2f}) | ROUTE: {route} | ACTION: {action}"
        cv2.putText(bgr, line1, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)
        
        dist_food = telemetry.get('dist_food', 0.0)
        pred_err = telemetry.get('prediction_error', 0.0)
        mem_w = telemetry.get('memory_writes', 0)
        mem_r = telemetry.get('memory_retrievals', 0)
        mem_sim = telemetry.get('memory_similarity', 0.0)
        efe = telemetry.get('best_efe', 0.0)
        col = telemetry.get('collision_occurred', False)
        
        col_color = (0, 0, 255) if col else (0, 255, 0)
        col_str = "COLLISION!" if col else "CLEAR"
        
        line2 = f"DIST: {dist_food:4.2f}m | PE: {pred_err:4.2f} | EFE: {efe:6.1f} | MEM W:{mem_w:3d} R:{mem_r:4d} SIM:{mem_sim:4.2f} | STATUS: "
        cv2.putText(bgr, line2, (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 200, 200), 1, cv2.LINE_AA)
        
        # Draw status tag
        cv2.putText(bgr, col_str, (880, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.52, col_color, 2, cv2.LINE_AA)
        
        # 3. Bottom HUD watermark
        cv2.putText(bgr, "CARL-DX PHASE 1-R3 MEMORY-CAUSALITY BENCHMARK | RIGID SOLID PHYSICS", 
                    (20, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 140, 160), 1, cv2.LINE_AA)
        
        self.writer.write(bgr)
        self.frame_count += 1

    def close(self):
        """Finalizes and closes the video file."""
        if self.writer is not None:
            self.writer.release()
            self.writer = None
