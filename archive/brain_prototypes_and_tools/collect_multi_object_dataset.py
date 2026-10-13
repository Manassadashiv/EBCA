import os
import sys
import numpy as np
import cv2
import mujoco
import math
import random
import os as _os
_FILE_DIR = _os.path.dirname(_os.path.abspath(__file__))
BASE_DIR = _os.path.dirname(_FILE_DIR)


def project_to_camera(model, data, cam_id, world_pos, W, H):
    cam_pos = data.cam_xpos[cam_id]
    cam_mat = data.cam_xmat[cam_id].reshape(3, 3)
    
    rel_pos = world_pos - cam_pos
    
    x_c = np.dot(rel_pos, cam_mat[:, 0]) # right
    y_c = np.dot(rel_pos, cam_mat[:, 1]) # up
    z_c = -np.dot(rel_pos, cam_mat[:, 2]) # forward (distance)
    
    if z_c <= 0.02: # Behind camera
        return None
        
    fovy_rad = np.deg2rad(model.cam_fovy[cam_id])
    f = H / (2.0 * np.tan(fovy_rad / 2.0))
    
    u = W / 2.0 + (x_c / z_c) * f
    v = H / 2.0 - (y_c / z_c) * f
    
    return int(u), int(v)

def is_geom_visible(model, data, cam_id, geom_id):
    """Casts a ray from a forward-offset position to avoid self-collision and checks for wall/obstacle occlusion."""
    try:
        cam_pos = data.cam_xpos[cam_id]
        cam_mat = data.cam_xmat[cam_id].reshape(3, 3)
        cam_forward = -cam_mat[:, 2] # local forward direction of camera
        
        # Start the ray 0.15m forward to avoid hitting CARL's own head/camera mount
        ray_start = cam_pos + 0.15 * cam_forward
        
        geom_pos = data.geom_xpos[geom_id]
        dir_vec = geom_pos - ray_start
        dist = np.linalg.norm(dir_vec)
        if dist < 0.01:
            return True
            
        dir_vec = dir_vec / dist
        
        # Exclude the camera body from raycast intersections
        cam_body_id = model.cam_bodyid[cam_id]
        geomid_hit = np.array([-1], dtype=np.int32)
        hit_dist = mujoco.mj_ray(model, data, ray_start, dir_vec, None, 1, int(cam_body_id), geomid_hit)
        
        # If the ray hit an obstacle or wall closer than the target, it is occluded!
        if hit_dist >= 0 and hit_dist < (dist - 0.05):
            hit_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geomid_hit[0])
            if hit_name and ('wall' in hit_name or 'obstacle' in hit_name or 'floor' in hit_name or 'hazard' in hit_name):
                return False
        return True
    except Exception:
        return False

def get_geom_bbox(model, data, cam_id, geom_name, W, H):
    try:
        geom_id = model.geom(geom_name).id
        # First verify visual visibility to prevent labeling occluded/blocked geoms
        if not is_geom_visible(model, data, cam_id, geom_id):
            return None
    except Exception:
        return None

    geom_names = [geom_name]
    if geom_name == "predator":
        geom_names.append("predator_glow")
    elif geom_name == "obstacle":
        geom_names.append("obstacle_glow")
        
    points = []
    for g_name in geom_names:
        try:
            g_id = model.geom(g_name).id
            g_type = model.geom_type[g_id]
            pos = data.geom_xpos[g_id]
            mat = data.geom_xmat[g_id].reshape(3, 3)
            size = model.geom_size[g_id]
            
            if g_type == mujoco.mjtGeom.mjGEOM_SPHERE:
                r = size[0]
                for offset in [np.array([r,0,0]), np.array([-r,0,0]), np.array([0,r,0]), np.array([0,-r,0]), np.array([0,0,r]), np.array([0,0,-r])]:
                    points.append(pos + offset)
            elif g_type == mujoco.mjtGeom.mjGEOM_BOX:
                sx, sy, sz = size
                for dx in [-sx, sx]:
                    for dy in [-sy, sy]:
                        for dz in [-sz, sz]:
                            points.append(pos + np.dot(mat, np.array([dx, dy, dz])))
            elif g_type == mujoco.mjtGeom.mjGEOM_CYLINDER:
                r, h = size[0], size[1]
                for theta in np.linspace(0, 2*np.pi, 8, endpoint=False):
                    for dz in [-h, h]:
                        points.append(pos + np.dot(mat, np.array([r*math.cos(theta), r*math.sin(theta), dz])))
            else:
                points.append(pos)
        except Exception:
            pass
            
    pixels = []
    for p in points:
        pix = project_to_camera(model, data, cam_id, p, W, H)
        if pix is not None:
            pixels.append(pix)
            
    if not pixels:
        return None
        
    pixels = np.array(pixels)
    u_min, v_min = np.min(pixels, axis=0)
    u_max, v_max = np.max(pixels, axis=0)
    
    # Clip to image boundary
    u_min = max(0, min(W - 1, u_min))
    u_max = max(0, min(W - 1, u_max))
    v_min = max(0, min(H - 1, v_min))
    v_max = max(0, min(H - 1, v_max))
    
    if (u_max - u_min) < 2 or (v_max - v_min) < 2:
        return None
        
    return u_min, v_min, u_max, v_max

