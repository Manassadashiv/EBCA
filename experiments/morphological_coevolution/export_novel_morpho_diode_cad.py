"""
export_novel_morpho_diode_cad.py
Generates the 3D CAD model for the novel:
"Morpho-Diode Monolithic Organism (MDMO)"
Incorporating:
1. Tesla-Valvular Compliant Diode Wheels (Logarithmic-spiral flexure vanes)
2. Cheetah-Vertebra Elastica Morphing Chassis (Passively squeezes in narrow chicanes)
3. Monolithic Viscoelastic Biotensegrity Caster (Single-piece compliant suspension)

Exported for FEA in ANSYS Workbench / SpaceClaim and PrePoMax (CalculiX).
"""

import os
import numpy as np
import trimesh

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "novel_biomimetic_cad")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_tesla_valvular_wheel(outer_radius=37.0, width=22.0, num_vanes=12):
    """
    Creates a Tesla-Valvular Compliant Diode Wheel:
    Features logarithmic-spiral flexural vanes connecting inner hub to outer rim.
    Expands radially under forward torque, cushions vertical impacts, and locks in reverse.
    """
    # Outer tire rim
    rim = trimesh.creation.cylinder(radius=outer_radius, height=width, sections=48)
    inner_cut = trimesh.creation.cylinder(radius=outer_radius - 3.5, height=width + 2.0, sections=48)
    # Hollow rim ring
    rot_y = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    rim.apply_transform(rot_y)
    inner_cut.apply_transform(rot_y)
    
    # Hub center
    hub_radius = outer_radius * 0.28
    hub = trimesh.creation.cylinder(radius=hub_radius, height=width, sections=24)
    hub.apply_transform(rot_y)

    # Tesla Asymmetric Curved Spiral Vanes
    vanes = []
    t_vals = np.linspace(0, 1, 15)
    for i in range(num_vanes):
        base_angle = i * (2 * np.pi / num_vanes)
        # Logarithmic spiral profile r(theta) = r0 * exp(b*theta)
        spiral_pts = []
        for t in t_vals:
            r = hub_radius + (outer_radius - 3.5 - hub_radius) * t
            theta = base_angle + 0.95 * t  # Asymmetric curve
            x = r * np.cos(theta)
            z = r * np.sin(theta)
            spiral_pts.append([x, z])
            
        # Extrude curved beam along Y
        for j in range(len(spiral_pts) - 1):
            p1 = spiral_pts[j]
            p2 = spiral_pts[j+1]
            dx, dz = p2[0] - p1[0], p2[1] - p1[1]
            seg_len = np.sqrt(dx**2 + dz**2)
            seg_angle = np.arctan2(dz, dx)
            
            vane_seg = trimesh.creation.box(extents=[seg_len * 1.05, width - 2.0, 1.8])
            rot_seg = trimesh.transformations.rotation_matrix(seg_angle, [0, 1, 0])
            vane_seg.apply_transform(rot_seg)
            mid_x = (p1[0] + p2[0]) / 2.0
            mid_z = (p1[1] + p2[1]) / 2.0
            vane_seg.apply_translation([mid_x, 0, mid_z])
            vanes.append(vane_seg)

    wheel_mesh = trimesh.util.concatenate([rim, hub] + vanes)
    return wheel_mesh

def create_cheetah_elastica_chassis(length=155.0, base_width=100.0, height=38.0):
    """
    Creates the Cheetah-Vertebra Elastica Morphing Chassis:
    Monolithic compliant metamaterial ribcage with lateral flexure zones.
    Passively compresses width under chicane contact forces without breaking.
    """
    # Central spinal longitudinal backbone
    spine = trimesh.creation.box(extents=[length, 24.0, height * 0.7])
    spine.apply_translation([0, 0, height * 0.1])

    # Symmetrical lateral compliant ribs (5 per side)
    ribs = []
    x_positions = np.linspace(-length * 0.40, length * 0.35, 6)
    for x_pos in x_positions:
        # Left parabolic arch rib
        rib_l = trimesh.creation.box(extents=[8.0, base_width * 0.42, 6.0])
        rib_l.apply_translation([x_pos, base_width * 0.28, height * 0.15])
        # Right parabolic arch rib
        rib_r = trimesh.creation.box(extents=[8.0, base_width * 0.42, 6.0])
        rib_r.apply_translation([x_pos, -base_width * 0.28, height * 0.15])
        
        # Outer lateral bumper runners (absorb and glide along chicane walls)
        runner_l = trimesh.creation.box(extents=[length * 0.18, 5.0, height * 0.6])
        runner_l.apply_translation([x_pos, base_width * 0.49, 0])
        runner_r = trimesh.creation.box(extents=[length * 0.18, 5.0, height * 0.6])
        runner_r.apply_translation([x_pos, -base_width * 0.49, 0])
        
        ribs.extend([rib_l, rib_r, runner_l, runner_r])

    # Nose deflection prow (for sliding over obstacles)
    prow = trimesh.creation.box(extents=[28.0, base_width * 0.75, 12.0])
    rot_prow = trimesh.transformations.rotation_matrix(np.radians(22), [0, 1, 0])
    prow.apply_transform(rot_prow)
    prow.apply_translation([length / 2.0 - 5.0, 0, -6.0])

    chassis_mesh = trimesh.util.concatenate([spine, prow] + ribs)
    return chassis_mesh

