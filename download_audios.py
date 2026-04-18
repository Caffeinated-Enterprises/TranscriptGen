import logging
import os

import yt_dlp

_log = logging.getLogger(__name__)


def download_audio_batch(video_urls, output_dir):
    """Download best audio as MP3 for each URL into ``output_dir``."""
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "sleep_interval": 10,
        "max_sleep_interval": 25,
        "quiet": False,
        "no_warnings": True,
    }

    msg = f"Starting batch download of {len(video_urls)} audio tracks into {output_dir!r}"
    _log.info(msg)
    _log.info("Randomized delay between downloads: 10-25s (rate limiting).")
    print(f"{msg}...")
    print("A randomized delay will be applied between each download to prevent rate limiting.\n")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download(video_urls)
            _log.info("Audio batch finished successfully for %s", output_dir)
            print("\n✅ All audio downloads completed successfully!")
        except Exception as e:
            _log.exception("Audio batch failed for %s: %s", output_dir, e)
            print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    my_videos = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",
    ]
    out = os.path.join(os.getcwd(), "audio_downloads")

    if my_videos:
        download_audio_batch(my_videos, out)
    else:
        print("Please add some video URLs to the 'my_videos' list.")
