import os
import json
import base64
import sounddevice as sd
import threading
import numpy as np
from dotenv import load_dotenv
from websocket import WebSocketApp
import customtkinter as ctk
import random

# Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INSTRUCTIONS = os.getenv("PROMPT")

# URL del WebSocket
url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"

# Inicializar SoundDevice
stream = None
input_stream = None
running = True
pulse_running = False
pulse_line = None

# Parámetros de audio
FORMAT = "int16"
CHANNELS = 1
RATE = 24000
CHUNK = 2048
input_device_index = None

# Configurar el tema de customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Crear la ventana principal
root = ctk.CTk()
root.title("Demo de asistente - Realtime API OpenAI")
root.geometry("435x235")
root.resizable(False, False)

# Crear el canvas
canvas = ctk.CTkCanvas(root, width=600, height=300, bg="black", highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Inicializar las barras para el audio captado
num_bars = 50
bar_width = 10
spacing = 1
center_y_input = 75

bars_input = []

for i in range(num_bars):
    x = i * (bar_width + spacing)
    bar_input = canvas.create_line(x, center_y_input, x, center_y_input, fill="cyan", width=bar_width)
    bars_input.append(bar_input)

# Crear línea de pulso
center_y_output = 225
pulse_line = canvas.create_line(0, center_y_output, 600, center_y_output, fill="red", width=2)

def reset_bars(bars, center_y):
    for i in range(num_bars):
        x = i * (bar_width + spacing)
        canvas.coords(bars[i], x, center_y, x, center_y)

def update_visualization(audio_data=None):
    def process_audio(data, bars, center_y):
        if data is not None and data.size > 0:
            audio_np = np.frombuffer(data, dtype=np.int16)
            segment_size = max(len(audio_np) // num_bars, 1)
            amplitudes = [np.abs(audio_np[i * segment_size: (i + 1) * segment_size]).mean() for i in range(num_bars)]
            max_amplitude = 5000
            heights = [min(int((amp / max_amplitude) * 100), 100) for amp in amplitudes]
            for i, height in enumerate(heights):
                x = i * (bar_width + spacing)
                canvas.coords(bars[i], x, center_y - height, x, center_y + height)

    if audio_data is not None and audio_data.size > 0:
        process_audio(audio_data, bars_input, center_y_input)
    root.after(25, update_visualization)  # Actualizar cada 25 ms para mejorar la fluidez

def start_pulse_animation():
    global pulse_running
    pulse_running = True
    def animate():
        if pulse_running:
            y = center_y_output + random.randint(-20, 20)
            canvas.coords(pulse_line, 0, y, 600, y)
            root.after(100, animate)
    animate()

def stop_pulse_animation():
    global pulse_running
    pulse_running = False
    canvas.coords(pulse_line, 0, center_y_output, 600, center_y_output)

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

def capture_audio(ws):
    global input_stream, running
    running = True

    def audio_callback(indata, frames, time, status):
        if status:
            print(f"Error en el stream de entrada: {status}")
        encoded_audio = base64.b64encode(indata).decode("utf-8")
        audio_message = {
            "type": "input_audio_buffer.append",
            "audio": encoded_audio
        }
        ws.send(json.dumps(audio_message))
        update_visualization(audio_data=indata)
        # Vaciar el buffer de entrada
        indata.fill(0)

    input_stream = sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype=FORMAT, blocksize=CHUNK, callback=audio_callback)
    input_stream.start()

    print("Capturando audio en tiempo real. Habla ahora...")
    while running:
        sd.sleep(100)
    
    input_stream.stop()
    input_stream.close()
    ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
    ws.send(json.dumps({"type": "response.create"}))

def on_open(ws):
    print("Conectado al servidor de OpenAI.")
    prompt = {
        "type": "session.update",
        "session": {
            "modalities": ["text", "audio"],
            "instructions": INSTRUCTIONS,
            "voice": "ash",
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.8,
                "prefix_padding_ms": 200,
                "silence_duration_ms": 1000
            },
        }
    }
    ws.send(json.dumps(prompt))
    print("Evento de configuración de sesión enviado")

def on_message(ws, message):
    res = json.loads(message)
    print("Mensaje recibido del servidor:", res)
    
    if res["type"] == "session.updated":
        print("Configuración aplicada. Iniciando conversación")
        start_audio_stream()
        threading.Thread(target=capture_audio, args=(ws,), daemon=True).start()
    
    elif res["type"] == "response.audio.delta":
        start_pulse_animation()
        output_audio = np.frombuffer(base64.b64decode(res["delta"]), dtype=np.int16)
        if stream:
            stream.write(output_audio)
    
    elif res["type"] == "response.done":
        print("Respuesta entregada. Puedes seguir hablando...")
        reset_bars(bars_input, center_y_input)
        stop_pulse_animation()

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    global running
    print("Conexión terminada")
    stop_audio_stream()
    running = False

def close_app():
    global running
    running = False
    ws.close()
    root.destroy()

# Headers para auth
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "OpenAI-Beta": "realtime=v1"
}

ws = WebSocketApp(url, header=headers, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
threading.Thread(target=lambda: ws.run_forever()).start()
root.bind("<Escape>", lambda event: close_app())

update_visualization()
root.mainloop()
