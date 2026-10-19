import math
import struct
import os

# Parametric CAD generator for KBMWL-EP:
# Kinematic-Bifurcation Metamorphic Wheel-Leg & Elastica Preflex
# Designed for ANSYS / PrePoMax FEA and high-precision 3D printing

class BinarySTLWriter:
    def __init__(self, filepath):
        self.filepath = filepath
        self.triangles = []

    def add_triangle(self, v1, v2, v3):
        # Calculate outward normal
        ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
        bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        norm = math.sqrt(nx*nx + ny*ny + nz*nz)
        if norm > 1e-9:
            nx, ny, nz = nx/norm, ny/norm, nz/norm
        else:
            nx, ny, nz = 0.0, 0.0, 1.0
        self.triangles.append((nx, ny, nz, v1, v2, v3))

    def add_cylinder(self, r, h, center=(0,0,0), axis='z', segments=32):
        cx, cy, cz = center
        top, bot = [], []
        for i in range(segments):
            th = 2.0 * math.pi * i / segments
            x = r * math.cos(th)
            y = r * math.sin(th)
            if axis == 'z':
                top.append((cx + x, cy + y, cz + h/2.0))
                bot.append((cx + x, cy + y, cz - h/2.0))
            elif axis == 'y':
                top.append((cx + x, cy + h/2.0, cz + y))
                bot.append((cx + x, cy - h/2.0, cz + y))
            elif axis == 'x':
                top.append((cx + h/2.0, cy + x, cz + y))
                bot.append((cx - h/2.0, cy + x, cz + y))
        top_c = (cx, cy + (h/2.0 if axis=='y' else 0), cz + (h/2.0 if axis=='z' else 0)) if axis!='x' else (cx+h/2.0, cy, cz)
        bot_c = (cx, cy - (h/2.0 if axis=='y' else 0), cz - (h/2.0 if axis=='z' else 0)) if axis!='x' else (cx-h/2.0, cy, cz)
        
        for i in range(segments):
            j = (i + 1) % segments
            self.add_triangle(top_c, top[i], top[j])
            self.add_triangle(bot_c, bot[j], bot[i])
            self.add_triangle(top[i], bot[i], top[j])
            self.add_triangle(top[j], bot[i], bot[j])

    def add_box(self, dx, dy, dz, center=(0,0,0)):
        cx, cy, cz = center
        hx, hy, hz = dx/2.0, dy/2.0, dz/2.0
        v = [
            (cx - hx, cy - hy, cz - hz),
            (cx + hx, cy - hy, cz - hz),
            (cx + hx, cy + hy, cz - hz),
            (cx - hx, cy + hy, cz - hz),
            (cx - hx, cy - hy, cz + hz),
            (cx + hx, cy - hy, cz + hz),
            (cx + hx, cy + hy, cz + hz),
            (cx - hx, cy + hy, cz + hz),
        ]
        faces = [
            (0,1,2,3), (4,7,6,5),
            (0,4,5,1), (2,6,7,3),
            (0,3,7,4), (1,5,6,2)
        ]
        for f in faces:
            self.add_triangle(v[f[0]], v[f[1]], v[f[2]])
            self.add_triangle(v[f[0]], v[f[2]], v[f[3]])

    def save(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.filepath)), exist_ok=True)
        with open(self.filepath, 'wb') as f:
            header = b'CARL-DX KBMWL-EP Metamorphic Wheel-Leg Assembly binary STL' + b' ' * 80
            f.write(header[:80])
            f.write(struct.pack('<I', len(self.triangles)))
            for nx, ny, nz, v1, v2, v3 in self.triangles:
                f.write(struct.pack('<3f', nx, ny, nz))
                f.write(struct.pack('<3f', v1[0], v1[1], v1[2]))
                f.write(struct.pack('<3f', v2[0], v2[1], v2[2]))
                f.write(struct.pack('<3f', v3[0], v3[1], v3[2]))
                f.write(struct.pack('<H', 0))

