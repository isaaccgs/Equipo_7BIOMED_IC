// =============================================================================
// ADC.c — Lectura del Conversor Analógico-Digital en ESP32
// =============================================================================
//
// DESCRIPCIÓN GENERAL
// -------------------
// Este programa corre en una placa ESP32. Su función es leer continuamente
// el voltaje presente en el pin GPIO34, convertirlo a un número digital
// (proceso llamado conversión ADC), y enviarlo por el puerto serial a la
// computadora en formato CSV (valores separados por coma).
//
// CONCEPTOS CLAVE ANTES DE LEER EL CÓDIGO
// ----------------------------------------
// • ADC (Analog-to-Digital Converter): convierte una señal analógica
//   (voltaje continuo) en un número entero que la computadora puede procesar.
//
// • Resolución de 12 bits: el ADC del ESP32 puede representar 2^12 = 4096
//   niveles distintos (0 a 4095). Cuantos más bits, más precisa la lectura.
//
// • Voltaje de referencia (3.3V): el ESP32 opera a 3.3V, por eso el voltaje
//   máximo que puede medir es 3.3V (no 5V como Arduino UNO).
//
// • Puerto Serial: canal de comunicación entre el ESP32 y la PC. Los datos
//   viajan como texto a través del cable USB.
//
// • Baud rate (115200): velocidad de transmisión en bits por segundo.
//   Emisor y receptor deben usar exactamente el mismo valor.
//
// =============================================================================

// Incluye la librería base de Arduino/ESP32. Proporciona funciones como
// Serial.begin(), analogRead(), delay(), etc. Sin este include el programa
// no compilaría porque esas funciones no estarían definidas.
#include <Arduino.h>

// -----------------------------------------------------------------------------
// DEFINICIÓN DE CONSTANTE
// -----------------------------------------------------------------------------
// #define crea una constante en tiempo de compilación: el preprocesador
// reemplaza cada aparición de "ADC_PIN" por "34" antes de compilar.
// Usar una constante con nombre (en vez de escribir 34 directamente en el
// código) hace el programa más fácil de modificar y entender.
//
// GPIO34 fue elegido porque en el ESP32 es un pin de "solo entrada" (input-only),
// lo que lo hace ideal para leer señales analógicas sin riesgo de dañar la placa.
#define ADC_PIN 34  // GPIO34 — pin analógico de solo entrada del ESP32

// -----------------------------------------------------------------------------
// FUNCIÓN setup()
// -----------------------------------------------------------------------------
// En Arduino/ESP32, setup() se ejecuta UNA SOLA VEZ al arrancar la placa
// (al conectarla o al presionar reset). Aquí se configura el hardware.
void setup() {

  // Inicia la comunicación serial a 115200 baudios.
  // Este número debe coincidir exactamente con el configurado en el receptor
  // (en nuestro caso, el script Python). Si no coinciden, los datos llegan
  // como caracteres basura (ilegibles).
  Serial.begin(115200);

  // Configura la resolución del ADC a 12 bits.
  // Esto significa que las lecturas estarán en el rango 0–4095:
  //   0    → 0.0 V  (voltaje mínimo)
  //   4095 → 3.3 V  (voltaje máximo)
  // El ESP32 soporta 9, 10, 11 y 12 bits. Más bits = más resolución,
  // pero también más ruido en la señal.
  analogReadResolution(12);  // Rango resultante: 0 a 4095
}

// -----------------------------------------------------------------------------
// FUNCIÓN loop()
// -----------------------------------------------------------------------------
// loop() se ejecuta INDEFINIDAMENTE después de setup(). Todo lo que quieras
// que el microcontrolador haga de forma continua va aquí. Es equivalente a
// un while(true) en C tradicional.
void loop() {

  // Lee el valor crudo (raw) del pin ADC_PIN (GPIO34).
  // El resultado es un entero entre 0 y 4095, proporcional al voltaje
  // presente en ese pin en el momento exacto de la lectura.
  // Ejemplo: si el pin está a 1.65V (mitad de 3.3V), raw ≈ 2047.
  int raw = analogRead(ADC_PIN);

  // Convierte el valor crudo a voltaje usando una regla de tres:
  //
  //   raw       voltage
  //   ----  =  --------
  //   4095       3.3V
  //
  // Despejando voltage:
  //   voltage = raw * (3.3 / 4095.0)
  //
  // Nota: se usa 4095.0 (con punto decimal) para forzar división en punto
  // flotante. Si escribiéramos solo 4095, C haría división entera y el
  // resultado sería siempre 0 (porque 3/4095 en enteros = 0).
  float voltage = raw * (3.3 / 4095.0);

  // Envía los datos por el puerto serial en formato CSV (Comma Separated Values):
  //   "<raw>,<voltage>\n"
  // Ejemplo de línea enviada: "2048,1.6500\n"
  //
  // Formato de printf:
  //   %d      → entero decimal (para 'raw')
  //   %.4f    → flotante con 4 decimales (para 'voltage')
  //   \n      → salto de línea, necesario para que el receptor sepa dónde
  //             termina cada lectura
  //
  // El script Python leerá estas líneas y las separará por la coma.
  Serial.printf("%d,%.4f\n", raw, voltage);

  // Pausa de 10 milisegundos antes de la siguiente lectura.
  // Esto da una frecuencia de muestreo de aproximadamente:
  //   1000 ms / 10 ms = 100 muestras por segundo (100 Hz)
  //
  // Sin este delay, el ESP32 enviaría datos tan rápido como puede
  // (~varios miles por segundo), saturando el puerto serial y la PC.
  delay(10);  // 10 ms → ~100 muestras/segundo
}
