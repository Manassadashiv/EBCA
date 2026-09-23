"""
test_collision_auditor.py — Unit Test for MuJoCo Fine-Grained Contact Classifier
"""

import mujoco
import numpy as np
from brain.carl_embodied_organism import CarlEmbodiedOrganism

class MockHAL:
    def __init__(self, xml_path="D:/ebca/world/vessel_kinetic.xml"):
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        
    def get_robot_pos(self):
        qbase_adr = self.model.joint('spatial_identity').qposadr[0]
        x = float(self.data.qpos[qbase_adr])
        y = float(self.data.qpos[qbase_adr + 1])
        qw = float(self.data.qpos[qbase_adr + 3])
        qx = float(self.data.qpos[qbase_adr + 4])
        qy = float(self.data.qpos[qbase_adr + 5])
        qz = float(self.data.qpos[qbase_adr + 6])
        yaw = np.arctan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy**2 + qz**2))
        return x, y, yaw

def test_contact_filtering():
    hal = MockHAL()
    embodiment = CarlEmbodiedOrganism()
    
    # Step physics for settling
    for _ in range(50):
        mujoco.mj_step(hal.model, hal.data)
        
    sensory = embodiment.read_proprioception(hal)
    
    print(f"Total World Solver Constraints (ncon): {sensory.ncon}")
    print(f"Left Wheel Ground Contacts:  {sensory.wheel_contacts_L}")
    print(f"Right Wheel Ground Contacts: {sensory.wheel_contacts_R}")
    print(f"Caster Ground Contacts:      {sensory.caster_contacts}")
    print(f"Robot Wall Contacts:         {sensory.robot_wall_contacts}")
    print(f"Robot Obstacle Contacts:     {sensory.robot_obstacle_contacts}")
    print(f"Chassis Floor Impacts:       {sensory.chassis_floor_contacts}")
    print(f"Has Body Collision:          {sensory.has_body_collision}")
    
    assert sensory.ncon >= 10, "World should contain prop resting contacts"
    assert sensory.wheel_contacts_L > 0, "Left wheel must contact floor"
    assert sensory.wheel_contacts_R > 0, "Right wheel must contact floor"
    assert sensory.caster_contacts > 0, "Casters must contact floor"
    assert sensory.robot_wall_contacts == 0, "Robot must not contact walls at spawn"
    assert sensory.robot_obstacle_contacts == 0, "Robot must not contact obstacles at spawn"
    assert sensory.chassis_floor_contacts == 0, "Chassis must not hit floor"
    assert sensory.has_body_collision == False, "Normal rolling must NEVER trigger has_body_collision!"
    
    print("\n[PASS] Collision contact auditor unit test passed flawlessly!")

if __name__ == "__main__":
    test_contact_filtering()
