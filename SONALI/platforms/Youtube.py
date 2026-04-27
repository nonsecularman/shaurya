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

        self.id_regex = re.compile(
            r"(?:v=|\/)([A-Za-z0-9_-]{11})(?:[&?]|$)"
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

    async def url(self, message) -> Optional[str]:
        """
        Message ya replied message se YouTube URL extract karta hai.
        """
        try:
            text = getattr(message, "text", None) or getattr(message, "caption", None) or ""

            if not text and getattr(message, "reply_to_message", None):
                reply = message.reply_to_message
                text = getattr(reply, "text", None) or getattr(reply, "caption", None) or ""

            if not text:
                return None

            text = text.strip()

            # /play <something>
            if text.startswith("/") and " " in text:
                text = text.split(" ", 1)[1].strip()

            match = self.regex.search(text)
            return match.group(0) if match else None

        except Exception as ex:
            logger.warning("Failed to extract YouTube URL: %s", ex)
            return None

    async def query(self, message) -> Optional[str]:
        """
        /play song name ya replied text se query nikaalta hai.
        Agar URL milega to None return karega.
        """
        try:
            text = getattr(message, "text", None) or getattr(message, "caption", None) or ""

            if not text and getattr(message, "reply_to_message", None):
                reply = message.reply_to_message
                text = getattr(reply, "text", None) or getattr(reply, "caption", None) or ""

            if not text:
                return None

            text = text.strip()

            if text.startswith("/") and " " in text:
                text = text.split(" ", 1)[1].strip()

            if not text:
                return None

            if self.valid(text):
                return None

            return text

        except Exception as ex:
            logger.warning("Failed to extract query: %s", ex)
            return None

    def video_id(self, url: str) -> Optional[str]:
        """
        YouTube URL se video id nikaalta hai.
        """
        try:
            if not url:
                return None

            if "youtu.be/" in url:
                part = url.split("youtu.be/")[-1]
                return part.split("?")[0].split("&")[0].split("/")[0][:11]

            if "shorts/" in url:
                part = url.split("shorts/")[-1]
                return part.split("?")[0].split("&")[0].split("/")[0][:11]

            match = self.id_regex.search(url)
            if match:
                return match.group(1)

        except Exception as ex:
            logger.warning("Failed to parse video id from url %s: %s", url, ex)

        return None

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

    async def details(self, url: str, m_id: int, video: bool = False) -> Optional[Track]:
        """
        Direct YouTube URL se basic Track object banata hai.
        """
        try:
            video_id = self.video_id(url)
            if not video_id:
                return None

            # py_yt se same URL ko search style me fetch karne ki try
            _search = VideosSearch(url, limit=1, with_live=False)
            results = await _search.next()

            if results and results.get("result"):
                data = results["result"][0]
                return Track(
                    id=data.get("id") or video_id,
                    channel_name=(data.get("channel") or {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=_to_seconds(data.get("duration")),
                    message_id=m_id,
                    title=_safe_title(data.get("title")),
                    thumbnail=_safe_thumb(data.get("thumbnails")),
                    url=data.get("link") or url,
                    view_count=(data.get("viewCount") or {}).get("short", ""),
                    video=video,
                )

            return Track(
                id=video_id,
                message_id=m_id,
                title="YouTube Track",
                url=url,
                video=video,
            )

        except Exception as ex:
            logger.warning("Failed to fetch details for url %s: %s", url, ex)
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
                "format": "bestaudio[acodec=opus]/bestaudio/best",
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
# Singleton instance
# =========================================================
youtube = YouTube()

# =========================================================
# Compatibility alias
# =========================================================
YouTubeAPI = YouTube
