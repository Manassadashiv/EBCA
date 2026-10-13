import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

import mujoco
from tests.test_stage3_4R3_certification import ENV2_XML

with open(str(ENV2_XML), "r") as f:
    xml = f.read()

target = 'range="-0.008 0.008" stiffness="350" damping="18"'
replacement = 'range="0.000 0.006" stiffness="60" damping="12"'
assert target in xml, "Target string not found in XML"
xml_mod = xml.replace(target, replacement)

model = mujoco.MjModel.from_xml_string(xml_mod)
data = mujoco.MjData(model)
qa = int(model.joint("spatial_identity").qposadr[0])

for tick in range(25):
    data.ctrl[0] = 12.5
    data.ctrl[1] = -12.5
    for _ in range(3):
        mujoco.mj_step(model, data)
    z = data.qpos[qa+2]
    ncon = data.ncon
    print(f"t={tick} z={z:.4f} ncon={ncon}")
