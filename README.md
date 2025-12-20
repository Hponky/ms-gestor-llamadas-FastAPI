# HAR-228 Text-to-Voice AI Microservice

Microservicio avanzado diseñado para transformar texto en voz en tiempo real. Utiliza un modelo de lenguaje (LLM) para interpretar la entrada y un motor de síntesis (TTS) para generar audio fluido en formato MP3.

## 🚀 Características Principales
- **Inteligencia Real**: Procesa el texto a través de Mistral AI (vía OpenRouter) para generar respuestas coherentes.
- **Síntesis de Voz Fluida**: Utiliza Edge-TTS para una voz natural en español (es-MX-JorgeNeural).
- **Streaming de Audio**: El audio se entrega mediante *StreamingResponse*, permitiendo la reproducción inmediata mientras se genera.
- **CORS Habilitado**: Configurado para integrarse fácilmente con cualquier frontend moderno.
- **Limpieza Automática**: Filtra emojis y caracteres especiales para garantizar la estabilidad del motor de voz.
- **Arquitectura Hexagonal**: Estructura modular que separa la lógica de negocio de los proveedores externos.

## 🛠️ Requisitos
- **Python 3.12+**
- **FFmpeg** (Opcional, para procesamiento avanzado de audio)
- **OpenRouter API Key**

---

## 💻 Instalación y Configuración

1. **Clonar e instalar dependencias**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r app/requirements.txt
   ```

2. **Variables de Entorno**:
   Crea un archivo `.env` en la carpeta `app/` basándote en `.env.example`:
   ```env
   OPENROUTER_API_KEY=tu_clave_aqui
   OPENROUTER_MODEL=mistralai/devstral-2512:free
   TTS_PROVIDER=edge_tts
   ```

---

## 🏃 Ejecución

Desde la raíz del proyecto:
```powershell
$env:PYTHONPATH="app"; .\venv\Scripts\python.exe -m src.main
```
El servidor estará disponible en `http://localhost:8000`.

---

## 🧪 Métodos de Prueba

### 1. Prueba Directa en Navegador (Recomendado para Audio)
La forma más rápida de verificar que el audio se escucha correctamente es usar el método GET:
- Abre: `http://localhost:8000/chat?text=Hola HAR-228, dime que el sistema funciona correctamente`

### 2. Swagger UI (Documentación Interactiva)
Para ver todos los detalles técnicos y probar el endpoint POST:
- Ve a: `http://localhost:8000/docs`

### 3. Integración vía API (POST)
Endpoint: `POST /chat`
Cuerpo (JSON):
```json
{
  "text": "Hola, ¿cuál es tu función principal?"
}
```

---

## 🐋 Despliegue con Docker (Alta Concurrencia)
Para producción o entornos de nube, se recomienda usar el contenedor Docker que ya viene pre-configurado con **Gunicorn**:

```powershell
# 1. Construir la imagen
docker build -t har228-service .

# 2. Correr el contenedor
docker run -p 8000:8000 --env-file app/.env har228-service
```

---

## 🛠️ Escalabilidad (Futuros LLMs)
El microservicio está diseñado siguiendo el principio de inversión de dependencias. Para añadir un nuevo proveedor (ej. Gemini o OpenAI directo):
1. Crea un nuevo adaptador en `app/src/infrastructure/llm/`.
2. Implementa la interfaz `ILLMProvider`.
3. Regístralo en `app/src/api/dependencies.py`.
4. Cambia `LLM_PROVIDER` en tu `.env`.

---

## 🏗️ Estructura de Capas
- **Domain**: Define las interfaces (`ILLMProvider`, `ITTSProvider`) y entidades del sistema.
- **Application**: Orquesta el flujo entre el LLM y el TTS.
- **Infrastructure**: Implementa los adaptadores reales para OpenRouter y Edge-TTS.
- **API**: Expone los endpoints REST usando FastAPI.

---

## 🛠️ Herramientas de Calidad (Enterprise Ready)

### 📈 Logs Persistentes
El sistema genera logs avanzados con **Structlog**. En producción, los logs se guardan en la carpeta `logs/app.log` con rotación automática (10MB) para evitar llenar el disco.

### 🧪 Tests Automatizados
Para verificar la lógica de orquestación sin gastar créditos de OpenAI/Mistral:
```powershell
# Ejecutar tests unitarios (con mocks)
$env:PYTHONPATH="app"; pytest tests/test_orchestrator.py
```

### 🤖 CI/CD (GitHub Actions)
Se ha incluido un flujo de trabajo en `.github/workflows/ci.yml` que valida automáticamente tu código en cada `push` o `pull request`.
