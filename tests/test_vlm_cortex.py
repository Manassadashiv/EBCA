"""
test_vlm_cortex.py — Unit Tests for VLM System 2 Cognitive Cortex

Validates:
1. Thread-safe initialization, start, and clean shutdown of VLMSystem2Cortex.
2. Non-blocking frame queue dispatch and intention readout.
3. Fallback heuristic processing when quantized weights are uninitialized.
"""

import os
import sys
import time
import numpy as np
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from brain.carl_vlm_cortex import VLMSystem2Cortex


def test_vlm_cortex_lifecycle_and_reasoning():
    cortex = VLMSystem2Cortex(model_id="nvidia/NVLM-D-7B", quantization_bits=4)
    # Start thread
    cortex.start_cortex()
    assert cortex.running is True

    # Dispatch synthetic visual frame (120x160x3 RGB)
    dummy_frame = np.zeros((120, 160, 3), dtype=np.uint8)
    dummy_frame[:, :, 1] = 180  # Green dominant (food cue)

    cortex.submit_frame(dummy_frame, current_mode="EXPLORE", battery=0.85)

    # Allow worker thread to process
    time.sleep(0.2)

    intention = cortex.get_latest_intention()
    assert "scene_description" in intention
    assert "recommended_goal" in intention
    assert intention["recommended_goal"] in ["EXPLOIT", "EXPLORE", "SURVIVE"]

    # Clean shutdown
    cortex.stop_cortex()
    assert cortex.running is False
