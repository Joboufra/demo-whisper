import os
import json
import numpy as np
import base64
from websocket import WebSocketApp
from dotenv import load_dotenv
import threading

import audio_manager
from ui import start_pulse_animation, stop_pulse_animation, reset_bars

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INSTRUCTIONS = os.getenv("PROMPT")

url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"

# Flag mutable para animación de pulso
pulse_running_flag = [False]

def create_websocket(canvas, bars_input, pulse_line, root):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1"
    }

    ws = WebSocketApp(
        url,
        header=headers,
        on_open=lambda ws: on_open(ws),
        on_message=lambda ws, msg: on_message(ws, msg, canvas, bars_input, pulse_line, root),
        on_error=on_error,
        on_close=on_close
    )
    return ws

def on_open(ws):
    print(" 🌐 Conectado al servidor de OpenAI.")
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
    print(" ⚙️  Evento de configuración de sesión enviado")

def on_message(ws, message, canvas, bars_input, pulse_line, root):
    res = json.loads(message)
    print(" 🔊 Mensaje recibido")

    if res["type"] == "session.updated":
        print(" ⚙️  Configuración aplicada")
        audio_manager.start_audio_stream()
        threading.Thread(
            target=audio_manager.capture_audio,
            args=(ws, canvas, bars_input, root),
            daemon=True
        ).start()

    elif res["type"] == "response.audio.delta":
        # Inicia animación de pulso
        if not pulse_running_flag[0]:
            pulse_running_flag[0] = True
            start_pulse_animation(root, canvas, pulse_line, pulse_running_flag)

        output_audio = np.frombuffer(base64.b64decode(res["delta"]), dtype=np.int16)
        if audio_manager.stream:
            audio_manager.stream.write(output_audio)

    elif res["type"] == "response.done":
        print(" 🟢 Respuesta entregada. Puedes hablar de nuevo.")
        reset_bars(canvas, bars_input)
        stop_pulse_animation(canvas, pulse_line, pulse_running_flag)

def on_error(ws, error):
    print(f" ❌ Error en WebSocket: {error}")

def on_close(ws, close_status_code, close_msg):
    print(" 🔴 Conexión terminada")
    audio_manager.stop_audio_stream()
    audio_manager.stop_input_capture()