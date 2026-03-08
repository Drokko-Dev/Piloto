FROM python:3.11-slim

# Install system dependencies for MoviePy, ImageMagick, and Kokoro
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    libsndfile1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Relax ImageMagick security policy for TextClips (MoviePy needs this)
RUN sed -i 's/<policy domain="path" rights="none" pattern="@\*"/<!--<policy domain="path" rights="none" pattern="@\*"-->/' /etc/ImageMagick-6/policy.xml || true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
