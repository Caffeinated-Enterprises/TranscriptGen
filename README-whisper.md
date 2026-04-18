# Whisper Transcription Service

This service automatically transcribes all media files in the downloads folder using OpenAI's Whisper-large model with GPU acceleration.

## Features

- **Recursive Media Discovery**: Finds all video and audio files in downloads directory
- **GPU Acceleration**: Uses up to 2 GPUs simultaneously for parallel transcription
- **Folder Structure Preservation**: Maintains exact folder structure in transcripts
- **Markdown Output**: Saves transcripts as formatted markdown files with timestamps
- **Video Support**: Automatically extracts audio from video files using ffmpeg
- **Resume Capability**: Skips already transcribed files

## Usage

### Build and Run

```bash
# Build the whisper service
docker-compose build whisper-transcriber

# Run the transcription service
docker-compose up whisper-transcriber

# Or run both services together
docker-compose up
```

### Environment Variables

- `DOWNLOADS_DIR`: Source directory for media files (default: `/app/downloads`)
- `TRANSCRIPTS_DIR`: Output directory for transcripts (default: `/app/transcripts`)
- `WHISPER_MODEL`: Whisper model size (default: `large`)

## Supported Formats

**Video**: mp4, avi, mov, mkv, wmv, flv, webm
**Audio**: mp3, wav, flac, aac, ogg, m4a, wma

## Output Structure

Transcripts are saved in `/app/transcripts` with the same folder structure as the source files:

```
downloads/
├── folder1/
│   ├── video1.mp4
│   └── audio1.mp3
└── folder2/
    └── video2.mkv

transcripts/
├── folder1/
│   ├── video1.md
│   └── audio1.md
└── folder2/
    └── video2.md
```

## Transcript Format

Each markdown file contains:
- File metadata (source, timestamp, model, GPU)
- Full transcript text
- Timestamped segments

## GPU Requirements

- Requires NVIDIA GPU with CUDA support
- Automatically detects available GPUs
- Uses up to 2 GPUs simultaneously
- Each GPU runs its own Whisper instance

## Manual Execution

```bash
# Run transcription manually
docker-compose run --rm whisper-transcriber

# With custom model
docker-compose run --rm -e WHISPER_MODEL=medium whisper-transcriber
```
