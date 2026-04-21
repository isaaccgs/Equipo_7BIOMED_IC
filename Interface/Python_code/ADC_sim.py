# =============================================================================
# ADC_sim.py — Visualización en tiempo real de datos del ADC del ESP32
# =============================================================================
#
# DESCRIPCIÓN GENERAL
# -------------------
# Este script se conecta al ESP32 a través del puerto serial (USB) y grafica
# en tiempo real los datos que la placa envía: el valor crudo del ADC y su
# equivalente en voltaje.
#
# FLUJO DE DATOS
# --------------
#   ESP32 (ADC.c)  →  USB/Serial  →  Este script  →  Gráfica en pantalla
#
# La gráfica muestra dos señales en tiempo real:
#   • Arriba  : valor crudo del ADC (0 a 4095, entero)
#   • Abajo   : voltaje calculado (0.0 a 3.3 V, flotante)
#
# REQUISITOS
# ----------
# Antes de correr este script, instala las librerías necesarias.
# Ver README.md para instrucciones de instalación con pip, conda o uv.
#
# =============================================================================

# -----------------------------------------------------------------------------
# IMPORTACIONES (LIBRERÍAS)
# -----------------------------------------------------------------------------

# 'serial' viene del paquete pyserial. Permite abrir y leer el puerto serial
# (USB) de la computadora, que es el canal por donde el ESP32 envía datos.
import serial

# 'sys' es una librería estándar de Python (no hay que instalarla).
# La usamos para llamar sys.exit(1) cuando ocurre un error crítico al abrir
# el puerto serial. El argumento 1 indica al sistema operativo que el programa
# terminó con error (0 = éxito, cualquier otro número = error).
import sys

# 'matplotlib.pyplot' es la librería de graficación más popular en Python.
# La importamos con el alias 'plt' por convención (es más corto de escribir).
# Se usa para crear y actualizar las gráficas en tiempo real.
import matplotlib.pyplot as plt

# 'deque' (pronunciado "deck") viene de "double-ended queue" (cola de dos
# extremos). Es como una lista, pero con la capacidad de limitarse a un
# número máximo de elementos (maxlen). Cuando está llena y agregas un
# elemento nuevo al final, automáticamente descarta el más antiguo del inicio.
# Esto implementa la "ventana deslizante" de las últimas MAX_POINTS muestras.
from collections import deque


# -----------------------------------------------------------------------------
# CONFIGURACIÓN GLOBAL (CONSTANTES)
# -----------------------------------------------------------------------------

# Puerto serial donde está conectado el ESP32.
# IMPORTANTE: este valor cambia según tu computadora y sistema operativo.
# Ver README.md para saber cómo encontrar tu puerto.
# Ejemplos comunes:
#   macOS/Linux : "/dev/cu.wchusbserial10"  o  "/dev/ttyUSB0"
#   Windows     : "COM3"  o  "COM4"  (varía según el dispositivo)
PORT = "/dev/cu.wchusbserial10"  # <-- ¡Cambia esto por tu puerto serial!

# Velocidad de comunicación en bits por segundo (baudios).
# DEBE ser idéntica a la configurada en Serial.begin() del código C.
# Si no coinciden, los datos llegan corruptos (caracteres extraños).
BAUD = 115200

# Número máximo de puntos visibles en la gráfica al mismo tiempo.
# Con 500 puntos y 100 muestras/segundo, la ventana visible cubre 5 segundos.
# Aumentar este número muestra más historia pero puede hacer la gráfica más lenta.
MAX_POINTS = 500


