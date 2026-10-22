# Grabby Video Downloader in un container: Python 3.12 + ffmpeg + yt-dlp.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py downloader.py registro.py ./
COPY static ./static

# Dentro il container ascolta su tutte le interfacce; i file vanno in /downloads.
ENV HOST=0.0.0.0 \
    GRABBY_IN_CONTAINER=1 \
    PORT=8000 \
    DOWNLOAD_DIR=/downloads \
    PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "app.py"]
