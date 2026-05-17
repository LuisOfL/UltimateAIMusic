# 1. Ajustado a la versión exacta de tu entorno de Anaconda (Python 3.11)
FROM python:3.11-slim

# 2. Configurar variables de entorno esenciales
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TORCH_HOME=/app/.cache/torch \
    XDG_CACHE_HOME=/app/.cache \
    TTS_HOME=/app/.cache/tts

# 3. Instalar dependencias del sistema operativo
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# 4. Establecer el directorio de trabajo
WORKDIR /app

# 5. Copiar el archivo de requerimientos e instalar dependencias de Python
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copiar el resto del código del backend
COPY . .

# 7. Crear los directorios para persistencia de modelos y procesamiento temporal
RUN mkdir -p /app/.cache /app/separated /app/outputs

# 8. Exponer el puerto estándar de uvicorn
EXPOSE 8080

# 9. Comando para arrancar FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]