# -----------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------------------------------------------------------
def main():

    # -----------------------------------------------------------------------
    # APERTURA DEL PUERTO SERIAL
    # -----------------------------------------------------------------------
    # Intentamos abrir la conexión serial con el ESP32.
    # Usamos un bloque try/except para manejar el caso en que el puerto
    # no exista o esté siendo usado por otro programa (ej: Arduino IDE).
    try:
        # Crea un objeto Serial que representa la conexión con el ESP32.
        #   PORT    : ruta del dispositivo (definida arriba)
        #   BAUD    : velocidad de comunicación
        #   timeout : si no llegan datos en 1 segundo, readline() regresa
        #             sin esperar indefinidamente (evita bloqueos)
        ser = serial.Serial(PORT, BAUD, timeout=1)

        # Limpia cualquier dato residual que hubiera en el buffer del puerto.
        # Sin esto, podríamos leer datos viejos o incompletos de una conexión
        # anterior, lo que causaría errores al parsear la primera línea.
        ser.reset_input_buffer()

        print(f"Conectado a {PORT}")

    except serial.SerialException as e:
        # Si el puerto no se puede abrir (no existe, está ocupado, etc.),
        # mostramos el error y terminamos el programa con código de error 1.
        print(f"Error al abrir el puerto serial: {e}")
        print("Verifica que el ESP32 esté conectado y que el puerto sea correcto.")
        sys.exit(1)  # Termina el programa indicando que hubo un error

    # -----------------------------------------------------------------------
    # ESTRUCTURAS DE DATOS (VENTANA DESLIZANTE)
    # -----------------------------------------------------------------------
    # Creamos dos deques para almacenar las últimas MAX_POINTS muestras.
    # Cuando el deque está lleno y se agrega un elemento nuevo, el más
    # antiguo se descarta automáticamente — esto implementa la "ventana
    # deslizante" que hace que la gráfica se desplace hacia la derecha.
    raw_data  = deque(maxlen=MAX_POINTS)  # Valores crudos: enteros 0-4095
    volt_data = deque(maxlen=MAX_POINTS)  # Voltajes: flotantes 0.0-3.3

    # -----------------------------------------------------------------------
    # CONFIGURACIÓN DE LA GRÁFICA
    # -----------------------------------------------------------------------
    # Activa el modo interactivo de matplotlib. En modo normal, plt.show()
    # bloquea el programa hasta que el usuario cierra la ventana. En modo
    # interactivo (ion = interactive on), la gráfica se actualiza sin bloquearse,
    # lo que permite actualizarla dentro de un bucle while.
    plt.ion()

    # Crea la ventana (fig) con dos subgráficas (ax1 arriba, ax2 abajo).
    #   subplots(2, 1) : 2 filas, 1 columna → una sobre la otra
    #   figsize=(10, 6): ancho 10 pulgadas, alto 6 pulgadas
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

    # Título principal que aparece sobre ambas gráficas
    fig.suptitle("ESP32 ADC — Pin 34 (ruido)")

    # --- Gráfica superior: valor crudo del ADC ---
    # ax1.plot([],[]) crea una línea vacía. La guardamos en 'line1' para
    # poder actualizar sus datos después sin redibujar toda la gráfica.
    line1, = ax1.plot([], [], color="cyan", linewidth=0.8)
    ax1.set_ylabel("Raw (0-4095)")   # Etiqueta del eje Y
    ax1.set_ylim(0, 4095)            # Límites fijos del eje Y (no escala automática)
    ax1.set_xlim(0, MAX_POINTS)      # Muestra MAX_POINTS muestras en el eje X
    ax1.grid(True, alpha=0.3)        # Cuadrícula tenue (alpha=0.3 = 30% opacidad)

    # --- Gráfica inferior: voltaje calculado ---
    line2, = ax2.plot([], [], color="orange", linewidth=0.8)
    ax2.set_ylabel("Voltaje (V)")
    ax2.set_ylim(0, 3.3)             # Límites: 0V a 3.3V (rango del ESP32)
    ax2.set_xlim(0, MAX_POINTS)
    ax2.set_xlabel("Muestras")       # Etiqueta del eje X (solo en la gráfica de abajo)
    ax2.grid(True, alpha=0.3)

    # Ajusta automáticamente los márgenes para que las gráficas no se encimen
    plt.tight_layout()

    # -----------------------------------------------------------------------
    # BUCLE PRINCIPAL DE LECTURA Y GRAFICACIÓN
    # -----------------------------------------------------------------------
    # Este bucle corre mientras la ventana de la gráfica esté abierta.
    # plt.fignum_exists(fig.number) devuelve False cuando el usuario cierra
    # la ventana, lo que termina el bucle limpiamente.
    try:
        while plt.fignum_exists(fig.number):

            # Lee una línea completa del puerto serial (hasta el '\n').
            # readline() espera hasta recibir el '\n' o hasta que expire el timeout.
            # .decode("utf-8") convierte los bytes recibidos a texto legible.
            #   errors="replace" : si hay bytes inválidos, los reemplaza con '?'
            #                      en vez de lanzar una excepción.
            # .strip() elimina espacios, '\n' y '\r' al inicio y al final.
            line = ser.readline().decode("utf-8", errors="replace").strip()

            # Si la línea está vacía (timeout o línea en blanco), la ignoramos
            # y volvemos al inicio del bucle para intentar leer de nuevo.
            if not line:
                continue

            # --- Parseo del CSV ---
            # Intentamos separar la línea en sus dos valores.
            # Formato esperado: "2048,1.6500"
            try:
                # split(",") divide la cadena por la coma → ["2048", "1.6500"]
                # La asignación múltiple desempaca los dos valores en variables
                raw_str, volt_str = line.split(",")

                # Convertimos los strings a sus tipos numéricos correspondientes
                # y los agregamos al final de cada deque.
                # Si el deque ya está lleno (500 elementos), el más antiguo se elimina.
                raw_data.append(int(raw_str))       # int("2048") → 2048
                volt_data.append(float(volt_str))   # float("1.6500") → 1.65

                # Imprime en consola para depuración (útil al inicio para verificar)
                print(f"raw={raw_str}  volt={volt_str}")

            except ValueError:
                # Si la línea no tiene el formato esperado (ej: "ERROR\n", línea
                # de boot del ESP32, etc.), se ignora y se continúa con la siguiente.
                print(f"Línea con formato inválido, se ignora: '{line}'")
                continue

            # --- Actualización de la gráfica ---
            # Creamos el eje X: simplemente los índices 0, 1, 2, ..., N-1
            # donde N es el número de puntos actualmente en el deque.
            x = range(len(raw_data))

            # Actualizamos los datos de las líneas sin redibujar todo el canvas.
            # set_data() es más eficiente que limpiar y volver a graficar.
            line1.set_data(x, raw_data)
            line2.set_data(x, volt_data)

            # draw_idle() marca el canvas como "necesita redibujo" pero no
            # lo fuerza inmediatamente — el sistema operativo lo dibuja cuando
            # pueda (más eficiente que draw() que es síncrono).
            fig.canvas.draw_idle()

            # flush_events() procesa los eventos pendientes de la interfaz
            # gráfica (mouse, teclado, redimensionado de ventana). Sin esto,
            # la ventana podría parecer congelada.
            fig.canvas.flush_events()

            # Pausa brevísima para ceder el control al sistema de graficación.
            # 0.01 segundos = 10 ms. Necesario para que matplotlib pueda
            # procesar eventos y actualizar la ventana visualmente.
            plt.pause(0.01)

    except KeyboardInterrupt:
        # El usuario presionó Ctrl+C en la terminal → salida limpia
        print("\nInterrumpido por el usuario. Cerrando conexión...")

    finally:
        # El bloque 'finally' siempre se ejecuta, independientemente de cómo
        # terminó el bucle (error, Ctrl+C, o cierre de ventana).
        # Garantiza que los recursos se liberen correctamente.
        ser.close()    # Cierra el puerto serial (libera el recurso del SO)
        plt.close()    # Cierra la ventana de la gráfica


# -----------------------------------------------------------------------------
# PUNTO DE ENTRADA
# -----------------------------------------------------------------------------
# Esta condición verifica si el script se está ejecutando directamente
# (python ADC_sim.py) en lugar de ser importado como módulo por otro script.
# Es una convención estándar de Python: solo llama a main() si este archivo
# es el programa principal, no si es importado como librería.
if __name__ == "__main__":
    main()
