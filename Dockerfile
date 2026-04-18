# Python + FFmpeg (required for yt-dlp audio extraction / remux)
FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY download.py download_audios.py download_playlists.py main.py ./

ENV OUTPUT_DIR=/app/downloads

RUN mkdir -p /app/downloads

# Grouped playlists from main.py -> downloads/<group>/<date>/...
ENTRYPOINT ["python", "-u", "main.py"]
