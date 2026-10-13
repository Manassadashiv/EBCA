import sys
from pathlib import Path
repo_root = Path('.').resolve()
sys.path.insert(0, str(repo_root))

from tests.test_stage3_4R3_certification import build_50_matched_configurations, execute_episode
from brain.carl_stage1_hal import CarlStage1HAL
import numpy as np, math, torch

if __name__ == "__main__":
    configs = build_50_matched_configurations()
    hal1 = CarlStage1HAL(xml_path=configs[0]["xml_path"])
    hal2 = CarlStage1HAL(xml_path=configs[20]["xml_path"])

    escapes = 0
    collisions = 0
    timeouts = 0
    g2_count = 0
    all_latencies = []

    print("--- RUNNING PURE PRODUCTION ENGINE BENCHMARK (N=50) ---")
    for cfg_id, cfg in enumerate(configs):
        hal = hal2 if cfg["env_id"] == 2 else hal1
        res = execute_episode("ARM-A", cfg, hal)
        if res["escaped"]:
            escapes += 1
            tag = "ESCAPE"
        elif res["had_collision"]:
            collisions += 1
            tag = "COLLISION"
        else:
            timeouts += 1
            tag = "TIMEOUT"
        if res["gate2_emergent_complete"]:
            g2_count += 1
        all_latencies.extend(res["latencies"])
        print(f"[{cfg_id:2d}/50] Cfg {cfg['config_id']:2d} (Env{cfg['env_id']}): {tag:9s} ticks={res['ticks']} | G2={res['gate2_emergent_complete']}")

    mean_lat = float(np.mean(all_latencies)) if all_latencies else 0.0
    p95_lat = float(np.percentile(all_latencies, 95)) if all_latencies else 0.0

    print(f"\n==========================================")
    print(f"PURE PRODUCTION 50-CONFIG CERTIFICATION AUDIT:")
    print(f"  Gate 1 - Escapes:    {escapes}/50 ({escapes/50*100:.1f}%) [Target: >= 40 (80.0%)] -> {'[PASS]' if escapes >= 40 else '[FAIL]'}")
    print(f"  Gate 1 - Collisions: {collisions}/50 ({collisions/50*100:.1f}%) [Target: <= 5 (10.0%)] -> {'[PASS]' if collisions <= 5 else '[FAIL]'}")
    print(f"  Gate 1 - Timeouts:   {timeouts}/50 ({timeouts/50*100:.1f}%)")
    print(f"  Gate 2 - Maneuvers:  {g2_count}/50 ({g2_count/50*100:.1f}%) [Target: >= 38 (75.0%)] -> {'[PASS]' if g2_count >= 38 else '[FAIL]'}")
    print(f"  Gate 4 - Mean Lat:   {mean_lat:.2f} ms [Target: <= 20.0 ms] -> {'[PASS]' if mean_lat <= 20.0 else '[FAIL]'}")
    print(f"  Gate 4 - p95 Lat:    {p95_lat:.2f} ms [Target: <= 45.0 ms] -> {'[PASS]' if p95_lat <= 45.0 else '[FAIL]'}")
    print(f"==========================================")

