import os
import json
import base64
import pyaudio
import threading
import numpy as np
from dotenv import load_dotenv
from websocket import WebSocketApp
import customtkinter as ctk

#Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INSTRUCTIONS = os.getenv("PROMPT")

#URL del WebSocket
url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"

#Inicializar PyAudio
p = pyaudio.PyAudio()
stream = None
input_stream = None
running = True

#Parámetros de audio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24200
CHUNK = 1024
input_device_index = None

#Configurar el tema de customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

#Crear la ventana principal
root = ctk.CTk()
root.title("Demo de asistente - Realtime API OpenAI")
root.geometry("435x235")

#Crear el canvas
canvas = ctk.CTkCanvas(root, width=600, height=300, bg="black", highlightthickness=0)
canvas.pack(fill="both", expand=True)

#Inicializar las barras para el audio captado y el audio recibido
num_bars = 50
bar_width = 10
spacing = 1
center_y_input = 75
center_y_output = 225

bars_input = []
bars_output = []

for i in range(num_bars):
    x = i * (bar_width + spacing)
    bar_input = canvas.create_line(x, center_y_input, x, center_y_input, fill="cyan", width=bar_width)
    bar_output = canvas.create_line(x, center_y_output, x, center_y_output, fill="lime", width=bar_width)
    bars_input.append(bar_input)
    bars_output.append(bar_output)

#Búfer para el audio recibido
output_buffer = bytearray()

def update_visualization(audio_data=None, output_data=None):
    def process_audio(data, bars, center_y):
        if data is not None:
            audio_np = np.frombuffer(data, dtype=np.int16)
            segment_size = max(len(audio_np) // num_bars, 1)
            amplitudes = [np.abs(audio_np[i * segment_size: (i + 1) * segment_size]).mean() for i in range(num_bars)]
            max_amplitude = 5000
            heights = [min(int((amp / max_amplitude) * 100), 100) for amp in amplitudes]
            for i, height in enumerate(heights):
                x = i * (bar_width + spacing)
                canvas.coords(bars[i], x, center_y - height, x, center_y + height)

    if audio_data:
        process_audio(audio_data, bars_input, center_y_input)
    if output_data:
        process_audio(output_data, bars_output, center_y_output)
    root.after(25, update_visualization)  # Actualizar cada 25 ms para mejorar la fluidez

def start_audio_stream():
    global stream
    if stream is None:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True
        )

def stop_audio_stream():
    global stream
    if stream:
        stream.stop_stream()
        stream.close()
        stream = None

def capture_audio(ws):
    global input_stream, running
    input_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=input_device_index,
        frames_per_buffer=CHUNK
    )

    print("Capturando audio en tiempo real. Habla ahora...")
    running = True
    
    while running:
        try:
            data = input_stream.read(CHUNK, exception_on_overflow=False)
            encoded_audio = base64.b64encode(data).decode("utf-8")
            audio_message = {
                "type": "input_audio_buffer.append",
                "audio": encoded_audio
            }
            ws.send(json.dumps(audio_message))
            
            update_visualization(audio_data=data)
        except Exception as e:
            print(f"Error al capturar audio: {e}")
            break
    
    input_stream.stop_stream()
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
                "threshold": 0.6,
                "prefix_padding_ms": 200,
                "silence_duration_ms": 1000
            },
        }
    }
    ws.send(json.dumps(prompt))
    print("Evento de configuración de sesión enviado")

def on_message(ws, message):
    global output_buffer
    res = json.loads(message)
    print("Mensaje recibido del servidor:", res)
    
    if res["type"] == "session.updated":
        print("Configuración aplicada. Iniciando conversación")
        threading.Thread(target=capture_audio, args=(ws,), daemon=True).start()
    
    elif res["type"] == "response.audio.delta":
        output_audio = base64.b64decode(res["delta"])
        output_buffer.extend(output_audio)
        start_audio_stream()
        while len(output_buffer) >= CHUNK:
            stream.write(output_buffer[:CHUNK])
            output_buffer = output_buffer[CHUNK:]
        update_visualization(output_data=output_audio)
    
    elif res["type"] == "response.done":
        print("Respuesta entregada. Puedes seguir hablando...")
        stop_audio_stream()
        update_visualization()

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    global running
    print("Conexión terminada")
    stop_audio_stream()
    running = False
    p.terminate()

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