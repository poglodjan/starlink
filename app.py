from flask import Flask
from flask_socketio import SocketIO
import threading
import json
import time
from voxel_engine import get_frame_positions
import numpy as np
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

def get_camera_matrix(cam):
    import numpy as np
    import math
    rx, ry, rz = cam["rotation_euler"].values()
    cx, cy, cz = map(math.cos, (rx, ry, rz))
    sx, sy, sz = map(math.sin, (rx, ry, rz))
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float32)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float32)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float32)
    R = Rz @ Ry @ Rx
    pos = np.array(list(cam["location"].values()), dtype=np.float32)
    return {"rot": R, "pos": pos}

with open('static/camera_data.json') as f: # parametry kamer
    camera_data = json.load(f)
cameras = [get_camera_matrix(cam) for cam in camera_data]

def background_processing():
    # sprawdzanie i import videos
    cam0_path = "static/videos/cam0.mp4"
    cam1_path = "static/videos/cam1.mp4"
    if not os.path.exists(cam0_path):
        print("Nie znaleziono cam0.mp4")
        return
    if not os.path.exists(cam1_path):
        print("Nie znaleziono cam1.mp4")
        return

    gen = get_frame_positions(cameras, [cam0_path, cam1_path])

    while True:
        try:
            frame_idx, positions = next(gen)

            print(f"\nK {frame_idx}")
            if positions:
                for obj_id, pos in positions.items():
                    print(f"Obiekt {obj_id}: {np.round(pos, 2)}")
            else:
                print("Brak obiektów")

                # zapis jako frame , object_id , lisa pozycji dla object_id
            data = {
                "frame": frame_idx,
                "objects": {str(obj_id): list(np.round(pos, 2)) for obj_id, pos in positions.items()}
            }
            socketio.emit("frame_data", data) # tu wysylka danych
            time.sleep(0.02)

        except StopIteration:
            print("Koniec przetwarzania wideo.")
            break

        except Exception as e:
            print("Błąd w background_processing:", e)
            break

@socketio.on('connect')
def on_connect():
    print("React klient połączony.")

@app.route('/')
def index():
    return "Serwer Flask działa."

if __name__ == '__main__':
    #background_processing() # lub jak bez threding
    t = threading.Thread(target=background_processing)
    t.daemon = True
    t.start()
    socketio.run(app, host='0.0.0.0', port=5001)