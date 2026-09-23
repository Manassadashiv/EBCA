import sys, math, numpy as np, torch
from pathlib import Path
repo_root = Path('d:/ebca')
sys.path.insert(0, str(repo_root))

from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

configs = build_50_matched_configurations()
cfg = configs[20]
ctrl = CARLActiveInferenceEngine(grid_path=cfg['grid_path'], w_info=1.0)
ctrl.initialize_pose(0.50, 0.0, 0.0)

# Simulate being at x=0.85, y=-0.70 in Env 2
macro_res = ctrl._compute_macro_frontier(0.85, -0.70)
if macro_res is not None:
    fx, fy, cur_d, dist_field = macro_res
    print(f"Frontier target: fx={fx:.3f}, fy={fy:.3f}, cur_d={cur_d:.3f}")
    rc_ix = int(np.clip((0.85 + ctrl.half_size) / ctrl.resolution, 0, ctrl.grid_size - 1))
    rc_iy = int(np.clip((-0.70 + ctrl.half_size) / ctrl.resolution, 0, ctrl.grid_size - 1))
    print(f"Robot cell: ix={rc_ix}, iy={rc_iy}")
    print(f"Distances: center={dist_field[rc_iy, rc_ix]:.3f}")
    print(f"  North (iy+1) = {dist_field[rc_iy+1, rc_ix]:.3f}")
    print(f"  South (iy-1) = {dist_field[rc_iy-1, rc_ix]:.3f}")
    print(f"  East  (ix+1) = {dist_field[rc_iy, rc_ix+1]:.3f}")
    print(f"  West  (ix-1) = {dist_field[rc_iy, rc_ix-1]:.3f}")
    de, dw = dist_field[rc_iy, rc_ix+1], dist_field[rc_iy, rc_ix-1]
    dn, ds = dist_field[rc_iy+1, rc_ix], dist_field[rc_iy-1, rc_ix]
    gx = (de - dw) / (2.0 * ctrl.resolution)
    gy = (dn - ds) / (2.0 * ctrl.resolution)
    th_geo = math.atan2(-gy, -gx)
    print(f"gx={gx:.3f}, gy={gy:.3f}, th_geo={th_geo:.3f} rad ({math.degrees(th_geo):.1f} deg)")
