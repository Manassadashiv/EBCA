# CARL / GENESIS — Session State and Handoff Document
### Last Updated: 2026-07-10
### Authors: Manas + Antigravity

> Read this at the start of every new session before touching any code.

---

## 1. The Mission (Never Forget This)

GENESIS is not a robotics project. It is an attempt to create digital life.

The original question was never 'can we build a robot?' It was:
'Can we create a new form of life?'

CARL is the first organism built on GENESIS. It is not an assistant. Not a task solver.
It is a newborn digital organism that perceives, remembers, imagines, learns, makes mistakes,
adapts, and survives — because those behaviors EMERGE, not because we scripted them.

The three scientific foundations (from GENESIS_MANIFEST.md):
1. Autopoiesis — the brain maintains itself. Unused synapses decay. Active ones grow.
2. Critical Brain Hypothesis — reservoir at edge of chaos (branching ratio sigma = 1.0)
3. Reservoir Computing / Liquid State Machine — ~500 neurons, fixed random weights at criticality.

---

## 2. The Critical Gap

### The brain exists. The body exists. They are DISCONNECTED.

phase18_alife_pretrained.py = THE EMERGENT BRAIN
- Has: food drives, social, sleep, fear, DA/NE/5HT/ACh, STDP, grid cells
- Runs on: world/carl_mujoco.xml (old wheeled body, no arms)

GENESIS/carl_scout/carl_primate_scout.xml = THE NEW BODY
- Has: 28-DOF, arms, hands, touch sensors, webbed palms
- Has: SCRIPTED state machine only (carl_autonomous.py)
- Missing: LiDAR, arm proprioception, food, drives, emergent brain

---

## 3. Known Body Loopholes

1. Mecanum wheels fake — visual only, cannot strafe
2. Only 1 knuckle per finger — stiff rods, cannot curl
3. Spine kp=5000 — too rigid, acts like steel rod
4. NO LIDAR IN XML — brainstem expects 24 rays, none exist
5. No arm proprioception — reads qpos directly (cheating)
6. No spine sensors — brain cannot feel posture
7. Eyes are decorative — no camera sensor exists
8. Ball + cylinder objects 2m away — outside arm reach
9. middle_R_tip wrong collision mask (partially fixed)
10. Workspace margin near-zero — cubes barely reachable

---

## 4. The Three-Option Decision

Option A — Run phase18 as-is TODAY
Get the emergent brain running. Confirm food-seeking, fear, social behavior works.

Option B — Merge phase18 brain into Primate Scout body (3-5 days)
Port physics interface, add LiDAR, add food, wire active inference to arms.

Option C — Build GENESIS Manifest body from scratch
New genesis_body.xml = Wall-E stable body + 16-ray LiDAR + food + neck expression + arms.
Exact spec from docs/GENESIS_MANIFEST.md Section III.

DECISION: Option A first. Confirm phase18 runs. Then A->B or A->C.

---

## 5. The 5 Manifest Files (NONE EXIST YET)

genesis_body.xml       — NOT BUILT
genesis_physics.py     — NOT BUILT
genesis_reservoir.py   — NOT BUILT (THE MOST CRITICAL MISSING PIECE — the LSM brain)
genesis_world.py       — NOT BUILT (food, day/night, pheromones)
genesis_run.py         — NOT BUILT

---

## 6. All Phase18 Dependencies (VERIFIED WORKING 2026-07-10)

phase18_alife_pretrained.py  — d:\carl_simulation\ (53KB)
carl_mj_physics.py           — d:\carl_simulation\world\
carl_mujoco.xml              — d:\carl_simulation\world\ (old wheeled body XML)
carl_grid_cells.py           — d:\carl_simulation\brain\
carl_stdp.py                 — d:\carl_simulation\brain\
carl_omega_extensions.py     — d:\carl_simulation\brain\
carl_physarum.py             — d:\carl_simulation\brain\
astar.py                     — d:\carl_simulation\brain\

Run command (from d:\carl_simulation):
  .\venv\Scripts\python.exe phase18_alife_pretrained.py

---

## 7. Next Immediate Steps

1. Confirm phase18 runs
2. Set up GENESIS\workstation\ folder with phase18 + all brain deps
3. Add 16-ray LiDAR to carl_primate_scout.xml
4. Add food pellets to the scene
5. Wire carl_allostatic.py into main loop (already exists in GENESIS/carl_scout/)
6. Build genesis_reservoir.py — the LSM brain

---

## 8. Mini + Major Project Framing

Mini Project: CARL simulation — digital organism in MuJoCo
Major Project: Physical hardware prototype — same brain, real body
Title: 'GENESIS: A Framework for Digital Organisms. CARL — The First Embodied Synthetic Life.'
DO NOT frame it as 'a robot arm picking up a cube.' That is the least interesting part.

---

'We set up the physics. We set up the chemistry. We light the match.
What catches fire is up to CARL.'
— GENESIS Manifest, 21 May 2026
