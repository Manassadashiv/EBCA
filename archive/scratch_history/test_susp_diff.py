import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import mujoco, re
from tests.run_stage3_4_final_200_battery import execute_episode, build_50_matched_configurations, CarlStage1HAL, ENV1_XML

configs = build_50_matched_configurations()
cfg = configs[0]

# 1. With suspension
hal = CarlStage1HAL(xml_path=str(ENV1_XML))
res1 = execute_episode('ARM-A', cfg, hal)
print('With suspension: escaped=', res1['escaped'], 'coll=', res1['had_collision'], 'ticks=', res1['ticks'])

# 2. Without suspension
xml_text = ENV1_XML.read_text()
xml_no_susp = re.sub(r'<joint name="susp_caster_.*?/>', '', xml_text)

hal_no = CarlStage1HAL(xml_path=str(ENV1_XML))
hal_no.model = mujoco.MjModel.from_xml_string(xml_no_susp)
hal_no.data = mujoco.MjData(hal_no.model)
res2 = execute_episode('ARM-A', cfg, hal_no)
print('Without suspension: escaped=', res2['escaped'], 'coll=', res2['had_collision'], 'ticks=', res2['ticks'])
