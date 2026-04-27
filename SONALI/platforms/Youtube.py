# Copyright (c) 2025 SONALImousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import re
import yt_dlp
import random
import asyncio
import aiohttp

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from py_yt import Playlist, VideosSearch

from SONALI import logger


# =========================================================
# Fallback Track class
# If your real Track class exists elsewhere, you can replace
# the import path below. This fallback prevents crash.
# =========================================================
try:
    from SONALI.types import Track  # change this if your real Track path is different
except Exception:
    @dataclass
    class Track:
        id: Optional[str] = None
        channel_name: str = ""
        duration: Optional[str] = None
        duration_sec: int = 0
        message_id: Optional[int] = None
        title: str = ""
        thumbnail: str = ""
        url: str = ""
        view_count: str = ""
        video: bool = False
        user: str = ""


def _to_seconds(duration: Optional[str]) -> int:
    if not duration:
        return 0
    try:
        parts = duration.strip().split(":")
        parts = [int(x) for x in parts]
        if len(parts) == 3:
            h, m, s = parts
            return h * 3600 + m * 60 + s
        if len(parts) == 2:
            m, s = parts
            return m * 60 + s
        if len(parts) == 1:
            return parts[0]
    except Exception:
        return 0
    return 0


def _safe_thumb(thumbnails) -> str:
    try:
        if isinstance(thumbnails, list) and thumbnails:
            url = thumbnails[-1].get("url", "")
            return url.split("?")[0] if url else ""
    except Exception:
        pass
    return ""


def _safe_title(title: Optional[str], limit: int = 25) -> str:
    if not title:
        return "Unknown Title"
    return str(title)[:limit]


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "SONALI/cookies"
        self.warned = False

        Path(self.cookie_dir).mkdir(parents=True, exist_ok=True)
        Path("downloads").mkdir(parents=True, exist_ok=True)

        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=PL[A-Za-z0-9_-]+|[A-Za-z0-9_-]{11}))\S*"
        )

    def get_cookies(self):
        Path(self.cookie_dir).mkdir(parents=True, exist_ok=True)

        if not self.checked:
            self.cookies.clear()
            try:
                for file in os.listdir(self.cookie_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(f"{self.cookie_dir}/{file}")
            except Exception as ex:
                logger.warning("Could not read cookies directory: %s", ex)
            self.checked = True

        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("Cookies are missing; downloads might fail.")
            return None

        return random.choice(self.cookies)

    async def save_cookies(self, urls: List[str]) -> None:
        logger.info("Saving cookies from urls...")
        Path(self.cookie_dir).mkdir(parents=True, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    name = url.rstrip("/").split("/")[-1]
                    link = "https://batbin.me/raw/" + name
                    async with session.get(link) as resp:
                        resp.raise_for_status()
                        with open(f"{self.cookie_dir}/{name}.txt", "wb") as fw:
                            fw.write(await resp.read())
                except Exception as ex:
                    logger.warning("Failed to save cookie from %s: %s", url, ex)

        self.checked = False
        self.cookies.clear()
        logger.info("Cookies saved in %s.", self.cookie_dir)

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url or ""))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url or ""))

    async def search(self, query: str, m_id: int, video: bool = False) -> Optional[Track]:
        try:
            _search = VideosSearch(query, limit=1, with_live=False)
            results = await _search.next()
        except Exception as ex:
            logger.warning("YouTube search failed for '%s': %s", query, ex)
            return None

        try:
            if results and results.get("result"):
                data = results["result"][0]

                return Track(
                    id=data.get("id"),
                    channel_name=(data.get("channel") or {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=_to_seconds(data.get("duration")),
                    message_id=m_id,
                    title=_safe_title(data.get("title")),
                    thumbnail=_safe_thumb(data.get("thumbnails")),
                    url=data.get("link") or "",
                    view_count=(data.get("viewCount") or {}).get("short", ""),
                    video=video,
                )
        except Exception as ex:
            logger.warning("Failed to parse YouTube search result: %s", ex)

        return None

    async def playlist(
        self,
        limit: int,
        user: str,
        url: str,
        video: bool
    ) -> List[Track]:
        tracks = []

        try:
            plist = await Playlist.get(url)
            videos = (plist or {}).get("videos", [])

            for data in videos[:max(limit, 0)]:
                try:
                    tracks.append(
                        Track(
                            id=data.get("id"),
                            channel_name=(data.get("channel") or {}).get("name", ""),
                            duration=data.get("duration"),
                            duration_sec=_to_seconds(data.get("duration")),
                            title=_safe_title(data.get("title")),
                            thumbnail=_safe_thumb(data.get("thumbnails")),
                            url=(data.get("link") or "").split("&list=")[0],
                            user=user,
                            view_count="",
                            video=video,
                        )
                    )
                except Exception as ex:
                    logger.warning("Failed to parse playlist item: %s", ex)

        except Exception as ex:
            logger.warning("Playlist fetch failed: %s", ex)

        return tracks

    def _find_existing_file(self, video_id: str, video: bool = False) -> Optional[str]:
        download_path = Path("downloads")
        if not download_path.exists():
            return None

        if video:
            allowed_exts = {".mp4", ".mkv", ".webm"}
        else:
            allowed_exts = {".webm", ".m4a", ".opus", ".mp3"}

        for file in download_path.glob(f"{video_id}.*"):
            if file.suffix.lower() in allowed_exts and file.exists():
                return str(file)

        return None

    async def download(self, video_id: str, video: bool = False) -> Optional[str]:
        url = self.base + video_id
        Path("downloads").mkdir(parents=True, exist_ok=True)

        existing = self._find_existing_file(video_id, video)
        if existing:
            return existing

        cookie = self.get_cookies()

        base_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "geo_bypass": True,
            "no_warnings": True,
            "overwrites": False,
            "nocheckcertificate": True,
        }

        if cookie:
            base_opts["cookiefile"] = cookie

        if video:
            ydl_opts = {
                **base_opts,
                "format": (
                    "bestvideo[height<=?720][width<=?1280][ext=mp4]+"
                    "bestaudio[ext=m4a]/best[ext=mp4]/best"
                ),
                "merge_output_format": "mp4",
            }
        else:
            ydl_opts = {
                **base_opts,
                "format": "bestaudio[acodec=opus]/bestaudio",
            }

        def _download():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as ex:
                logger.warning("yt-dlp download error for %s: %s", video_id, ex)
                return None
            except Exception as ex:
                logger.warning("Download failed for %s: %s", video_id, ex)
                return None

            return self._find_existing_file(video_id, video)

        return await asyncio.to_thread(_download)


# =========================================================
# Compatibility alias
# If somewhere __init__.py imports YouTubeAPI,
# this prevents ImportError.
# =========================================================
YouTubeAPI = YouTube
