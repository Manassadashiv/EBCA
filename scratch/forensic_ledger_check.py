import sys
import os
sys.path.insert(0, 'd:/ebca')

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage1_organism import CarlStage1Organism
import numpy as np

seeds = [42, 101, 202, 303, 404]
raw_ledger = {}

for s in seeds:
    hal = CarlStage1HAL(open_space=True)
    hal.reset()
    hal.set_floor_friction(3.0)
    org = CarlStage1Organism(hal=hal, seed=s)
    org.discovered_topology = {'discovered_drive_channels': [0, 1]}
    org.run_session(60)
    org.learn_predictive_readout(reg_lambda=10.0)

    hal.reset()
    hal.set_floor_friction(3.0)
    org.control_mode = 'goal_seeking'
    org.set_sensory_goal(channel=7, mode='maximize')

    p1_ticks = []
    for t in range(25):
        rec = org.step()
        det = org.detect_traction_discrepancy(slip_threshold=0.52)
        p1_ticks.append(det)

    hal.set_floor_friction(0.005)
    p2_ticks = []
    for t in range(35):
        rec = org.step()
        det = org.detect_traction_discrepancy(slip_threshold=0.52)
        p2_ticks.append(det)

    hal.set_floor_friction(3.0)
    p3_ticks = []
    for t in range(25):
        rec = org.step()
        det = org.detect_traction_discrepancy(slip_threshold=0.52)
        p3_ticks.append(det)

    p1_fp = sum(1 for x in p1_ticks if x)
    p2_det = sum(1 for x in p2_ticks if x)
    p2_steady = sum(1 for x in p2_ticks[5:] if x)
    p3_rec = sum(1 for x in p3_ticks if x)

    raw_ledger[s] = {
        'p1_fp_count': p1_fp,
        'p1_fp_rate': p1_fp / 25.0,
        'p2_det_count': p2_det,
        'p2_det_rate': p2_det / 35.0,
        'p2_steady_count': p2_steady,
        'p2_steady_rate': p2_steady / 30.0,
        'p3_rec_count': p3_rec,
        'p3_rec_rate': p3_rec / 25.0,
        'pass_dry_fp': (p1_fp / 25.0 <= 0.10),
        'pass_ice_det': (p2_det / 35.0 >= 0.70),
        'pass_recovery': (p3_rec / 25.0 <= 0.20)
    }

for s, res in raw_ledger.items():
    print(f"Seed {s}: DRY FP={res['p1_fp_count']}/25 ({res['p1_fp_rate']*100:.1f}%), ICE={res['p2_det_count']}/35 ({res['p2_det_rate']*100:.1f}%), REC={res['p3_rec_count']}/25 ({res['p3_rec_rate']*100:.1f}%)")

total_dry_fp = sum(res['p1_fp_count'] for res in raw_ledger.values())
total_ice_det = sum(res['p2_det_count'] for res in raw_ledger.values())
total_ice_steady = sum(res['p2_steady_count'] for res in raw_ledger.values())
total_rec = sum(res['p3_rec_count'] for res in raw_ledger.values())

print('--- RAW SUM TOTALS (EXACT MATH) ---')
print(f"Total Dry False Positives: {total_dry_fp} / 125 ({total_dry_fp / 125.0 * 100:.2f}%)")
print(f"Total Ice Detections: {total_ice_det} / 175 ({total_ice_det / 175.0 * 100:.2f}%)")
print(f"Total Steady Ice Detections: {total_ice_steady} / 150 ({total_ice_steady / 150.0 * 100:.2f}%)")
print(f"Total Recovery Flags: {total_rec} / 125 ({total_rec / 125.0 * 100:.2f}%)")