def generate_multi_object_dataset():
    xml_path = os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")
    model = mujoco.MjModel.from_xml_path(xml_path)
    data = mujoco.MjData(model)
    
    base_dir = os.path.join(BASE_DIR, "memory", "multi_object_dataset")
    os.makedirs(os.path.join(base_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "labels"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "debug_images"), exist_ok=True)
    
    cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, "eye_cam")
    W, H = 160, 120
    renderer = mujoco.Renderer(model, height=H, width=W)
    
    categories = [
        ("FOOD", "food", 0),
        ("OBSTACLE", "obstacle", 1),
        ("PREDATOR", "predator", 2)
    ]
    
    total_samples = 1200
    q_addr = int(model.joint("spatial_identity").qposadr[0])
    
    print(f"[MULTI-DATASET] Generating {total_samples} Multi-Object Wall-E scenes...")
    
    for img_idx in range(total_samples):
        # 1. Position CARL randomly inside the 10x10 arena
        x_off = np.random.uniform(-3.5, 3.5)
        y_off = np.random.uniform(-3.5, 3.5)
        
        data.qpos[q_addr : q_addr+3] = [x_off, y_off, 0.05]
        
        yaw = np.random.uniform(-np.pi, np.pi)
        hp = yaw / 2.0
        data.qpos[q_addr+3 : q_addr+7] = [math.cos(hp), 0.0, 0.0, math.sin(hp)]
        data.qpos[q_addr+7:] = 0.0 # reset neck/wheels/arms
        
        # Park the sliding hazard cube outside the arena (X = 99.0)
        data.qpos[0] = 99.0
        
        # Park all target geoms far away initially
        model.geom_pos[model.geom("food").id] = [99.0, 99.0, 0.12]
        model.geom_pos[model.geom("obstacle").id] = [99.0, 99.0, 0.45]
        model.geom_pos[model.geom("obstacle_glow").id] = [99.0, 99.0, 0.904]
        model.geom_pos[model.geom("predator").id] = [99.0, 99.0, 0.15]
        model.geom_pos[model.geom("predator_glow").id] = [99.0, 99.0, 0.46]
        
        # Decide how many objects are visible in this scene (0 to 3)
        num_objects = random.choices([0, 1, 2, 3], weights=[0.1, 0.4, 0.4, 0.1], k=1)[0]
        
        active_targets = random.sample(categories, min(num_objects, len(categories)))
        bboxes_to_save = []
        
        # Place active targets in front of CARL
        for idx, (cat_name, geom_name, class_id) in enumerate(active_targets):
            dist = np.random.uniform(0.9, 2.2)
            angle_offsets = [-0.25, 0.0, 0.25]
            rel_angle = angle_offsets[idx] + np.random.uniform(-0.1, 0.1)
            
            t_x = x_off + dist * math.cos(yaw + rel_angle)
            t_y = y_off + dist * math.sin(yaw + rel_angle)
            
            # Keep targets inside the arena boundary walls (bounds are +/- 4.7m)
            t_x = max(-4.7, min(4.7, t_x))
            t_y = max(-4.7, min(4.7, t_y))
            
            if geom_name == "food":
                model.geom_pos[model.geom("food").id] = [t_x, t_y, 0.12]
            elif geom_name == "obstacle":
                model.geom_pos[model.geom("obstacle").id] = [t_x, t_y, 0.45]
                model.geom_pos[model.geom("obstacle_glow").id] = [t_x, t_y, 0.904]
            elif geom_name == "predator":
                model.geom_pos[model.geom("predator").id] = [t_x, t_y, 0.15]
                model.geom_pos[model.geom("predator_glow").id] = [t_x, t_y, 0.46]
                
        # 2. Step physics to update transforms
        for _ in range(10):
            mujoco.mj_step(model, data)
            
        # 3. Render image from camera
        renderer.update_scene(data, camera="eye_cam")
        img = renderer.render()
        
        # 4. Extract bounding boxes (with visibility validation)
        for cat_name, geom_name, class_id in active_targets:
            bbox = get_geom_bbox(model, data, cam_id, geom_name, W, H)
            if bbox is not None:
                bboxes_to_save.append((class_id, cat_name, bbox))
                
        # 5. Save image and labels
        img_filename = f"img_{img_idx:04d}.jpg"
        label_filename = f"img_{img_idx:04d}.txt"
        
        img_path = os.path.join(base_dir, "images", img_filename)
        label_path = os.path.join(base_dir, "labels", label_filename)
        debug_path = os.path.join(base_dir, "debug_images", img_filename)
        
        bgr_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(img_path, bgr_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        dbg_img = bgr_img.copy() if bboxes_to_save else None
        
        with open(label_path, "w") as lf:
            for class_id, cat_name, bbox in bboxes_to_save:
                u_min, v_min, u_max, v_max = bbox
                x_center = ((u_min + u_max) / 2.0) / W
                y_center = ((v_min + v_max) / 2.0) / H
                bbox_width = (u_max - u_min) / W
                bbox_height = (v_max - v_min) / H
                lf.write(f"{class_id} {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}\n")
                
                if dbg_img is not None:
                    cv2.rectangle(dbg_img, (u_min, v_min), (u_max, v_max), (0, 255, 0), 2)
                    cv2.putText(dbg_img, cat_name, (u_min, max(12, v_min - 4)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                                
        if dbg_img is not None:
            cv2.imwrite(debug_path, dbg_img)
            
        if (img_idx + 1) % 200 == 0:
            print(f"Generated {img_idx + 1}/{total_samples} multi-object samples.")
            
    print(f"Successfully generated {total_samples} multi-object vision training samples in {base_dir}!")

if __name__ == '__main__':
    generate_multi_object_dataset()
