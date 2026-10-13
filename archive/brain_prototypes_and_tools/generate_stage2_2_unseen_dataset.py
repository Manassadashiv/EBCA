"""
brain/generate_stage2_2_unseen_dataset.py — Step 8 Unseen Test Dataset Harvester
Classification: [POST-FREEZE TEST GENERATION] Single Official Primary Unseen Partition

Generates 25 episodes across held-out seeds [303, 404, 505, 606, 707] (5 episodes per seed).
Computes and locks cryptographic SHA-256 manifest.
Strict Invariant: Executed strictly post-freeze!
"""

import sys
import json
import hashlib
from pathlib import Path
import numpy as np

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage2_2_data_collector import harvest_dataset_partition


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def generate_primary_unseen_test():
    print("\n" + "=" * 70)
    print("STEP 8: GENERATING OFFICIAL PRIMARY UNSEEN TEST PARTITION (POST-FREEZE)")
    print("=" * 70)

    dataset_dir = Path("evidence/stage2_2/datasets")
    unseen_path = dataset_dir / "unseen_test.npz"

    # Seeds [303, 404, 505, 606, 707] - 5 episodes per seed = 25 episodes
    seeds = [303, 404, 505, 606, 707]
    episodes_per_seed = 5

    harvest_dataset_partition(
        seeds=seeds,
        episodes_per_seed=episodes_per_seed,
        partition_name="PRIMARY_UNSEEN_TEST",
        output_path=unseen_path
    )

    file_hash = compute_sha256(unseen_path)
    manifest = {
        "partition": "PRIMARY_UNSEEN_TEST",
        "seeds": seeds,
        "episodes_per_seed": episodes_per_seed,
        "total_episodes": len(seeds) * episodes_per_seed,
        "file_path": str(unseen_path),
        "sha256": file_hash
    }

    manifest_path = dataset_dir / "unseen_test_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nPRIMARY UNSEEN TEST GENERATED AND LOCKED!")
    print(f"File: {unseen_path}")
    print(f"SHA-256: {file_hash}")
    print(f"Manifest: {manifest_path}")
    print("=" * 70)


if __name__ == "__main__":
    generate_primary_unseen_test()
