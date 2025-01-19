# Asistente de Voz en Tiempo Real con Realtime API de OpenAI

Este proyecto es una demo de un asistente que permite mantener una conversación por voz en tiempo real utilizando la Realtime API de OpenAI con el modelo `gpt-4o-realtime-preview-2024-10-01`.

![image](https://github.com/user-attachments/assets/9bea5ea3-9465-44bd-a2cb-46c884614fb9)


## Características

- **Conversación en tiempo real** con reconocimiento de voz y generación de respuestas, haciendo uso de prompts customizados.
- **Visualización de audio** captado y recibido en tiempo real mediante `customtkinter`.
- **Integración con WebSocket** para una comunicación eficiente con la API de OpenAI.

## Requisitos

- **Python 3.8 o superior**
- **Dependencias**:
   - `pyaudio`
   - `websocket-client`
   - `numpy`
   - `customtkinter`
   - `python-dotenv`

## Instalación

1. **Clona el repositorio**:  
   Clona el proyecto desde GitHub y accede a la carpeta del repositorio:  
   `git clone https://github.com/joboufra/demo-whisper.git`  
   `cd demo-whisper`
2. **Instala las dependencias**:  
   Utiliza `pip` para instalar las dependencias necesarias del archivo `requirements.txt`:  
   `pip install -r requirements.txt`
3. __Configura las variables de entorno__:  
   Crea un archivo `.env` en la raíz del proyecto y agrega tu clave de API y el prompt inicial:  
   `OPENAI_API_KEY=tu_clave_de_api`  
   `PROMPT=Tu prompt inicial`
4. **Ejecuta la aplicación**:  
   Inicia el asistente ejecutando el archivo principal:  
   `python main.py`

## Uso

1. La aplicación mostrará una interfaz donde podrás hablar y recibir respuestas en tiempo real.
2. La barra superior muestra el audio captado por el micrófono.
3. La barra inferior muestra el audio generado por la IA.
4. **Cerrar la aplicación**: Presiona `ESC` para cerrar la aplicación.

## Funcionalidad del Código

1. **Captura de audio** con `PyAudio` y envío a la API de OpenAI a través de WebSocket.
2. **Recepción del audio generado** por la IA y reproducción en tiempo real.
3. **Visualización dinámica** de las ondas de audio en la interfaz gráfica.
4. **Gestión de sesión y eventos** de WebSocket para comunicación fluida.
