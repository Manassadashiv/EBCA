import os
import sys
import numpy as np
import mujoco

xml_path = "D:/ebca/world/vessel_kinetic.xml"
with open(xml_path, "r", encoding="utf-8") as f:
    xml_content = f.read()

# Add armature and clean damping to all hinge joints
xml_content = xml_content.replace('<joint name="w_left" type="hinge" axis="0 1 0" damping="0.001" frictionloss="0.0001" />',
                                  '<joint name="w_left" type="hinge" axis="0 1 0" damping="0.05" armature="0.005" frictionloss="0.001" />')
xml_content = xml_content.replace('<joint name="w_right" type="hinge" axis="0 1 0" damping="0.001" frictionloss="0.0001" />',
                                  '<joint name="w_right" type="hinge" axis="0 1 0" damping="0.05" armature="0.005" frictionloss="0.001" />')
xml_content = xml_content.replace('<joint name="hip_pitch" type="hinge" axis="0 1 0" range="-0.15 0.15" stiffness="40.0" damping="5.0" />',
                                  '<joint name="hip_pitch" type="hinge" axis="0 1 0" range="-0.15 0.15" damping="0.5" armature="0.005" />')
xml_content = xml_content.replace('<joint name="hip_roll" type="hinge" axis="1 0 0" range="-0.06 0.06" stiffness="100.0" damping="10.0" />',
                                  '<joint name="hip_roll" type="hinge" axis="1 0 0" range="-0.06 0.06" damping="0.5" armature="0.005" />')
xml_content = xml_content.replace('<joint name="neck_sweep" type="hinge" axis="0 1 0" range="-0.6 0.7" stiffness="0.5" damping="0.1" />',
                                  '<joint name="neck_sweep" type="hinge" axis="0 1 0" range="-0.6 0.7" damping="0.2" armature="0.002" />')
xml_content = xml_content.replace('<joint name="head_pan" type="hinge" axis="0 0 1" range="-1.4 1.4" damping="0.1" />',
                                  '<joint name="head_pan" type="hinge" axis="0 0 1" range="-1.4 1.4" damping="0.2" armature="0.002" />')

model = mujoco.MjModel.from_xml_string(xml_content)
data = mujoco.MjData(model)

mujoco.mj_resetData(model, data)
for j in range(model.njnt):
    if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE:
        qa = model.jnt_qposadr[j]
        data.qpos[qa+3 : qa+7] = [1.0, 0.0, 0.0, 0.0]

q_rob = model.joint('spatial_identity').qposadr[0]
v_rob = model.joint('spatial_identity').dofadr[0]
data.qpos[q_rob : q_rob+3] = [0.0, 0.0, 0.05291]
mujoco.mj_forward(model, data)

print("Testing 500 ticks (10,000 substeps) with continuous driving:")
stable = True
for t in range(500):
    data.ctrl[0] = 10.0
    data.ctrl[1] = 10.0
    for _ in range(20):
        mujoco.mj_step(model, data)
    
    if np.isnan(data.qpos).any() or np.isnan(data.qvel).any() or np.isinf(data.qvel).any():
        print(f"UNSTABLE at tick {t}!")
        stable = False
        break

if stable:
    px, py, pz = data.qpos[q_rob : q_rob+3]
    print(f"SUCCESS! Completed 500 ticks perfectly stable! Final pos: ({px:.3f}, {py:.3f}, {pz:.4f})")
