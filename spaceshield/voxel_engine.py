# analytic_trajectory_estimation.py (wersja zwracająca 1 punkt w czasie rzeczywistym)
import cv2
import math
import json
import numpy as np
import os
from numba import njit

@njit
def intersection_points(origins, directions):
    M = origins.shape[0]
    A = np.zeros((3, 3), dtype=np.float32)
    b = np.zeros(3, dtype=np.float32)
    for i in range(M):
        d = directions[i]
        o = origins[i]
        I = np.eye(3, dtype=np.float32) - np.outer(d, d)
        A += I
        b += I @ o
    pos = np.linalg.solve(A, b)
    return pos

class KalmanFilter3D:
    def __init__(self, dt=1.0):
        self.dt = dt
        self.x = np.zeros((6, 1))
        self.P = np.eye(6) * 500
        self.F = np.eye(6)
        for i in range(3):
            self.F[i, i + 3] = dt
        self.H = np.zeros((3, 6))
        self.H[:, :3] = np.eye(3)
        self.Q = np.eye(6) * 0.1
        self.R = np.eye(3) * 25

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update(self, z):
        z = np.array(z, dtype=np.float32).reshape((3, 1))
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        I = np.eye(6)
        self.P = (I - K @ self.H) @ self.P
        return self.x[:3].flatten()

def estimate_trajectory_step(cameras, caps, prev_grays, f_pix_vals, last_pos, kf=None):
    all_dirs = []
    all_origins = []
    valid_cam_indices = []

    for i, (cam, cap) in enumerate(zip(cameras, caps)):
        if i == 2:
            continue
        if cap is None or prev_grays[i] is None:
            continue
        ret, frame = cap.read()
        if not ret:
            continue
        curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(curr_gray, prev_grays[i])
        mask = diff > 2
        coords = np.argwhere(mask)
        if coords.shape[0] == 0:
            print(f"---- Kamera {i} została odrzucona (brak ruchu)")
            prev_grays[i] = curr_gray
            continue
        prev_grays[i] = curr_gray
        pix_vals = diff[coords[:, 0], coords[:, 1]].astype(np.float32)
        top_idx = np.argmax(pix_vals)
        v, u = coords[top_idx]

        x = u - curr_gray.shape[1] / 2.0
        y = -(v - curr_gray.shape[0] / 2.0)
        z = -f_pix_vals[i]
        ray = np.array([x, y, z], dtype=np.float32)
        ray /= np.linalg.norm(ray)
        world_dir = cam["rot"] @ ray
        world_dir /= np.linalg.norm(world_dir)

        all_dirs.append(world_dir)
        all_origins.append(cam["pos"])
        valid_cam_indices.append(i)

    if len(all_dirs) >= 2:
        dirs_np = np.array(all_dirs, dtype=np.float32)
        origs_np = np.array(all_origins, dtype=np.float32)
        est_pos = intersection_points(origs_np, dirs_np)

        if last_pos is not None:
            jump = np.linalg.norm(est_pos - last_pos)
            if jump > 20.0:
                est_pos = last_pos + (est_pos - last_pos) * 0.3

        if kf:
            kf.predict()
            smoothed = kf.update(est_pos)
            return tuple(smoothed), smoothed, prev_grays
        else:
            return tuple(est_pos), est_pos, prev_grays

    return None, last_pos, prev_grays