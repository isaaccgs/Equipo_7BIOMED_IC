import cv2
import mediapipe as mp
import urllib.request
import os

MODEL_URL  = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
MODEL_PATH = "pose_landmarker_lite.task"

if not os.path.exists(MODEL_PATH):
    print("Descargando modelo...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

# Conexiones generales (resto del cuerpo)
CONNECTIONS = [
    (11, 13), (13, 15),  # brazo izquierdo
    (11, 12),            # hombros
    (23, 24),            # caderas
    (11, 23), (12, 24),  # torso
    (23, 25), (25, 27),  # pierna izquierda
    (24, 26), (26, 28),  # pierna derecha
]

# Brazo derecho: hombro(12) → codo(14) → muñeca(16)
ARM_CONNECTIONS = [
    (12, 14),
    (14, 16),
]
ARM_LANDMARKS = [12, 14, 16]  # puntos a resaltar


def draw_skeleton(frame, landmarks):
    h, w = frame.shape[:2]
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

    # Cuerpo en verde
    for a, b in CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (0, 255, 0), 2)
    for cx, cy in pts:
        cv2.circle(frame, (cx, cy), 4, (0, 100, 255), -1)

    # Brazo derecho en naranja
    for a, b in ARM_CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (0, 140, 255), 4)
    for idx in ARM_LANDMARKS:
        cv2.circle(frame, pts[idx], 8, (0, 140, 255), -1)


options = mp.tasks.vision.PoseLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_poses=1,
)

FPS = 30
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, FPS)

w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

writer = cv2.VideoWriter(
    "output.mp4",
    cv2.VideoWriter_fourcc(*"mp4v"),
    FPS, (w, h)
)

print("Grabando... q para detener")

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

        writer.write(frame)
        cv2.imshow("Skeleton — q para salir", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
writer.release()
cv2.destroyAllWindows()
print("Video guardado: output.mp4")