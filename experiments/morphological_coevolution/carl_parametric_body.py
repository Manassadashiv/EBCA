"""
carl_parametric_body.py
Dynamic MuJoCo XML generator for Brain-Directed Morphological Co-Evolution.
Generates a parametric robot body and a multi-terrain challenge gauntlet:
1. Step obstacle (height 12 mm) -> penalizes tiny wheel radius (r < 0.038m).
2. Low-friction ice patch (mu = 0.15) -> tests mass distribution and traction.
3. Narrow chicane (width 0.23m) -> penalizes wide wheelbase (L > 0.20m).
4. Goal area at x = 6.2m.
"""

def generate_carl_xml(
    wheelbase_L: float = 0.20,      # Distance between left and right wheels (m)
    wheel_radius_r: float = 0.045,   # Wheel radius (m)
    chassis_mass_m: float = 1.0,     # Chassis mass (kg)
    caster_stiffness_k: float = 350, # Caster spring stiffness (N/m)
    caster_damping_c: float = 18.0,  # Caster damper (N*s/m)
    tire_friction: float = 1.1       # Tire-ground friction
) -> str:
    half_L = wheelbase_L / 2.0
    chassis_half_y = max(0.04, half_L - 0.02)
    chassis_z_pos = wheel_radius_r + 0.005
    wheel_width = 0.012

    xml = f"""<mujoco model="carl_coevolution">
  <compiler angle="radian" autolimits="true"/>
  <option gravity="0 0 -9.81" timestep="0.005" iterations="40" solver="Newton" tolerance="1e-9"/>

  <visual>
    <headlight ambient="0.3 0.3 0.35" diffuse="0.6 0.6 0.7" specular="0 0 0"/>
    <rgba haze="0.05 0.05 0.08 1"/>
  </visual>

  <asset>
    <texture name="grid" type="2d" builtin="checker" width="512" height="512"
             rgb1="0.08 0.09 0.12" rgb2="0.12 0.14 0.18"/>
    <material name="floor_mat" texture="grid" texrepeat="20 5" reflectance="0.05"/>
    <material name="ice_mat" rgba="0.6 0.85 1.0 0.85" reflectance="0.6" shininess="0.9"/>
    <material name="step_mat" rgba="0.8 0.4 0.1 1" reflectance="0.2"/>
    <material name="wall_mat" rgba="0.2 0.25 0.35 1" reflectance="0.3"/>
    <material name="chassis_mat" rgba="0.1 0.7 0.9 1" reflectance="0.5"/>
    <material name="tire_mat" rgba="0.05 0.05 0.05 1" reflectance="0.1"/>
    <material name="goal_mat" rgba="0.1 1.0 0.4 0.8" emission="0.8"/>
  </asset>

  <default>
    <geom contype="1" conaffinity="1" condim="3" friction="0.85 0.005 0.0001"/>
  </default>

  <worldbody>
    <light name="sun" pos="3.0 1.0 5.0" dir="0 0 -1" directional="true"/>

    <!-- Floor (Length 10m, Width 3m) -->
    <geom name="floor" type="plane" size="6.0 2.0 0.1" pos="3.0 1.0 0" material="floor_mat"/>

    <!-- Outer Corridor Walls -->
    <geom name="w_south" type="box" size="3.5 0.04 0.15" pos="3.5 0.0 0.15" material="wall_mat"/>
    <geom name="w_north" type="box" size="3.5 0.04 0.15" pos="3.5 2.0 0.15" material="wall_mat"/>

    <!-- Zone 1: Step Obstacle (x = 1.8m, height = 11mm) -->
    <geom name="step_obstacle" type="box" size="0.10 0.95 0.0055" pos="1.80 1.0 0.0055" material="step_mat"/>

    <!-- Zone 2: Ice Patch (x in [2.6, 3.8]m, friction = 0.15) -->
    <geom name="ice_patch" type="box" size="0.60 0.95 0.001" pos="3.20 1.0 0.001"
          material="ice_mat" friction="0.15 0.001 0.00005"/>

    <!-- Zone 3: Narrow Chicane (x in [4.5, 5.1]m, gap width = 0.28m, centered at y=1.0) -->
    <geom name="chicane_s" type="box" size="0.30 0.43 0.15" pos="4.80 0.43 0.15" material="wall_mat"/>
    <geom name="chicane_n" type="box" size="0.30 0.43 0.15" pos="4.80 1.57 0.15" material="wall_mat"/>

    <!-- Goal Target at x = 6.0m -->
    <geom name="goal" type="cylinder" size="0.25 0.01" pos="6.0 1.00 0.01" material="goal_mat" contype="0" conaffinity="0"/>

    <!-- ==================== THE PARAMETRIC CARL ORGANISM ==================== -->
    <body name="carl_base" pos="0.5 1.0 {chassis_z_pos}">
      <freejoint name="root"/>
      
      <!-- Main Chassis Box -->
      <geom name="chassis" type="box" size="0.08 {chassis_half_y} 0.02" mass="{chassis_mass_m}"
            material="chassis_mat" friction="0.2 0.005 0.0001"/>

      <!-- Left Drive Wheel -->
      <body name="left_wheel" pos="0 {half_L} 0">
        <joint name="joint_lw" type="hinge" axis="0 1 0" damping="0.02"/>
        <geom name="lw_geom" type="cylinder" size="{wheel_radius_r} {wheel_width}" euler="1.5708 0 0"
              mass="0.15" material="tire_mat" friction="{tire_friction} 0.005 0.0001"/>
      </body>

      <!-- Right Drive Wheel -->
      <body name="right_wheel" pos="0 -{half_L} 0">
        <joint name="joint_rw" type="hinge" axis="0 1 0" damping="0.02"/>
        <geom name="rw_geom" type="cylinder" size="{wheel_radius_r} {wheel_width}" euler="1.5708 0 0"
              mass="0.15" material="tire_mat" friction="{tire_friction} 0.005 0.0001"/>
      </body>

      <!-- Rear Caster Suspension Leg (Spring-Damper Slide Joint) -->
      <body name="caster_suspension" pos="-0.09 0 0">
        <joint name="joint_caster_z" type="slide" axis="0 0 1" range="-0.015 0.015"
               stiffness="{caster_stiffness_k}" damping="{caster_damping_c}"/>
        <geom name="caster_ball" type="sphere" size="0.018" pos="0 0 -{wheel_radius_r - 0.018}"
              mass="0.06" friction="0.05 0.001 0.0001"/>
      </body>

      <!-- Front Distance Sensors -->
      <site name="sonar_front" pos="0.08 0 0.01" euler="0 0 0"/>
      <site name="sonar_left" pos="0.07 0.03 0.01" euler="0 0 0.45"/>
      <site name="sonar_right" pos="0.07 -0.03 0.01" euler="0 0 -0.45"/>
    </body>
  </worldbody>

  <actuator>
    <velocity name="motor_l" joint="joint_lw" kv="2.0" ctrlrange="-25 25" forcerange="-0.8 0.8"/>
    <velocity name="motor_r" joint="joint_rw" kv="2.0" ctrlrange="-25 25" forcerange="-0.8 0.8"/>
  </actuator>

  <sensor>
    <rangefinder name="rf_front" site="sonar_front"/>
    <rangefinder name="rf_left" site="sonar_left"/>
    <rangefinder name="rf_right" site="sonar_right"/>
    <accelerometer name="imu_accel" site="sonar_front"/>
    <gyro name="imu_gyro" site="sonar_front"/>
  </sensor>
</mujoco>
"""
    return xml

if __name__ == "__main__":
    test_xml = generate_carl_xml()
    import mujoco
    m = mujoco.MjModel.from_xml_string(test_xml)
    print("Parametric CARL XML compiled successfully! Nu =", m.nu, "Nq =", m.nq)
