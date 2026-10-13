import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, CarlAutonomousOrganismAgent, GRID_PATH
import mujoco, numpy as np, math

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)
bumper_id = hal.model.geom("chassis_bumper").id

damaging_eps = []
escaped_eps = []

for idx, cfg in enumerate(cfgs):
    hal.reset()
    sx, sy = cfg["spawn_pos"]
    syaw = cfg["spawn_yaw"]
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa + 2] = [sx, sy]
    hal.data.qpos[qa + 3:qa + 7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)
    hal.set_floor_friction(0.20)

    agent = CarlAutonomousOrganismAgent(dt=hal.dt, deliberation_mode="active_inference", grid_path=str(GRID_PATH))
    agent.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))

    had_dmg = False
    escaped = False
    c_force = np.zeros(6, dtype=np.float64)

    for t in range(650):
        res = agent.step_cognitive_cycle(hal)
        u = res["action_cmd"]
        s, diag = hal.step(u)

        # Grounded collision check: structural penetration (< -4mm) or non-bumper collision
        for i in range(hal.data.ncon):
            c = hal.data.contact[i]
            in1 = c.geom1 in hal.carl_geom_ids
            in2 = c.geom2 in hal.carl_geom_ids
            if (in1 and not in2) or (in2 and not in1):
                other = c.geom2 if in1 else c.geom1
                carl_g = c.geom1 if in1 else c.geom2
                if other != hal.floor_geom_id:
                    is_bumper = (carl_g == bumper_id)
                    if not is_bumper or c.dist < -0.004:
                        had_dmg = True
                        break
        if diag["pos_x"] < -0.55:
            escaped = True
            break

    if escaped:
        escaped_eps.append(idx)
    if had_dmg:
        damaging_eps.append(idx)
    print(f"Ep {idx:2d}: escaped={escaped}, damaging_collision={had_dmg}, ticks={t+1}", flush=True)

print(f"\nSummary: Escapes: {len(escaped_eps)}/30 ({len(escaped_eps)/30*100:.1f}%), Damaging collisions: {len(damaging_eps)}/30 ({len(damaging_eps)/30*100:.1f}%)")
