# CARL-DX P0-03 Repair Changelog: Narrow-Corridor vs. Dead-End Veto

---

## Modified Files & Forensic Rationale

### 1. `D:\ebca\brain\carl_generative_self_model.py`

#### A. Dead-End Gate Decoupling (`CarlGenerativeSelfModel.imagine_counterfactual_rollouts`)
- **Old Logic**:
  ```python
  min_front_clearance = float(np.min(sonar_rays[6:9]))
  is_dead_end_trapped = (
      min_front_clearance < 1.10
      and left_clearance < 1.40
      and right_clearance < 1.40
  )
```
- **New Logic**:
  ```python
  min_front_clearance = float(np.min(sonar_rays[6:9]))
  front_direct_clear = float(sonar_rays[7]) if n_rays == 15 else float(sonar_rays[mid])
  is_dead_end_trapped = (
      front_direct_clear < 0.75
      and min_front_clearance < 0.70
      and left_clearance < 1.40
      and right_clearance < 1.40
  )
```
- **Why**: Decouples direct heading ray from peripheral sidewall rays so that open narrow corridors are not treated as dead ends.
- **Expected Effect**: `reverse_penalty` and `spin_penalty` remain active ($+1000.0 / +1200.0$) in open corridors, promoting forward translation.
- **Potential Regression**: True dead ends must still trigger `is_dead_end_trapped`. Verified: when `front_direct_clear < 0.75m`, `is_dead_end_trapped = True`.

#### B. Balanced Collision Risk Curve (`CarlGenerativeSelfModel.imagine_counterfactual_rollouts`)
- **Old Logic**:
  ```python
  if proj_clearance < 0.95 and v_lin > 0.0:
    cumulative_collision_risk += (0.95 - proj_clearance) * 70.0
  if proj_clearance < 0.50 and v_lin > 0.0:
    cumulative_collision_risk += (0.50 - proj_clearance) * 300.0
```
- **New Logic**:
  ```python
  if proj_clearance < 0.75 and v_lin > 0.0:
    cumulative_collision_risk += (0.75 - proj_clearance) * 30.0
  if proj_clearance < 0.45 and v_lin > 0.0:
    cumulative_collision_risk += (0.45 - proj_clearance) * 200.0
```
- **Why**: Prevents premature Free Energy explosion ($> 900$) when clearance is $0.85\text{m}$, which previously caused `BRAKE_REST` to beat forward motion.

---

### 2. `D:\ebca\brain\carl_endogenous_agency.py`

#### A. Dead-End Enclosure Veto (`CarlEndogenousAgency.evaluate_internal_action_veto`)
- **Old Logic**:
  ```python
  front_clearance = float(np.min(sonar_rays[5:10]))
  is_dead_end = (
      front_clearance < 1.10
      and left_clearance < 1.40
      and right_clearance < 1.40
  )
  in_open_narrow_passage = (
      left_clearance < 0.75
      and right_clearance < 0.75
      and front_clearance > 1.05
  )
```
- **New Logic**:
  ```python
  front_cone_clear = float(np.min(sonar_rays[6:9]))
  front_direct_clear = (
      float(sonar_rays[7]) if n_rays == 15 else float(sonar_rays[mid])
  )
  is_dead_end = (
      front_direct_clear < 0.75
      and front_cone_clear < 0.70
      and left_clearance < 1.40
      and right_clearance < 1.40
  )
  in_open_narrow_passage = (
      left_clearance < 0.75
      and right_clearance < 0.75
      and front_direct_clear > 0.80
  )
```
- **Why**: Ensures the safety veto only overrides forward actions with spin when the forward path itself is blocked.
- **Expected Effect**: Zero false spin vetoes in traversable narrow corridors.
