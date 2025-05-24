from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from voxel_engine import estimate_trajectory_step, KalmanFilter3D
import threading, time, cv2, os, math, numpy as np, json

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

start_processing = False

# === Wczytaj dane kamer z JSON ===
with open('static/camera_data.json') as f:
    camera_data = json.load(f)

cameras = []
for cam in camera_data:
    pos = np.array([cam['location']['x'], cam['location']['y'], cam['location']['z']], dtype=np.float32)
    rx, ry, rz = cam['rotation_euler']['x'], cam['rotation_euler']['y'], cam['rotation_euler']['z']
    cx, cy, cz = map(math.cos, (rx, ry, rz))
    sx, sy, sz = map(math.sin, (rx, ry, rz))

    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float32)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float32)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float32)
    R = Rz @ Ry @ Rx
    fov_rad = math.radians(cam.get('fov', 60.0))
    cameras.append({"pos": pos, "rot": R, "fov_rad": fov_rad})

# === Globalny stan aplikacji ===
pos = [0.0, 0.0, 0.0]
last_pos = None
kf = KalmanFilter3D(dt=1.0)

@app.route('/')
def index():
    return render_template('index.html', videos=['cam0.mp4', 'cam1.mp4', 'cam2.mp4'])

@app.route("/start", methods=["POST"])
def start():
    global start_processing
    start_processing = True
    print("Rozpoczęto przetwarzanie")
    return jsonify({"status": "started"})

def background_loop():
    global pos, last_pos, start_processing

    # Przygotuj kamery
    caps, prev_grays, f_pix_vals = [], [], []
    for i, cam in enumerate(cameras):
        path = f"static/videos/cam{i}.mp4"
        cap = cv2.VideoCapture(path) if os.path.exists(path) else None
        caps.append(cap if cap and cap.isOpened() else None)

    for cam, cap in zip(cameras, caps):
        if cap:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            prev_grays.append(gray)
            f_pix_vals.append((w / 2.0) / math.tan(cam["fov_rad"] / 2.0))
        else:
            prev_grays.append(None)
            f_pix_vals.append(None)

    frame_idx = 0
    while True:
        if not start_processing:
            time.sleep(0.01)
            continue

        try:
            result = estimate_trajectory_step(cameras, caps, prev_grays, f_pix_vals, last_pos, kf)
        except Exception as e:
            print(f"Błąd w estimate_trajectory_step: {e}")
            time.sleep(0.033)
            continue

        if result:
            pos_new, last_pos, prev_grays = result
            if pos_new:
                pos[:] = list(pos_new)
                print(f"✅ Pozycja {frame_idx}: {pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}")
                socketio.emit('position', {'x': pos[0], 'y': pos[1], 'z': pos[2]}) # wysyłanie socketu
        else:
            print(f"⚠️ Klatka {frame_idx}: brak danych")

        frame_idx += 1
        if frame_idx >= 170:
            for cap in caps:
                if cap:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_idx = 0
            print("🔁 Reset wideo")

        time.sleep(1.0 / 60.0)  # ~60 FPS

# === Start wątku i serwera SocketIO ===
if __name__ == "__main__":
    threading.Thread(target=background_loop, daemon=True).start()
    socketio.run(app, debug=True)
