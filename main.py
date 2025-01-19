import threading
from websocket_manager import create_websocket
from ui import create_main_window, run_app, close_app
from dotenv import load_dotenv

load_dotenv()  # Para que se lean OPENAI_API_KEY y PROMPT del .env

def main():
    # Crea la ventana y sus elementos gráficos
    root, canvas, bars_input, pulse_line = create_main_window(
        title="Demo de asistente - Realtime API OpenAI",
        geometry="435x235",
        close_callback=None  # Se ajusta después
    )

    # Crea el WebSocket, pasando referencias al canvas y demás
    ws = create_websocket(canvas, bars_input, pulse_line, root)

    # Asocia el cierre ordenado de la app al evento <Escape>
    root.bind("<Escape>", lambda _: close_app(ws, root))

    # Ejecuta el WebSocket en un thread separado
    threading.Thread(target=lambda: ws.run_forever(), daemon=True).start()

    # Inicia el bucle principal de la interfaz
    run_app(root)

if __name__ == "__main__":
    main()
