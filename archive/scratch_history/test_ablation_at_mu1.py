import sys
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import (
    generate_matched_configs, CarlStage1HAL, XML_PATH, execute_physical_episode
)
import scipy.stats as stats

hal = CarlStage1HAL(xml_path=str(XML_PATH), headless=True)
configs = generate_matched_configs(num_configs=20, seed=5301)
intact_esc = 0
abl_esc = 0

for idx, cfg in enumerate(configs):
    side = "left" if idx % 2 == 0 else "right"
    # Testing motor degradation perturbation: intact vs ablated
    r_int = execute_physical_episode(config=cfg, hal=hal, floor_friction=1.0, torque_loss_side=side, endocrine_enabled=True)
    r_abl = execute_physical_episode(config=cfg, hal=hal, floor_friction=1.0, torque_loss_side=side, endocrine_enabled=False)
    if r_int["escaped"]: intact_esc += 1
    if r_abl["escaped"]: abl_esc += 1
    print(f"Ep {idx:2d}: Intact={'ESC' if r_int['escaped'] else 'NO '} | Abl={'ESC' if r_abl['escaped'] else 'NO '}")

int_pct = (intact_esc / 20) * 100
abl_pct = (abl_esc / 20) * 100
delta = int_pct - abl_pct
_, p_val = stats.fisher_exact([[intact_esc, 20-intact_esc], [abl_esc, 20-abl_esc]], alternative='greater')
print(f"Summary: Intact={intact_esc}/20 ({int_pct}%), Ablated={abl_esc}/20 ({abl_pct}%), Delta=+{delta}%, p={p_val:.6f}")
