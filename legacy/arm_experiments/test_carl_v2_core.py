"""
Unit test for CARL-v2 Operational Space Control & Tactile Admittance Engine
"""
import sys
import numpy as np
import mujoco

sys.path.append(r"d:\ebca")
from carl_v2_core import OperationalSpaceController, TactileAdmittanceController, run_carl_v2_control_step

MODEL_PATH = r"D:\ebca\world\vessel_kinetic.xml"

def test_carl_v2_core():
    print("=" * 80)
    print("  CARL-v2 CORE MODULE UNIT TEST")
    print("=" * 80)
    
    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)
    
    osc = OperationalSpaceController(model, "touch_site_L")
    admittance = TactileAdmittanceController(k_adm=0.002, max_clamp=0.52)
    
    # Place target cube
    _cube_j_id = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "fj_cube_2")]
    data.qpos[_cube_j_id:_cube_j_id+3] = [0.20, 0.0, 0.048]
    data.qpos[_cube_j_id+3:_cube_j_id+7] = [1.0, 0.0, 0.0, 0.0]
    mujoco.mj_forward(model, data)
    
    print("[TEST] Running 100 CARL-v2 Operational Space control steps...")
    for step in range(100):
        # Action 4D: Move hand down towards cube (-Z velocity) and request 3.0 N clamp force
        action_4d = np.array([0.01, 0.0, -0.02, 3.0])
        
        ctrl = run_carl_v2_control_step(model, data, osc, admittance, action_4d)
        
        # Apply to model actuators
        for i in range(min(len(ctrl), model.nu)):
            data.ctrl[i] = ctrl[i]
            
        mujoco.mj_step(model, data)
        
    t1 = float(data.sensor("touch_L").data[0])
    t2 = float(data.sensor("touch_bot_L").data[0])
    t3 = float(data.sensor("touch_thumb_L").data[0])
    
    print(f"[TEST SUCCESS] 100 control steps completed cleanly!")
    print(f"[TEST TELEMETRY] Touch Forces: F1={t1:.3f}N | F2={t2:.3f}N | F3={t3:.3f}N")
    print(f"[TEST TELEMETRY] Final Admittance Clamp Angle: {admittance.current_clamp:.3f} rad")
    print("=" * 80)

if __name__ == "__main__":
    test_carl_v2_core()
