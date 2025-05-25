import cv2
import numpy as np
import math
import json
from numba import njit
from scipy.spatial.distance import pdist, squareform

MOTION_THRESHOLD = 10
MIN_AREA = 100
MERGE_DISTANCE = 15.0
MAX_ASSOCIATION_DIST = 30.0


@njit
def intersection_point(o1, d1, o2, d2):
    I = np.eye(3, dtype=np.float32)
    A = (I - np.outer(d1, d1)) + (I - np.outer(d2, d2))
    b = (I - np.outer(d1, d1)) @ o1 + (I - np.outer(d2, d2)) @ o2
    return np.linalg.solve(A, b)

def merge_close_points(points, threshold):
    if len(points) <= 1:
        return points
    points_np = np.array(points)
    dists = squareform(pdist(points_np))
    visited = set()
    clusters = []
    for i in range(len(points)):
        if i in visited:
            continue
        cluster = [points_np[i]]
        visited.add(i)
        for j in range(i + 1, len(points)):
            if j not in visited and np.linalg.norm(points_np[i] - points_np[j]) < threshold:
                cluster.append(points_np[j])
                visited.add(j)
        clusters.append(np.mean(cluster, axis=0))
    return clusters

class KalmanFilter3D:
    def __init__(self):
        self.dt = 1.0
        self.x = np.zeros((6, 1))
        self.P = np.eye(6) * 500
        self.F = np.eye(6)
        for i in range(3):
            self.F[i, i + 3] = self.dt
        self.H = np.zeros((3, 6))
        self.H[:, :3] = np.eye(3)
        self.Q = np.eye(6) * 0.1
        self.R = np.eye(3) * 10

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update(self, z):
        z = np.array(z, dtype=np.float32).reshape((3, 1))
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x += K @ y
        self.P = (np.eye(6) - K @ self.H) @ self.P
        return self.x[:3].flatten()

def get_frame_positions(cameras, cam_paths):
    cap0 = cv2.VideoCapture(cam_paths[0])
    cap1 = cv2.VideoCapture(cam_paths[1])
    prev_gray0, prev_gray1 = None, None
    frame_idx = 0

    kalman_filters = {}
    last_positions = {}
    next_id = 0

    while True:
        ret0, frame0 = cap0.read()
        ret1, frame1 = cap1.read()
        if not ret0 or not ret1:
            break

        gray0 = cv2.cvtColor(frame0, cv2.COLOR_BGR2GRAY)
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)

        if prev_gray0 is None or prev_gray1 is None:
            prev_gray0 = gray0
            prev_gray1 = gray1
            continue

        def detect(gray, prev_gray):
            diff = cv2.absdiff(prev_gray, gray)
            _, thresh = cv2.threshold(diff, MOTION_THRESHOLD, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            return [cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) > MIN_AREA]

        boxes0 = detect(gray0, prev_gray0)
        boxes1 = detect(gray1, prev_gray1)
        prev_gray0, prev_gray1 = gray0, gray1

        shape = gray0.shape
        f_pix = shape[1] / (2 * math.tan(math.radians(60) / 2))
        points_3d = []

        for box0 in boxes0:
            u0, v0 = box0[0] + box0[2] // 2, box0[1] + box0[3] // 2
            x0 = u0 - shape[1] / 2
            y0 = -(v0 - shape[0] / 2)
            ray0 = np.array([x0, y0, -f_pix], dtype=np.float32)
            ray0 /= np.linalg.norm(ray0)
            world_ray0 = cameras[0]["rot"] @ ray0

            for box1 in boxes1:
                u1, v1 = box1[0] + box1[2] // 2, box1[1] + box1[3] // 2
                x1 = u1 - shape[1] / 2
                y1 = -(v1 - shape[0] / 2)
                ray1 = np.array([x1, y1, -f_pix], dtype=np.float32)
                ray1 /= np.linalg.norm(ray1)
                world_ray1 = cameras[1]["rot"] @ ray1
                try:
                    pt = intersection_point(cameras[0]["pos"], world_ray0, cameras[1]["pos"], world_ray1)
                    points_3d.append(pt)
                except:
                    continue

        merged = merge_close_points(points_3d, threshold=MERGE_DISTANCE)

        updated_positions = {}
        used_ids = set()

        for pt in merged:
            pt = np.array(pt)
            matched_id = None
            min_dist = MAX_ASSOCIATION_DIST

            for obj_id, last_pos in last_positions.items():
                if obj_id in used_ids:
                    continue
                dist = np.linalg.norm(pt - last_pos)
                if dist < min_dist:
                    min_dist = dist
                    matched_id = obj_id

            if matched_id is None:
                matched_id = next_id
                kalman_filters[matched_id] = KalmanFilter3D()
                next_id += 1

            kf = kalman_filters[matched_id]
            kf.predict()
            smoothed = kf.update(pt)
            updated_positions[matched_id] = smoothed
            used_ids.add(matched_id)

        last_positions = updated_positions
        yield frame_idx, updated_positions
        frame_idx += 1

    cap0.release()
    cap1.release()
