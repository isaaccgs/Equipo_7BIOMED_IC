"""
skeleton_recorder.py
====================
- ESPACIO  : iniciar / detener grabación
- Q        : salir

Al grabar genera:
    output.mp4  — video con skeleton
    emg.csv     — señal EMG (dummy por ahora)
"""

import csv
import os
import time
import threading
import urllib.request

import cv2
import mediapipe as mp
import numpy as np

# ---------------------------------------------------------------------------
# Modelo MediaPipe
# ---------------------------------------------------------------------------
MODEL_URL  = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
MODEL_PATH = "pose_landmarker_lite.task"

if not os.path.exists(MODEL_PATH):
    print("Descargando modelo...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

# ---------------------------------------------------------------------------
# Skeleton
# ---------------------------------------------------------------------------
CONNECTIONS = [
    (11, 13), (13, 15),  # brazo izquierdo
    (11, 12),            # hombros
    (23, 24),            # caderas
    (11, 23), (12, 24),  # torso
    (23, 25), (25, 27),  # pierna izquierda
    (24, 26), (26, 28),  # pierna derecha
]
ARM_CONNECTIONS = [(12, 14), (14, 16)]
ARM_LANDMARKS   = [12, 14, 16]

def draw_skeleton(frame, landmarks):
    h, w = frame.shape[:2]
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

    for a, b in CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (0, 255, 0), 2)
    for cx, cy in pts:
        cv2.circle(frame, (cx, cy), 4, (0, 100, 255), -1)

    for a, b in ARM_CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (0, 140, 255), 4)
    for idx in ARM_LANDMARKS:
        cv2.circle(frame, pts[idx], 8, (0, 140, 255), -1)

# ---------------------------------------------------------------------------
# EMG dummy — ¡ALUMNOS! reemplazar con lectura serial real
# ---------------------------------------------------------------------------
emg_buffer: list[tuple[float, float]] = []
emg_running = False
emg_lock    = threading.Lock()

def emg_dummy_thread():
    """
    Simula señal EMG a 1000 Hz.
    Reemplazar este loop con lectura del puerto serial:
        line = ser.readline().decode().strip()
        ts, val = parse(line)
    """
    fs     = 1000
    period = 1.0 / fs
    t      = 0.0

    while emg_running:
        noise  = np.random.normal(0, 10)
        burst  = 200 * np.sin(2 * np.pi * 120 * t) if (t % 2.0) < 0.5 else 0.0
        sample = noise + burst

        with emg_lock:
            emg_buffer.append((t, sample))

        t += period
        time.sleep(period)

# ---------------------------------------------------------------------------
# Panel EMG dibujado con OpenCV
# ---------------------------------------------------------------------------
PLOT_H  = 150           # altura del panel en píxeles
PLOT_BG = (20, 20, 35)
WINDOW  = 2000          # últimas N muestras visibles (~2s a 1000 Hz)

def draw_emg_panel(width: int) -> np.ndarray:
    panel = np.full((PLOT_H, width, 3), PLOT_BG, dtype=np.uint8)
    mid   = PLOT_H // 2

    # Línea de referencia
    cv2.line(panel, (0, mid), (width, mid), (50, 50, 70), 1)

    with emg_lock:
        sig = np.array([v for _, v in emg_buffer[-WINDOW:]], dtype=float)

    if len(sig) < 2:
        cv2.putText(panel, "Esperando señal EMG...", (10, mid + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 120, 120), 1)
        return panel

    # Normalizar a píxeles
    y_min, y_max = -400.0, 400.0
    xs = np.linspace(0, width - 1, len(sig)).astype(int)
    ys = (mid - sig / (y_max - y_min) * (PLOT_H - 20)).astype(int)
    ys = np.clip(ys, 2, PLOT_H - 2)

    pts = np.stack([xs, ys], axis=1).reshape(-1, 1, 2)
    cv2.polylines(panel, [pts], False, (0, 191, 255), 1, cv2.LINE_AA)

    cv2.putText(panel, "EMG (mV)", (8, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 191, 255), 1, cv2.LINE_AA)
    cv2.putText(panel, f"{sig[-1]:.1f} mV", (width - 85, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1, cv2.LINE_AA)

    return panel

# ---------------------------------------------------------------------------
# HUD sobre el frame de video
# ---------------------------------------------------------------------------
def draw_hud(frame, recording: bool, n_samples: int):
    h, w = frame.shape[:2]
    if recording:
        if int(time.time() * 2) % 2 == 0:
            cv2.circle(frame, (w - 30, 24), 10, (0, 0, 220), -1)
        cv2.putText(frame, "REC", (w - 75, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 220), 2, cv2.LINE_AA)
        cv2.putText(frame, f"EMG: {n_samples} muestras", (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 1, cv2.LINE_AA)
    else:
        cv2.putText(frame, "ESPACIO para grabar  |  Q para salir", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

# ---------------------------------------------------------------------------
# Guardar EMG
# ---------------------------------------------------------------------------
def save_emg():
    with emg_lock:
        rows = list(emg_buffer)
    with open("emg.csv", "w", newline="") as f:
        csv.writer(f).writerows([["timestamp_s", "emg_mV"]] + rows)
    print(f"   emg.csv  — {len(rows)} muestras guardadas")
    return len(rows)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global emg_running

    options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_poses=1,
    )

    FPS = 30
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, FPS)
    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    recording  = False
    writer     = None
    emg_thread = None

    with mp.tasks.vision.PoseLandmarker.create_from_options(options) as detector:
        frame_idx = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # --- Pose ---
            rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result   = detector.detect_for_video(mp_image, frame_idx)
            frame_idx += 1

            if result.pose_landmarks:
                draw_skeleton(frame, result.pose_landmarks[0])

            # --- HUD ---
            with emg_lock:
                n = len(emg_buffer)
            draw_hud(frame, recording, n)

            # --- Canvas: video + panel EMG ---
            emg_panel = draw_emg_panel(fw)
            canvas    = np.vstack([frame, emg_panel])

            # --- Grabar solo el frame (sin el panel) ---
            if recording and writer:
                writer.write(frame)

            cv2.imshow("Skeleton Recorder", canvas)

            # --- Teclado ---
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                if recording:
                    recording = False
                    emg_running = False
                    if emg_thread:
                        emg_thread.join(timeout=2)
                    writer.release()
                    writer = None
                    save_emg()
                    print("   output.mp4  — video guardado")
                break

            elif key == ord(" "):
                if not recording:
                    recording = True
                    writer = cv2.VideoWriter(
                        "output.mp4",
                        cv2.VideoWriter_fourcc(*"mp4v"),
                        FPS, (fw, fh)
                    )
                    with emg_lock:
                        emg_buffer.clear()
                    emg_running = True
                    emg_thread  = threading.Thread(target=emg_dummy_thread, daemon=True)
                    emg_thread.start()
                    print("⏺  Grabando...")

                else:
                    recording = False
                    emg_running = False
                    if emg_thread:
                        emg_thread.join(timeout=2)
                    writer.release()
                    writer = None
                    save_emg()
                    print("⏹  Listo. output.mp4 guardado")

    emg_running = False
    if writer:
        writer.release()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()