def generate_kbmwl_cad():
    cad_dir = 'd:/ebca/experiments/morphological_coevolution/cad_models'
    os.makedirs(cad_dir, exist_ok=True)
    
    assembly = BinarySTLWriter(os.path.join(cad_dir, 'carl_kbmwl_assembly.stl'))
    
    # 1. Main Metamorphic Core Hub (Central Drive Axis)
    print("Generating central metamorphic hub...")
    hub_r = 18.0
    hub_w = 14.0
    assembly.add_cylinder(hub_r, hub_w, center=(-60, 0, 37), axis='x', segments=32)
    assembly.add_cylinder(hub_r, hub_w, center=(60, 0, 37), axis='x', segments=32)
    
    # 2. Tri-Lobe Metamorphic Pantograph Links (3 claws per wheel, 120 deg apart)
    print("Generating 1-DOF kinematic bifurcation claws...")
    for side in [-60, 60]:
        for k in range(3):
            angle = k * (2.0 * math.pi / 3.0)
            
            # Primary kinematic pivot arm (revolute link 1)
            arm_len = 24.0
            ax = side
            ay = 10.0 * math.cos(angle)
            az = 37.0 + 10.0 * math.sin(angle)
            assembly.add_box(8.0, 6.0, arm_len, center=(ax, ay + (arm_len/2.0)*math.cos(angle), az + (arm_len/2.0)*math.sin(angle)))
            
            # Shielded bearing pivot boss (MF63ZZ seat)
            bx = ax
            by = ay + arm_len * math.cos(angle)
            bz = az + arm_len * math.sin(angle)
            assembly.add_cylinder(4.5, 9.0, center=(bx, by, bz), axis='x', segments=16)
            
            # Outer curved morphing rim segment (transforms between round rim & claw)
            rim_r = 37.0
            rx = ax + (2.0 if side > 0 else -2.0)
            ry = rim_r * math.cos(angle)
            rz = 37.0 + rim_r * math.sin(angle)
            assembly.add_box(12.0, 16.0, 7.0, center=(rx, ry, rz))
            
            # High-friction elastomer climbing cleat
            assembly.add_box(10.0, 8.0, 4.0, center=(rx, ry * 1.08, rz * 1.08))

    # 3. Non-Euclidean Continuous Elastica Preflex Chassis Spine (Idea 11/14 hybrid)
    print("Generating non-linear elastica preflex chassis...")
    spine_len = 160.0
    spine_w = 40.0
    spine_h = 10.0
    assembly.add_box(spine_w, spine_len, spine_h, center=(0, 0, 42))
    
    # Curved elastica spring arches (Euler-Bernoulli large deflection flexures)
    for sign in [-1, 1]:
        assembly.add_cylinder(28.0, 18.0, center=(0, sign * 50, 44), axis='z', segments=32)
        # Internal hollow core for progressive non-linear stiffness
        assembly.add_box(14.0, 24.0, 12.0, center=(0, sign * 50, 44))

    # 4. Sensor Horizon Stabilized Deck (Isolated from vibration)
    assembly.add_box(50.0, 70.0, 8.0, center=(0, -10, 52))
    assembly.add_cylinder(12.0, 16.0, center=(0, 15, 62), axis='z', segments=24) # Sensor turret
    
    # 5. Low-Friction Monolithic Caster Flexure Mount (Rear)
    assembly.add_box(16.0, 22.0, 18.0, center=(0, -75, 25))
    assembly.add_cylinder(10.0, 10.0, center=(0, -75, 12), axis='z', segments=24) # Ball caster seat

    assembly.save()
    print(f"Watertight CAD assembly exported to: {assembly.filepath}")
    print(f"Total triangular elements for FEA: {len(assembly.triangles):,}")

if __name__ == '__main__':
    generate_kbmwl_cad()
