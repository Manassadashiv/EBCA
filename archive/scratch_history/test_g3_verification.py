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
configs_g3 = generate_matched_configs(num_configs=20, seed=5301)
g3_intact_escapes = 0
g3_ablation_escapes = 0

for idx, cfg in enumerate(configs_g3):
    side = "left" if idx % 2 == 0 else "right"
    res_intact = execute_physical_episode(
        config=cfg,
        hal=hal,
        floor_friction=0.20,
        torque_loss_side=side,
        endocrine_enabled=True
    )
    res_ablation = execute_physical_episode(
        config=cfg,
        hal=hal,
        floor_friction=0.20,
        torque_loss_side=side,
        endocrine_enabled=False
    )
    if res_intact["escaped"]:
        g3_intact_escapes += 1
    if res_ablation["escaped"]:
        g3_ablation_escapes += 1
    print(f"Pair {idx:2d}: Intact={'ESC' if res_intact['escaped'] else 'NO '} | Ablation={'ESC' if res_ablation['escaped'] else 'NO '}")

intact_pct = (g3_intact_escapes / len(configs_g3)) * 100.0
ablation_pct = (g3_ablation_escapes / len(configs_g3)) * 100.0
delta_gain = intact_pct - ablation_pct

contingency = [
    [g3_intact_escapes, len(configs_g3) - g3_intact_escapes],
    [g3_ablation_escapes, len(configs_g3) - g3_ablation_escapes]
]
odds_ratio, p_value = stats.fisher_exact(contingency, alternative="greater")
print(f"Summary: Intact={g3_intact_escapes}/20 ({intact_pct}%), Ablation={g3_ablation_escapes}/20 ({ablation_pct}%)")
print(f"Delta: +{delta_gain}%, p-value: {p_value:.6f}")
