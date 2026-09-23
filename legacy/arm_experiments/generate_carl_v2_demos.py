"""
CARL-v2 Expert Demonstration Generator
Generates 500 expert trajectories for Behavior Cloning (BC) pre-training.
"""
import os
import sys
import numpy as np
import mujoco

sys.path.append(r"d:\ebca")
from carl_v2_core import OperationalSpaceController, TactileAdmittanceController, run_carl_v2_control_step

MODEL_PATH = r"D:\ebca\world\vessel_kinetic.xml"
DEMO_PATH = r"D:\ebca\memory\carl_v2_expert_demos.npz"

def generate_expert_demonstrations(num_episodes: int = 500):
    print("=" * 80)
    print(f"  CARL-v2 EXPERT DEMONSTRATION GENERATOR ({num_episodes} EPISODES)")
    print("=" * 80)

    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)

    osc = OperationalSpaceController(model, "touch_site_L")
    admittance = TactileAdmittanceController(k_adm=0.002, max_clamp=0.52)

    _cube_j_id = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "fj_cube_2")]

    states_list = []
    actions_list = []

    successful_demos = 0

    for ep in range(num_episodes):
        np.random.seed(ep + 10000)
        mujoco.mj_resetData(model, data)

        target_x = float(np.random.uniform(0.18, 0.22))
        target_y = float(np.random.uniform(-0.05, 0.05))
        target_z = 0.048

        data.qpos[_cube_j_id:_cube_j_id+3] = [target_x, target_y, target_z]
        data.qpos[_cube_j_id+3:_cube_j_id+7] = [1.0, 0.0, 0.0, 0.0]
        mujoco.mj_forward(model, data)

        ep_states = []
        ep_actions = []

        for step in range(120):
            # Compute current end-effector 3D position
            site_pos = data.site_xpos[osc.site_id].copy()
            cube_pos = data.body("obj_cube_2").xpos.copy()

            # Target 3D velocity vector (towards cube)
            dx = cube_pos[0] - site_pos[0]
            dy = cube_pos[1] - site_pos[1]
            dz = (max(0.018, cube_pos[2] + 0.009)) - site_pos[2]

            v_x = float(np.clip(dx * 5.0, -0.10, 0.10))
            v_y = float(np.clip(dy * 5.0, -0.10, 0.10))
            v_z = float(np.clip(dz * 5.0, -0.10, 0.10))
            f_target = 3.5 if step > 25 else 0.0

            action_4d = np.array([v_x, v_y, v_z, f_target])

            # State representation: [qpos(5), qvel(5), ee_pos(3), cube_pos(3), touch_sensors(3)]
            touch_f1 = float(data.sensor("touch_L").data[0])
            touch_f2 = float(data.sensor("touch_bot_L").data[0])
            touch_f3 = float(data.sensor("touch_thumb_L").data[0])

            state_obs = np.concatenate([
                data.qpos[0:5].copy(),
                data.qvel[0:5].copy(),
                site_pos,
                cube_pos,
                [touch_f1, touch_f2, touch_f3]
            ])

            ep_states.append(state_obs)
            ep_actions.append(action_4d)

            ctrl = run_carl_v2_control_step(model, data, osc, admittance, action_4d)
            for i in range(min(len(ctrl), model.nu)):
                data.ctrl[i] = ctrl[i]

            mujoco.mj_step(model, data)

        states_list.append(np.array(ep_states))
        actions_list.append(np.array(ep_actions))
        successful_demos += 1

        if (ep + 1) % 100 == 0:
            print(f"  [DEMO GEN] Collected {ep + 1}/{num_episodes} expert demonstration trajectories...")

    os.makedirs(r"D:\ebca\memory", exist_ok=True)
    np.savez_compressed(DEMO_PATH, states=np.array(states_list), actions=np.array(actions_list))
    print("=" * 80)
    print(f"[DEMO GEN SUCCESS] Saved {successful_demos} expert demonstrations to {DEMO_PATH}")
    print("=" * 80)

if __name__ == "__main__":
    generate_expert_demonstrations(500)
