import sys
import os
sys.path.insert(0, os.path.abspath("."))
import numpy as np
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.test_stage2_1b_r1_efference import generate_developmental_babbling
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose

hal = CarlStage1HAL(open_space=True)

for seed in [42, 101, 202]:
    hal.reset()
    apply_stochastic_initial_pose(hal, seed)
    U_train = generate_developmental_babbling(seed, 400)
    S_train = np.array([hal.step(u)[0] for u in U_train])
    
    brain = CarlStage2BIntegratedBrain(seed=seed)
    brain.develop_from_babbling(U_train, S_train)
    k_eff = brain.learn_motor_efference(U_train, S_train)
    
    pos_after_train = hal.get_diagnostics()
    
    U_val = generate_developmental_babbling(seed + 8888, 200)
    S_val = np.array([hal.step(u)[0] for u in U_val])
    val_res = brain.evaluate_efference_prediction(U_val, S_val)
    
    pos_after_val = hal.get_diagnostics()
    
    print(f"R1 Seed {seed:3d}: k_eff={k_eff:.4f}, R2={val_res['r2']:.4f}, corr={val_res['corr']:.4f}")
    print(f"  Pos after train: ({pos_after_train['pos_x']:.2f}, {pos_after_train['pos_y']:.2f}), contacts={pos_after_train['carl_contacts']}")
    print(f"  Pos after val:   ({pos_after_val['pos_x']:.2f}, {pos_after_val['pos_y']:.2f}), contacts={pos_after_val['carl_contacts']}")
