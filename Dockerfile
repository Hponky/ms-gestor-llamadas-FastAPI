# Usar una imagen base ligera de Python
FROM python:3.12-slim

# Evitar que Python genere archivos .pyc y asegurar que los logs se vean en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema, requirements y gunicorn en una sola capa
COPY app/requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn \
    && rm -rf /var/lib/apt/lists/*

# Copiar el resto del código del microservicio
COPY app/ .

# Exponer el puerto que usará FastAPI
EXPOSE 8000

# Comando para iniciar con Gunicorn y workers de Uvicorn para alta concurrencia
# (4 workers es un buen punto de partida, pero se puede ajustar según la CPU)
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "src.main:app"]