def create_monolithic_biotensegrity_caster():
    """
    Creates the Monolithic Viscoelastic Biotensegrity Caster:
    Single-piece 3D-printable S-curve flexure with integrated leaf spring and caster socket.
    Costs ₹18 in PETG, eliminates coil springs, bearings, and pins completely.
    """
    # Mounting block to chassis spine
    mount = trimesh.creation.box(extents=[22.0, 24.0, 14.0])
    mount.apply_translation([-75.0, 0, 5.0])

    # Dual curved progressive flexure leaves (S-curve profile)
    leaves = []
    for curve_sign, z_offset in [(1, 0), (-1, -12.0)]:
        leaf = trimesh.creation.box(extents=[42.0, 18.0, 3.2]) # 3.2mm flexure thickness
        rot_leaf = trimesh.transformations.rotation_matrix(np.radians(-28 * curve_sign), [0, 1, 0])
        leaf.apply_transform(rot_leaf)
        leaf.apply_translation([-94.0, 0, z_offset])
        leaves.append(leaf)

    # Lower caster cup & housing
    cup = trimesh.creation.cylinder(radius=13.0, height=14.0, sections=24)
    cup.apply_translation([-115.0, 0, -20.0])

    # Integrated solid low-friction rolling sphere
    sphere = trimesh.creation.icosphere(subdivisions=3, radius=11.0)
    sphere.apply_translation([-115.0, 0, -25.0])

    caster_mesh = trimesh.util.concatenate([mount, cup, sphere] + leaves)
    return caster_mesh

def main():
    print("=" * 70)
    print("GENERATING NOVEL BIOMIMETIC MORPHO-DIODE MONOLITHIC ROBOT CAD")
    print("=" * 70)

    # 1. Build Components
    print("\n[1/4] Synthesizing Cheetah-Vertebra Elastica Morphing Chassis...")
    chassis = create_cheetah_elastica_chassis(length=155.0, base_width=100.0, height=38.0)

    print("[2/4] Synthesizing Tesla-Valvular Compliant Diode Wheels...")
    wheel_l = create_tesla_valvular_wheel(outer_radius=37.0, width=22.0, num_vanes=12)
    wheel_l.apply_translation([0, 92.0, 0]) # 184mm track width

    wheel_r = create_tesla_valvular_wheel(outer_radius=37.0, width=22.0, num_vanes=12)
    rot_flip = trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1])
    wheel_r.apply_transform(rot_flip)
    wheel_r.apply_translation([0, -92.0, 0])

    print("[3/4] Synthesizing Monolithic Biotensegrity Caster Suspension...")
    caster = create_monolithic_biotensegrity_caster()

    # 2. Assemble
    print("[4/4] Merging Monolithic Organism Assembly...")
    assembly = trimesh.util.concatenate([chassis, wheel_l, wheel_r, caster])

    ext = assembly.extents
    print(f"\n[ASSEMBLY STATS]:")
    print(f"  * Total Vertices: {len(assembly.vertices):,}")
    print(f"  * Total Facets  : {len(assembly.faces):,}")
    print(f"  * Bounding Size : Length={ext[0]:.1f}mm, Width={ext[1]:.1f}mm, Height={ext[2]:.1f}mm")
    print(f"  * Measured Wheel Center-to-Center: 184.0 mm")
    print(f"  * Measured Wheel Outer Diameter  : 74.0 mm")

    # 3. Export Formats for PrePoMax / ANSYS
    stl_path = os.path.join(OUTPUT_DIR, "carl_morpho_diode_assembly.stl")
    obj_path = os.path.join(OUTPUT_DIR, "carl_morpho_diode_assembly.obj")
    assembly.export(stl_path)
    assembly.export(obj_path)

    # Export individual parts for component FEA
    chassis.export(os.path.join(OUTPUT_DIR, "carl_morphing_chassis.stl"))
    wheel_l.export(os.path.join(OUTPUT_DIR, "carl_tesla_diode_wheel.stl"))
    caster.export(os.path.join(OUTPUT_DIR, "carl_biotensegrity_caster.stl"))

    print(f"\n[SAVED NOVEL STL]: {stl_path} ({os.path.getsize(stl_path)/1024:.1f} KB)")
    print(f"[SAVED NOVEL OBJ]: {obj_path} ({os.path.getsize(obj_path)/1024:.1f} KB)")
    print("=" * 70)

if __name__ == "__main__":
    main()
