"""
Download playlist videos, write per-playlist markdown under a date-stamped folder,
then download MP3 audio for each playlist into the same folder.
"""
import logging
import os
import re
import sys
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

from download_audios import download_audio_batch
from download_playlists import (
    download_playlist_videos,
    extract_playlist_entries,
    write_playlist_markdown,
)

LOGGER_NAME = "yt_downloader"


def _safe_dir_name(name: str) -> str:
    """Filesystem-safe folder name from a group label."""
    s = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return s or "group"


def setup_logging(log_path: str) -> logging.Logger:
    """Attach file + console handlers to the root logger so all modules share one log file."""
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    root.addHandler(fh)
    root.addHandler(sh)
    return logging.getLogger(LOGGER_NAME)


def _run_session(
    playlist_urls: Sequence[str],
    session_dir: str,
    group_label: Optional[str] = None,
) -> None:
    """Run video + markdown + audio for all playlists under ``session_dir`` (one dated folder)."""
    os.makedirs(session_dir, exist_ok=True)

    log_path = os.path.join(session_dir, "download.log")
    log = setup_logging(log_path)
    log.info("Log file: %s", log_path)
    log.info("Session output directory: %s", session_dir)
    if group_label:
        log.info("Group: %s", group_label)
    log.info("Playlists to process: %d", len(playlist_urls))

    if group_label:
        print(f"\n========== Group: {group_label} ==========")
        print(f"Output: {session_dir}\n")

    batches: List[Tuple[str, List[str]]] = []

    for idx, playlist_url in enumerate(playlist_urls, start=1):
        log.info("--- Playlist %d/%d ---", idx, len(playlist_urls))
        log.info("Extracting metadata: %s", playlist_url)
        print(f"\n[{idx}/{len(playlist_urls)}] Fetching playlist: {playlist_url!r}")

        data = extract_playlist_entries(playlist_url)
        if not data:
            log.error("Could not read playlist entries; skipping: %s", playlist_url)
            print("  Skipped: invalid or empty playlist.")
            continue

        playlist_title, folder_name, links = data
        folder_path = os.path.join(session_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        log.info("Playlist title: %s -> folder: %s", playlist_title, folder_path)

        md_path = write_playlist_markdown(playlist_title, folder_name, folder_path, links)
        log.info("Wrote markdown (%d links): %s", len(links), md_path)
        print(f"  Wrote {len(links)} links -> {md_path}")

        log.info("Starting video downloads into %s", folder_path)
        print(f"  Downloading videos -> {folder_path!r} ...")
        try:
            download_playlist_videos(playlist_url, folder_path)
            log.info("Video downloads finished for playlist: %s", playlist_title)
            print("  Video downloads finished.")
        except Exception as e:
            log.exception("Video download failed for %s: %s", playlist_url, e)
            print(f"  Video download error: {e}")
            continue

        video_urls = [url for _title, url in links]
        batches.append((folder_path, video_urls))

    log.info("--- Audio phase: %d playlist(s) ---", len(batches))
    print("\n--- Starting audio downloads per playlist ---\n")

    for idx, (folder_path, video_urls) in enumerate(batches, start=1):
        log.info("Audio batch %d/%d: %d tracks -> %s", idx, len(batches), len(video_urls), folder_path)
        print(f"[{idx}/{len(batches)}] Audio: {len(video_urls)} tracks -> {folder_path!r}")
        try:
            download_audio_batch(video_urls, folder_path)
            log.info("Audio batch completed for %s", folder_path)
        except Exception as e:
            log.exception("Audio batch failed for %s: %s", folder_path, e)
            print(f"  Audio batch error: {e}")

    log.info("Session finished.")
    print(f"\nDone. Outputs under: {session_dir}")


def run(playlist_urls: Sequence[str], output_base_dir: str) -> None:
    """
    For each playlist: under ``output_base_dir/<YYYY-MM-DD>/<playlist>/`` write
    ``<playlist>.md``, download video files, then download audio for all links into
    that same folder.
    """
    base = os.path.abspath(output_base_dir)
    date_folder_name = datetime.now().strftime("%Y-%m-%d")
    session_dir = os.path.join(base, date_folder_name)
    _run_session(playlist_urls, session_dir)


def run_grouped(
    groups: Sequence[Tuple[str, Sequence[str]]],
    output_base_dir: str,
) -> None:
    """
    Run ``run``-style downloads for each group into its own tree:

    ``output_base_dir/<group_folder>/<YYYY-MM-DD>/<playlist>/``

    Each ``groups`` item is ``(group_folder_name, playlist_urls)``. Empty URL lists
    are skipped.
    """
    base = os.path.abspath(output_base_dir)
    date_folder_name = datetime.now().strftime("%Y-%m-%d")

    for group_name, playlist_urls in groups:
        if not playlist_urls:
            print(f"\nSkipping empty group: {group_name!r}\n")
            continue
        safe = _safe_dir_name(group_name)
        session_dir = os.path.join(base, safe, date_folder_name)
        _run_session(playlist_urls, session_dir, group_label=group_name)


if __name__ == "__main__":
    # Default list when PLAYLIST_URLS is not set in the environment (e.g. Docker: -e PLAYLIST_URLS=...)
    _default_playlists = [
        "https://www.youtube.com/playlist?list=PLkil-jsseebxNZKrETEEHEcXHCFB8ppk0",
        "https://www.youtube.com/playlist?list=PLkil-jsseebyFyRcRotztGpm3i1SkJcO8",
    ]
    if "PLAYLIST_URLS" in os.environ:
        _raw = os.environ["PLAYLIST_URLS"].strip()
        PLAYLIST_URLS = [u.strip() for u in _raw.split(",") if u.strip()]
    else:
        PLAYLIST_URLS = _default_playlists

    _out = os.environ.get("OUTPUT_DIR", "").strip()
    OUTPUT_BASE = os.path.abspath(_out) if _out else os.path.join(os.getcwd(), "downloads")

    if not PLAYLIST_URLS:
        print("Add playlist URLs to PLAYLIST_URLS in download.py (or import run() from elsewhere).")
        sys.exit(1)

    run(PLAYLIST_URLS, OUTPUT_BASE)
