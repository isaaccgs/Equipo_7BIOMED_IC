import cv2
import mediapipe as mp
import urllib.request
import os

MODEL_URL  = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
MODEL_PATH = "pose_landmarker_lite.task"

if not os.path.exists(MODEL_PATH):
    print("Descargando modelo...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

CONNECTIONS = [
    (11, 13), (13, 15),  # brazo izquierdo
    (12, 14), (14, 16),  # brazo derecho
    (11, 12),            # hombros
    (23, 24),            # caderas
    (11, 23), (12, 24),  # torso
    (23, 25), (25, 27),  # pierna izquierda
    (24, 26), (26, 28),  # pierna derecha
]

def draw_skeleton(frame, landmarks):
    h, w = frame.shape[:2]
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

    for a, b in CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (0, 255, 0), 2)

    for cx, cy in pts:
        cv2.circle(frame, (cx, cy), 4, (0, 100, 255), -1)


options = mp.tasks.vision.PoseLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_poses=1,
)

cap = cv2.VideoCapture(0)

with mp.tasks.vision.PoseLandmarker.create_from_options(options) as detector:
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result   = detector.detect_for_video(mp_image, frame_idx)
        frame_idx += 1

        if result.pose_landmarks:
            draw_skeleton(frame, result.pose_landmarks[0])

        cv2.imshow("Skeleton — q para salir", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()