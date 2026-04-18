import os
import re
from typing import List, Optional, Tuple

import yt_dlp

# (playlist_title, folder_name, list of (title, url))
PlaylistData = Tuple[str, str, List[Tuple[str, str]]]


def extract_playlist_entries(playlist_url: str) -> Optional[PlaylistData]:
    """Return playlist title, sanitized folder name, and (title, url) pairs, or None on failure."""
    ydl_opts_extract = {
        "extract_flat": "in_playlist",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts_extract) as ydl:
        info = ydl.extract_info(playlist_url, download=False)

    if not info or "entries" not in info:
        return None

    playlist_title = info.get("title", "Unknown_Playlist")
    folder_name = re.sub(r'[\\/*?:"<>|]', "", playlist_title).strip() or "Unknown_Playlist"
    links: List[Tuple[str, str]] = []
    for entry in info.get("entries") or []:
        if not entry:
            continue
        title = entry.get("title", "Unknown Title")
        url = entry.get("url")
        if url:
            if not url.startswith("http"):
                url = f"https://www.youtube.com/watch?v={url}"
            links.append((title, url))
    return playlist_title, folder_name, links


def write_playlist_markdown(
    playlist_title: str, folder_name: str, folder_path: str, links: List[Tuple[str, str]]
) -> str:
    """Write ``{folder_name}.md`` under ``folder_path``. Returns path to the file."""
    os.makedirs(folder_path, exist_ok=True)
    md_path = os.path.join(folder_path, f"{folder_name}.md")
    with open(md_path, "w", encoding="utf-8") as md_file:
        md_file.write(f"# {playlist_title}\n\n")
        for title, url in links:
            md_file.write(f"- [{title}]({url})\n")
    return md_path


def download_playlist_videos(playlist_url: str, folder_path: str) -> None:
    """Download all videos for the playlist into ``folder_path``."""
    os.makedirs(folder_path, exist_ok=True)
    ydl_opts_download = {
        "outtmpl": os.path.join(folder_path, "%(title)s.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
        ydl.download([playlist_url])


def download_playlist(playlist_urls, output_dir):
    """
    For each playlist URL: extract entries, write a markdown link file, and download
    videos into a subfolder of ``output_dir`` named after the playlist title.
    """
    os.makedirs(output_dir, exist_ok=True)

    for playlist_url in playlist_urls:
        print(f"Fetching playlist information for {playlist_url!r}... This might take a moment.")

        data = extract_playlist_entries(playlist_url)
        if not data:
            print("Error: Could not find playlist entries. Make sure it's a valid playlist URL.")
            continue

        playlist_title, folder_name, links = data
        folder_path = os.path.join(output_dir, folder_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Created folder: {folder_path}")

        md_file_path = write_playlist_markdown(playlist_title, folder_name, folder_path, links)
        print(f"Saved {len(links)} video links to {md_file_path}")

        print(f"\nStarting video downloads into {folder_path!r}...")
        download_playlist_videos(playlist_url, folder_path)

        print("Playlist done.\n")

    print("All done!")
