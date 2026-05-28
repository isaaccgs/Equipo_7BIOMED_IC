import cv2
import mediapipe as mp
import math
import matplotlib.pyplot as plt 
from scipy.signal import savgol_filter

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def calcular_angulo(cadera, rodilla, tobillo):
    angulo_muslo = math.atan2(cadera[1] - rodilla[1], cadera[0] - rodilla[0])
    angulo_pantorrilla = math.atan2(tobillo[1] - rodilla[1], tobillo[0] - rodilla[0])
    
    radianes = angulo_muslo - angulo_pantorrilla
    angulo = abs(math.degrees(radianes))
    
    if angulo > 180.0:
        angulo = 360.0 - angulo
        
    return angulo

cap = cv2.VideoCapture("MARCHA_KEVINmp4.mp4")

ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('marcha_procesada.mp4', fourcc, fps, (ancho, alto))

with mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    angulo_anterior = None
    historico_angulos = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Procesamiento finalizado o archivo no encontrado.")
            break
        
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False 
        
        results = pose.process(image)
        
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        try:
            landmarks = results.pose_landmarks.landmark
            h, w, c = image.shape
            
            cadera = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, 
                      landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
            
            rodilla = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, 
                       landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
            
            tobillo = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x, 
                       landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
            
            angulo_rodilla = calcular_angulo(cadera, rodilla, tobillo)
            
            if angulo_anterior is not None:
                diferencia = abs(angulo_rodilla - angulo_anterior)
                if diferencia > 20.0:
                    angulo_rodilla = angulo_anterior # Se descarta la lectura y se mantiene el estado previo
            
            angulo_anterior = angulo_rodilla
            historico_angulos.append(angulo_rodilla)
            
            posicion_texto = tuple(int(val * dim) for val, dim in zip(rodilla, [w, h]))
            
            cv2.putText(image, str(int(angulo_rodilla)), 
                        posicion_texto, 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            
        except:
            pass 
        
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        cv2.imshow('Analisis de Marcha - MediaPipe', image)
        out.write(image)
        
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
out.release()
cv2.destroyAllWindows()
if len(historico_angulos) > 11: #
    # FILTRO "Savitzky-Golay" 
    historico_suavizado = savgol_filter(historico_angulos, window_length=11, polyorder=3)
    
    plt.figure(figsize=(10, 5))
    
    plt.plot(historico_angulos, label='Señal Cruda (MediaPipe)', color='lightgray', linestyle='--')
    
    plt.plot(historico_suavizado, label='Cinemática Suavizada (Filtro Savitzky-Golay)', color='blue', linewidth=2.5)
    
    plt.axhline(y=180, color='red', linestyle='--', label='Extensión Total (180°)')
    
    plt.title('Análisis Cinemático de la Marcha - Ángulo de Rodilla')
    plt.xlabel('Fotogramas (Tiempo)')
    plt.ylabel('Ángulo (Grados)')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)
    
    plt.show()
else:
    print("No se registraron suficientes datos para graficar.")