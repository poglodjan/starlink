from flask import Flask, render_template, jsonify
from voxel_engine import estimate_trajectory_step, KalmanFilter3D
import threading
import time
import cv2
import os
import math
import numpy as np
import json

app = Flask(__name__)

# === Inicjalizacja kamer z camera_data.json ===
with open('static/camera_data.json', 'r') as f:
    camera_data = json.load(f)

cameras = []
for cam in camera_data:
    pos = np.array([cam['location']['x'], cam['location']['y'], cam['location']['z']], dtype=np.float32)
    rx, ry, rz = cam['rotation_euler']['x'], cam['rotation_euler']['y'], cam['rotation_euler']['z']
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float32)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float32)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float32)
    R = Rz @ Ry @ Rx
    fov_rad = math.radians(cam.get('fov', 60.0))
    cameras.append({"pos": pos, "rot": R, "fov_rad": fov_rad})

# === Globalne zmienne ===
latest_trajectory = []
last_pos = None
frame_idx = 1
kf = KalmanFilter3D(dt=1.0)

# === Aktualizacja trajektorii w tle ===
def background_updater():
    global latest_trajectory, last_pos, frame_idx, kf
    print("▶️ Uruchamiam background_updater...")

    caps = []
    for i in range(len(cameras)):
        path = f"static/videos/cam{i}.mp4"
        cap = cv2.VideoCapture(path) if os.path.exists(path) else None
        caps.append(cap if cap and cap.isOpened() else None)

    prev_grays = []
    f_pix_vals = []

    for cam, cap in zip(cameras, caps):
        if cap is None:
            prev_grays.append(None)
            f_pix_vals.append(None)
            continue
        ret, frame = cap.read()
        if not ret:
            prev_grays.append(None)
            f_pix_vals.append(None)
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        prev_grays.append(gray)
        f_pix_vals.append((w / 2.0) / math.tan(cam["fov_rad"] / 2.0))

    while True:
        result = estimate_trajectory_step(
    cameras, caps, prev_grays, f_pix_vals, last_pos, kf
        )

        if result is None:
            print(f"Frame {frame_idx}: brak danych – pomijam")
            frame_idx += 1
            time.sleep(0.1)
            continue

        pos, last_pos, prev_grays = result

        if pos is None:
            print(f"Frame {frame_idx}: brak pozycji – pomijam")
            frame_idx += 1
            time.sleep(0.1)
            continue

        latest_trajectory.append(pos)
        print(f"Frame {frame_idx}: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
        frame_idx += 1
        time.sleep(0.033)

# === Routing ===
@app.route('/')
def index():
    video_files = ['cam0.mp4', 'cam1.mp4', 'cam2.mp4', 'cam3.mp4']
    return render_template('index.html', videos=video_files)

@app.route('/trajectory')
def full_trajectory():
    return jsonify(latest_trajectory)

@app.route('/trajectory/latest')
def latest_point():
    return jsonify(latest_trajectory[-1]) if latest_trajectory else jsonify(None)

if __name__ == '__main__':
    print("🔄 Startuję wątek aktualizacji trajektorii...")
    threading.Thread(target=background_updater, daemon=True).start()
    app.run(debug=True, use_reloader=False)