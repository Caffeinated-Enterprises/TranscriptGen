#!/usr/bin/env python3
import os
import sys
import glob
import subprocess
import threading
import queue
import time
from pathlib import Path
import torch
import whisper

SUPPORTED_EXTENSIONS = {
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm',
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'
}

class WhisperTranscriber:
    def __init__(
        self,
        downloads_dir="/app/downloads",
        transcripts_dir="/app/transcripts",
        model_name="large",
        allowed_top_level_dirs=None,
        use_multi_gpu=False,
    ):
        self.downloads_dir = Path(downloads_dir)
        self.transcripts_dir = Path(transcripts_dir)
        self.model_name = model_name
        # None = no filter (all under downloads). Otherwise only paths like downloads/<name>/...
        self.allowed_top_level_dirs = allowed_top_level_dirs
        self.use_multi_gpu = use_multi_gpu
        self.device_count = torch.cuda.device_count()
        self.transcription_queue = queue.Queue()
        self.models = {}
        # One lock per loaded device so single-GPU runs are serialized; multi-GPU can run in parallel per device.
        self._gpu_locks = {}

        print(f"Found {self.device_count} GPU(s)")
        if self.device_count == 0:
            print("Loading Whisper on CPU...")
            self.models[0] = whisper.load_model(self.model_name, device="cpu")
            self._gpu_locks[0] = threading.Lock()
            print("Model loaded on CPU")
        else:
            # Default: one GPU + one worker (stable). Set WHISPER_MULTI_GPU=1 for two models on cuda:0,1.
            num_to_load = min(self.device_count, 2) if self.use_multi_gpu else 1
            if not self.use_multi_gpu and self.device_count > 1:
                print(
                    "Using a single GPU for transcription (set WHISPER_MULTI_GPU=1 to use up to 2 GPUs; "
                    "multi-GPU + threads can cause CUDA unknown errors)."
                )
            for gpu_id in range(num_to_load):
                device = f"cuda:{gpu_id}"
                print(f"Loading Whisper model on {device}...")
                self.models[gpu_id] = whisper.load_model(self.model_name, device=device)
                self._gpu_locks[gpu_id] = threading.Lock()
                print(f"Model loaded on {device}")
    
    def find_media_files(self, directory):
        """Recursively find all media files in directory"""
        media_files = []
        directory = Path(directory)
        
        for ext in SUPPORTED_EXTENSIONS:
            pattern = f"**/*{ext}"
            files = glob.glob(str(directory / pattern), recursive=True)
            media_files.extend(files)
        
        return media_files

    def _is_under_allowed_group(self, file_path: Path) -> bool:
        """If ``allowed_top_level_dirs`` is set, file must live under downloads/<dir>/... for one of those dirs."""
        if not self.allowed_top_level_dirs:
            return True
        try:
            resolved = Path(file_path).resolve()
            base = self.downloads_dir.resolve()
            rel = resolved.relative_to(base)
        except ValueError:
            return False
        if not rel.parts:
            return False
        return rel.parts[0] in self.allowed_top_level_dirs

    def find_media_files_filtered(self, directory):
        """Like ``find_media_files`` but restricted to allowed top-level group folders when configured."""
        all_files = self.find_media_files(directory)
        if not self.allowed_top_level_dirs:
            return all_files
        return [f for f in all_files if self._is_under_allowed_group(Path(f))]

    def get_relative_path(self, file_path, base_dir):
        """Get relative path from base directory"""
        return Path(file_path).relative_to(base_dir)
    
    def create_transcript_path(self, media_relative_path):
        """Create corresponding transcript path maintaining folder structure"""
        transcript_path = self.transcripts_dir / media_relative_path
        transcript_path = transcript_path.with_suffix('.md')
        return transcript_path

    def file_needs_transcription(self, file_path):
        """True if there is no transcript yet for this media file (under allowed groups)."""
        file_path = Path(file_path)
        try:
            relative_path = self.get_relative_path(file_path, self.downloads_dir)
        except ValueError:
            return False
        transcript_path = self.create_transcript_path(relative_path)
        return not transcript_path.exists()

    def ensure_directory_exists(self, file_path):
        """Ensure directory exists for given file path"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def is_audio_file(self, file_path):
        """Check if file is audio-only"""
        audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}
        return Path(file_path).suffix.lower() in audio_extensions
    
    def extract_audio(self, video_path, output_audio_path):
        """Extract audio from video file using ffmpeg"""
        try:
            cmd = [
                'ffmpeg', '-i', str(video_path),
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                '-y', str(output_audio_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio from {video_path}: {e}")
            return False
    
    def transcribe_file(self, file_path, gpu_id=0):
        """Transcribe a single media file"""
        file_path = Path(file_path)
        relative_path = None
        transcript_path = None
        audio_path = None
        temp_extracted = False

        try:
            relative_path = self.get_relative_path(file_path, self.downloads_dir)
            transcript_path = self.create_transcript_path(relative_path)

            if transcript_path.exists():
                print(f"Transcript already exists: {transcript_path}")
                return True

            self.ensure_directory_exists(transcript_path)

            device_label = "CPU" if self.device_count == 0 else f"GPU {gpu_id}"
            print(f"Transcribing {file_path} on {device_label}")

            audio_path = file_path
            if not self.is_audio_file(file_path):
                temp_audio_path = file_path.with_suffix('.wav')
                if not self.extract_audio(file_path, temp_audio_path):
                    return False
                audio_path = temp_audio_path
                temp_extracted = True

            model = self.models[gpu_id]
            lock = self._gpu_locks.get(gpu_id)
            if lock:
                with lock:
                    result = model.transcribe(str(audio_path))
            else:
                result = model.transcribe(str(audio_path))

            markdown_content = f"# Transcript: {file_path.name}\n\n"
            markdown_content += f"**Source:** {relative_path}\n"
            markdown_content += f"**Transcribed:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            markdown_content += f"**Model:** {self.model_name}\n"
            markdown_content += f"**Device:** {device_label}\n\n"
            markdown_content += "## Transcript\n\n"
            markdown_content += result['text']

            if result.get('segments'):
                markdown_content += "\n\n## Timestamps\n\n"
                for segment in result['segments']:
                    start_time = segment['start']
                    end_time = segment['end']
                    text = segment['text'].strip()
                    markdown_content += f"[{start_time:.2f} - {end_time:.2f}] {text}\n"

            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"Transcript saved: {transcript_path}")
            return True

        except Exception as e:
            print(f"Error transcribing {file_path}: {e}")
            return False
        finally:
            if temp_extracted and audio_path is not None and Path(audio_path).exists():
                try:
                    Path(audio_path).unlink()
                except OSError:
                    pass
            if torch.cuda.is_available():
                try:
                    torch.cuda.synchronize()
                    torch.cuda.empty_cache()
                except Exception:
                    pass
    
    def worker(self, gpu_id):
        """Worker function for transcription thread"""
        while True:
            try:
                file_path = self.transcription_queue.get(timeout=1)
                self.transcribe_file(file_path, gpu_id)
                self.transcription_queue.task_done()
            except queue.Empty:
                break
    
    def transcribe_all(self):
        """Transcribe all media files in downloads directory"""
        if not self.models:
            print("No models loaded. Exiting.")
            return
        
        all_media = self.find_media_files_filtered(self.downloads_dir)
        if self.allowed_top_level_dirs:
            print(f"Restricting to top-level folders: {sorted(self.allowed_top_level_dirs)}")
        print(f"Found {len(all_media)} media file(s) under downloads (after group filter)")

        media_files = [f for f in all_media if self.file_needs_transcription(f)]
        skipped = len(all_media) - len(media_files)
        if skipped:
            print(f"Skipping {skipped} file(s) that already have transcripts")
        print(f"Queued {len(media_files)} file(s) to transcribe")

        if not media_files:
            print("Nothing to transcribe")
            return

        for file_path in media_files:
            self.transcription_queue.put(file_path)

        num_workers = len(self.models)
        threads = []
        
        for gpu_id in range(num_workers):
            thread = threading.Thread(target=self.worker, args=(gpu_id,))
            thread.start()
            threads.append(thread)
        
        print(f"Started {num_workers} transcription workers")
        
        # Wait for all files to be processed
        self.transcription_queue.join()
        
        # Wait for threads to finish
        for thread in threads:
            thread.join()
        
        print("Transcription completed!")

def main():
    downloads_dir = os.getenv("DOWNLOADS_DIR", "/app/downloads")
    transcripts_dir = os.getenv("TRANSCRIPTS_DIR", "/app/transcripts")
    model_name = os.getenv("WHISPER_MODEL", "large")
    # Comma-separated names under downloads/ (e.g. group_3,group_4). Empty = scan all downloads.
    groups_raw = os.getenv("TRANSCRIBE_GROUPS", "group_3,group_4").strip()
    allowed = (
        frozenset(g.strip() for g in groups_raw.split(",") if g.strip())
        if groups_raw
        else None
    )

    print(f"Downloads directory: {downloads_dir}")
    print(f"Transcripts directory: {transcripts_dir}")
    print(f"Whisper model: {model_name}")
    if allowed:
        print(f"TRANSCRIBE_GROUPS: {', '.join(sorted(allowed))}")
    else:
        print("TRANSCRIBE_GROUPS: (empty) — all subfolders of downloads")

    # Ensure downloads directory exists
    Path(downloads_dir).mkdir(parents=True, exist_ok=True)

    use_multi_gpu = os.getenv("WHISPER_MULTI_GPU", "").lower() in ("1", "true", "yes")

    transcriber = WhisperTranscriber(
        downloads_dir,
        transcripts_dir,
        model_name,
        allowed_top_level_dirs=allowed,
        use_multi_gpu=use_multi_gpu,
    )
    transcriber.transcribe_all()

if __name__ == "__main__":
    main()
