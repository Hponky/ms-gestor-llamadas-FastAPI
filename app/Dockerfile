FROM python:3.12-slim

# Instalar dependencias de sistema para audio
RUN apt-get update && apt-get install -y \
    gcc \
    portaudio19-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Exponer puerto para FastAPI
EXPOSE 8000

# Comando de ejecución
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
