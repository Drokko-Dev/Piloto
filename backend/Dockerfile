FROM python:3.11-slim

# 1. Dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    libsndfile1 \
    wget \
    bzip2 \
    espeak-ng \
    espeak-ng-data \
    libespeak-ng1 \
    && mkdir -p /usr/share \
    && ln -s /usr/lib/x86_64-linux-gnu/espeak-ng-data /usr/share/espeak-ng-data \
    && rm -rf /var/lib/apt/lists/*

# 2. Configuración de ImageMagick
RUN sed -i 's/<policy domain="path" rights="none" pattern="@\*"//' /etc/ImageMagick-6/policy.xml || true

# 3. Instalación de Piper
RUN wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz \
    && tar -xf piper_amd64.tar.gz \
    && mv piper/piper /usr/local/bin/ \
    && mv piper/lib* /usr/local/lib/ \
    && ldconfig \
    && rm -rf piper piper_amd64.tar.gz

WORKDIR /app

# 4. Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar código
COPY . .

# 6. Ejecutar backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]