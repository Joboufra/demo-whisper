import sounddevice as sd
import base64
import json
import numpy as np
import time
from ui import reset_bars

# Variables de control de audio
FORMAT = "int16"
CHANNELS = 1
RATE = 24000
CHUNK = 1024

# Intervalo de envío (evitar envíos muy frecuentes)
SEND_INTERVAL = 0.10  # 500 ms
last_send_time = 0

# Referencias de stream
stream = None
input_stream = None

# Banderas de control
running = True

def start_audio_stream():
    global stream
    if stream is None:
        stream = sd.OutputStream(samplerate=RATE, channels=CHANNELS, dtype=FORMAT, blocksize=CHUNK)
        stream.start()

def stop_audio_stream():
    global stream
    if stream:
        stream.stop()
        stream.close()
        stream = None

def capture_audio(ws, canvas, bars_input, root):
    """
    Hilo que captura audio desde el micrófono y lo envía al servidor.
    """
    global input_stream, running, last_send_time
    running = True

    def audio_callback(indata, frames, callback_time, status):
        global last_send_time
        if status:
            print(f"Error en el stream de entrada: {status}")

        current_time = time.time()
        if current_time - last_send_time >= SEND_INTERVAL:
            encoded_audio = base64.b64encode(indata).decode("utf-8")
            audio_message = {
                "type": "input_audio_buffer.append",
                "audio": encoded_audio
            }
            try:
                ws.send(json.dumps(audio_message))
                last_send_time = current_time
            except Exception as e:
                print(f"Error enviando datos: {e}")

        # Actualiza barras de audio en la UI (cada callback)
        update_visualization(canvas, bars_input, indata, root)

    input_stream = sd.InputStream(
        samplerate=RATE,
        channels=CHANNELS,
        dtype=FORMAT,
        blocksize=CHUNK,
        callback=audio_callback
    )
    input_stream.start()

    print(" 🎤 Capturando audio en tiempo real. Habla ahora...")

    while running:
        sd.sleep(100)

    input_stream.stop()
    input_stream.close()
    ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
    ws.send(json.dumps({"type": "response.create"}))

def update_visualization(canvas, bars, audio_data, root):
    """
    Procesa audio y actualiza gráficamente las barras de entrada.
    Programa una siguiente llamada usando root.after.
    """
    if audio_data is not None and audio_data.size > 0:
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        segment_size = max(len(audio_np) // len(bars), 1)
        max_amplitude = 5000
        for i in range(len(bars)):
            segment = audio_np[i * segment_size : (i + 1) * segment_size]
            amp = np.abs(segment).mean()
            height = min(int((amp / max_amplitude) * 100), 100)
            x = i * 11  # BAR_WIDTH + SPACING = 10 + 1
            canvas.coords(bars[i], x, 75 - height, x, 75 + height)

    root.after(25, lambda: None)

def stop_input_capture():
    """
    Detiene la captura y resetea todo.
    """
    global running, input_stream
    running = False
    if input_stream:
        input_stream.stop()
        input_stream.close()
        input_stream = None
