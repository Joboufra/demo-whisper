import customtkinter as ctk
from customtkinter import CTkCanvas
import random

# Parámetros para las barras
NUM_BARS = 50
BAR_WIDTH = 10
SPACING = 1

# Alturas bases
CENTER_Y_INPUT = 75
CENTER_Y_OUTPUT = 225

def create_main_window(title, geometry, close_callback):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    root = ctk.CTk()
    root.title(title)
    root.geometry(geometry)
    root.resizable(False, False)

    # Canvas
    canvas = CTkCanvas(root, width=600, height=300, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # Barras de audio de entrada
    bars_input = []
    for i in range(NUM_BARS):
        x = i * (BAR_WIDTH + SPACING)
        bar_line = canvas.create_line(x, CENTER_Y_INPUT, x, CENTER_Y_INPUT, fill="cyan", width=BAR_WIDTH)
        bars_input.append(bar_line)

    # Línea de pulso (audio de salida)
    pulse_line = canvas.create_line(0, CENTER_Y_OUTPUT, 600, CENTER_Y_OUTPUT, fill="red", width=2)

    # Si se pasa una función de cierre, la vinculamos
    if close_callback:
        root.protocol("WM_DELETE_WINDOW", close_callback)

    return root, canvas, bars_input, pulse_line

def reset_bars(canvas, bars):
    for i, bar in enumerate(bars):
        x = i * (BAR_WIDTH + SPACING)
        canvas.coords(bar, x, CENTER_Y_INPUT, x, CENTER_Y_INPUT)

def run_app(root):
    root.mainloop()

def close_app(ws, root):
    # Cierra WebSocket y ventana
    ws.close()
    root.destroy()

def start_pulse_animation(root, canvas, pulse_line, running_flag):
    # Animación de pulso en la línea roja
    def animate():
        if running_flag[0]:  # running_flag es mutable (lista)
            y = CENTER_Y_OUTPUT + random.randint(-20, 20)
            canvas.coords(pulse_line, 0, y, 600, y)
            root.after(100, animate)
    animate()

def stop_pulse_animation(canvas, pulse_line, running_flag):
    running_flag[0] = False
    canvas.coords(pulse_line, 0, CENTER_Y_OUTPUT, 600, CENTER_Y_OUTPUT)
