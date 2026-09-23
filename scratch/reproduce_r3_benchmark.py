"""
scratch/reproduce_r3_benchmark.py — Complete Forensic Reproduction Script for Stage 2.1B-R.3
Classification: Scientific Reproduction Script

Executes:
1. Forensic Reproduction of Stage 2.1B-R.1 Task 3 baseline.
2. Preflight Seed Independence Check (verifying distinct freejoint spatial_identity poses).
3. Candidate Showdown (Candidate A: Coprime Multi-Scale Grid, Candidate B: Integer Winding Control, Candidate C: Calibrated Grounded Speed).
4. Causal Ablations on Unseen Seeds (No Multi-Scale, Shuffled Spatial, Shuffled Heading).
5. Compares against immutable acceptance gate (<= 0.22m).
"""

import os
import sys
import json
import time

BASE_DIR = "d:/ebca"
sys.path.insert(0, BASE_DIR)

from brain.test_stage2_1b_r3_global_space import main as run_benchmark

if __name__ == "__main__":
    print("================================================================================")
    print("CARL STAGE 2.1B-R.3: MASTER FORENSIC REPRODUCTION SCRIPT")
    print("================================================================================")
    t0 = time.time()
    run_benchmark()
    elapsed = time.time() - t0
    print(f"\n[REPRODUCTION COMPLETE] Total execution time: {elapsed:.2f} seconds.")
