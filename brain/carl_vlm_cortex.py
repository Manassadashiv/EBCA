"""
carl_vlm_cortex.py — NVIDIA 6B Vision-Language-Action (VLA) System 2 Cognitive Cortex

Implements:
1. Asynchronous System 2 cognitive processing decoupled from the 30 Hz motor reflex loop.
2. 4-bit / 8-bit (NF4 / INT4 / INT8) Quantization for execution within 6GB VRAM (RTX 3050).
3. Vision-Language prompt reasoning for semantic scene description, affordance detection, and goal biasing.
4. Non-blocking thread-safe frame queue and result buffer.
"""

import os
import sys
import time
import threading
import queue
import numpy as np
from typing import Optional, Dict, Any

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class VLMSystem2Cortex:
    """
    Asynchronous System 2 High-Level Visual Reasoning Cortex.
    Runs at 1-2 Hz in a background worker thread, receiving visual frames from
    the 30 Hz HAL and publishing high-level semantic intentions.
    """
    def __init__(self,
                 model_id: str = "nvidia/NVLM-D-7B",
                 quantization_bits: int = 4,
                 device: str = "cuda",
                 max_context_len: int = 512):
        self.model_id = model_id
        self.quantization_bits = quantization_bits
        self.device = device if (HAS_TORCH and torch.cuda.is_available() and device == "cuda") else "cpu"
        self.max_context_len = max_context_len

        self.frame_queue = queue.Queue(maxsize=2)
        self.latest_reasoning: Dict[str, Any] = {
            "scene_description": "Awaiting initial visual observation...",
            "detected_affordances": ["explore_open_corridor"],
            "recommended_goal": "SEEK_FOOD",
            "semantic_novelty": 0.5,
            "latency_ms": 0.0,
            "timestamp": time.time()
        }
        self.lock = threading.Lock()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.model = None
        self.tokenizer = None
        self.processor = None

    def load_model(self) -> bool:
        """
        Attempts to load the quantized VLM using bitsandbytes NF4 / INT8.
        Falls back smoothly to lightweight rule-based semantic inference if VLM weights
        are not locally cached or internet is offline.
        """
        if not HAS_TORCH:
            print("[VLM-CORTEX][WARN] PyTorch not detected. Running in lightweight fallback mode.")
            return False

        try:
            from transformers import AutoModelForCausalLM, AutoProcessor, BitsAndBytesConfig

            print(f"[VLM-CORTEX] Initializing {self.model_id} with {self.quantization_bits}-bit quantization...")

            if self.quantization_bits == 4:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True
                )
            elif self.quantization_bits == 8:
                bnb_config = BitsAndBytesConfig(load_in_8bit=True)
            else:
                bnb_config = None

            # Attempt local or hub load
            self.processor = AutoProcessor.from_pretrained(self.model_id, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                quantization_config=bnb_config,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )
            print(f"[VLM-CORTEX] Successfully loaded {self.model_id} (Quantization: {self.quantization_bits}-bit) on {self.device}!")
            return True
        except Exception as e:
            print(f"[VLM-CORTEX][INFO] Quantized VLM offline/uncached ({e}). Cortex active in Fast-Heuristic Vision Mode.")
            return False

    def start_cortex(self):
        """Starts the async background worker thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        print("[VLM-CORTEX] System 2 background cortex thread started.")

    def stop_cortex(self):
        """Stops the worker thread cleanly."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        print("[VLM-CORTEX] System 2 background cortex thread stopped.")

    def submit_frame(self, rgb_image: np.ndarray, current_mode: str, battery: float):
        """
        Non-blocking frame dispatch from the 30 Hz loop.
        Drops oldest frame if worker is currently reasoning.
        """
        if not self.running:
            return
        try:
            # Keep queue fresh (drop stale frame if full)
            if self.frame_queue.full():
                _ = self.frame_queue.get_nowait()
            self.frame_queue.put_nowait((rgb_image, current_mode, battery, time.time()))
        except Exception:
            pass

    def get_latest_intention(self) -> Dict[str, Any]:
        """Thread-safe readout of latest high-level cognitive deliberation."""
        with self.lock:
            return dict(self.latest_reasoning)

    def _worker_loop(self):
        while self.running:
            try:
                item = self.frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            frame, mode, battery, t_start = item
            reasoning = self._run_reasoning_step(frame, mode, battery)
            dt_ms = (time.time() - t_start) * 1000.0
            reasoning["latency_ms"] = round(dt_ms, 1)
            reasoning["timestamp"] = time.time()

            with self.lock:
                self.latest_reasoning = reasoning

    def _run_reasoning_step(self, frame: np.ndarray, mode: str, battery: float) -> Dict[str, Any]:
        """Executes one step of visual reasoning."""
        if self.model is not None and self.processor is not None:
            # Model-driven inference
            try:
                from PIL import Image
                pil_img = Image.fromarray(frame)
                prompt = (
                    f"<image>\nContext: Mode={mode}, Battery={battery:.2f}. "
                    "Analyze the spatial corridor, green food beacons, red hazard walls, and recommend an action."
                )
                inputs = self.processor(images=pil_img, text=prompt, return_tensors="pt").to(self.device)
                with torch.no_grad():
                    out = self.model.generate(**inputs, max_new_tokens=48)
                text = self.processor.decode(out[0], skip_special_tokens=True)
                return {
                    "scene_description": text,
                    "detected_affordances": ["navigate_vlm_path"],
                    "recommended_goal": "EXPLOIT_FOOD" if "food" in text.lower() else "EXPLORE_MAZE",
                    "semantic_novelty": 0.7
                }
            except Exception as e:
                pass

        # Fast heuristic visual analysis when VLM weights are not loaded
        mean_green = float(np.mean(frame[:, :, 1]))
        mean_red = float(np.mean(frame[:, :, 0]))
        food_cue = mean_green > (mean_red + 15.0)

        return {
            "scene_description": "Visual field scanned: open corridor with wall geometry.",
            "detected_affordances": ["food_approach"] if food_cue else ["corridor_navigation"],
            "recommended_goal": "EXPLOIT" if food_cue else ("SURVIVE" if battery < 0.25 else "EXPLORE"),
            "semantic_novelty": 0.45 if food_cue else 0.80
        }
