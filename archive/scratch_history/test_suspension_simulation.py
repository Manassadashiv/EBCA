"""
scratch/test_suspension_simulation.py
Simulates realistic driving with software slew rate limiting on CARL-DX.
Compares:
1. Baseline rigid caster (k=60, range=[0, 0.006], c=12)
2. Selected BOM Caster (k=350, range=[-0.008, 0.008], c=18)
"""

import mujoco
import numpy as np

def run_test(xml_path, k_val, c_val, range_val, label):
    m = mujoco.MjModel.from_xml_path(xml_path)
    d = mujoco.MjData(m)
    
    for j_name in ['susp_caster_front', 'susp_caster_rear']:
        j_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, j_name)
        if j_id >= 0:
            m.jnt_stiffness[j_id] = k_val
            m.jnt_range[j_id] = range_val
            m.dof_damping[m.jnt_dofadr[j_id]] = c_val
            
    mujoco.mj_resetData(m, d)
    
    qpos_f = m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, 'susp_caster_front')]
    act_L = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, 'act_w_left')
    act_R = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, 'act_w_right')
    
    dt = m.opt.timestep
    n_steps = int(2.0 / dt)
    
    susp_travels = []
    pitch_angles = []
    tire_normal_forces_L = []
    tire_normal_forces_R = []
    slip_events = 0
    
    body_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'drive_deck')
    geom_tire_L = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, 'tire_L')
    geom_tire_R = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, 'tire_R')
    
    current_target_speed = 0.0
    max_accel_per_sec = 8.0 # rad/s^2 smooth ramp
    
    for step in range(n_steps):
        t = step * dt
        if t > 0.4:
            # Smoothly ramp up to cruising speed (6.0 rad/s = ~0.3 m/s)
            current_target_speed = min(6.0, current_target_speed + max_accel_per_sec * dt)
        else:
            current_target_speed = 0.0
            
        d.ctrl[act_L] = current_target_speed
        d.ctrl[act_R] = current_target_speed
            
        mujoco.mj_step(m, d)
        
        travel = d.qpos[qpos_f]
        susp_travels.append(travel)
        
        quat = d.xquat[body_id]
        w, x, y, z = quat
        pitch = np.arcsin(np.clip(2.0 * (w * y - z * x), -1.0, 1.0))
        pitch_angles.append(pitch)
        
        fn_L = 0.0
        fn_R = 0.0
        for i in range(d.ncon):
            con = d.contact[i]
            if con.geom1 == geom_tire_L or con.geom2 == geom_tire_L:
                c_forces = np.zeros(6)
                mujoco.mj_contactForce(m, d, i, c_forces)
                fn_L += c_forces[0]
            if con.geom1 == geom_tire_R or con.geom2 == geom_tire_R:
                c_forces = np.zeros(6)
                mujoco.mj_contactForce(m, d, i, c_forces)
                fn_R += c_forces[0]
        tire_normal_forces_L.append(fn_L)
        tire_normal_forces_R.append(fn_R)
        
        if t > 0.5 and (fn_L < 0.10 or fn_R < 0.10):
            slip_events += 1
            
    susp_travels = np.array(susp_travels)
    pitch_angles = np.array(pitch_angles)
    tire_normal_forces_L = np.array(tire_normal_forces_L)
    tire_normal_forces_R = np.array(tire_normal_forces_R)
    
    print(f"\n=======================================================")
    print(f"CONFIGURATION: {label}")
    print(f"=======================================================")
    print(f"Resting deflection: {susp_travels[int(0.35/dt)]*1000:+.2f} mm")
    print(f"Dynamic Travel Range: [{np.min(susp_travels)*1000:+.2f} mm, {np.max(susp_travels)*1000:+.2f} mm]")
    print(f"Did it bottom out (> {range_val[1]*1000:.1f} mm)? {'YES (HARD LIMIT HIT)' if np.max(susp_travels) >= range_val[1]-1e-4 else 'NO (Smooth floating)'}")
    print(f"Pitch Oscillation Range: {np.ptp(pitch_angles[int(0.5/dt):])*180/np.pi:.2f} degrees")
    print(f"Mean Left Tire Normal Force (Fn): {np.mean(tire_normal_forces_L[int(0.5/dt):]):.2f} N")
    print(f"Mean Right Tire Normal Force (Fn): {np.mean(tire_normal_forces_R[int(0.5/dt):]):.2f} N")
    print(f"Zero-traction lift-off events: {slip_events} ({slip_events / (1.5/dt) * 100:.1f}%)")

if __name__ == '__main__':
    xml = 'world/stage3_4_environments/cul_de_sac_turning_bay.xml'
    run_test(xml, k_val=60.0, c_val=12.0, range_val=np.array([0.0, 0.006]), label="BASELINE (k=60 N/m, Bottomed Out)")
    run_test(xml, k_val=350.0, c_val=18.0, range_val=np.array([-0.008, 0.008]), label="BOM SELECTION: CY-15A Cushioned Spring Caster (k=350 N/m)")
