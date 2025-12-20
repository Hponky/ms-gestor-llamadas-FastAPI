# HAR-228 Voice-to-Voice AI Microservice

Este microservicio permite conversaciones de voz en tiempo real con una IA (Mistral/Devstral vía OpenRouter) utilizando WebRTC para baja latencia.

## 🚀 Características
- **Real-Time Voice-to-Voice**: Basado en `FastRTC` para manejo de WebRTC.
- **LLM**: OpenRouter (Configurado por defecto para `mistralai/devstral-2512:free`).
- **TTS**: `Edge-TTS` (Sintetizador neural gratuito de alta calidad).
- **VAD**: Detección de actividad de voz integrada para manejo de turnos.
- **Interrupciones**: La IA se detiene inmediatamente si detecta que el usuario empieza a hablar.

## 🛠 Instalación Local

### Requisitos
- Python 3.12+
- Docker (opcional)

### Configuración de Entorno
Crea un archivo `.env` basado en `.env.example`:
```bash
cp .env.example .env
```
Edita `.env` y añade tu `OPENROUTER_API_KEY`.

### Ejecución con Python
1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Iniciar el servidor:
   ```bash
   python -m src.main
   ```

### Ejecución con Docker
1. Construir la imagen:
   ```bash
   docker build -t har-228-voice-ai .
   ```
2. Ejecutar el contenedor:
   ```bash
   docker run -p 8000:8000 --env-file .env har-228-voice-ai
   ```

## 🖥 Uso
Una vez iniciado, accede a:
- **UI de Prueba**: `http://localhost:8000/conversation` (FastRTC provee una interfaz automática para probar micrófono y parlantes).
- **API Health**: `http://localhost:8000/`

## 🏗 Arquitectura
El proyecto sigue una **Arquitectura Hexagonal**:
- `src/domain`: Entidades e interfaces pura (Ports).
- `src/infrastructure`: Adaptadores para APIs externas (Adapters).
- `src/application`: Lógica de orquestación y VAD.
- `src/api`: Puntos de entrada y dependencias.
