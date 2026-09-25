"""
SocialDart Downloader Engine
High-performance, multi-platform media downloader backend powered by yt-dlp.
Supports watermark-free downloads, metadata pre-fetching, multi-threading,
bundled FFmpeg integration, turbo download speeds, and enterprise-grade security.
"""

import os
import re
import sys
import time
import shutil
import ipaddress
import urllib.parse
import threading
from typing import Dict, Any, Optional, Callable, Tuple

# Check for trusted CA certificates bundle
try:
    import certifi
    CA_BUNDLE = certifi.where()
except Exception:
    CA_BUNDLE = None

def find_ffmpeg_path() -> Optional[str]:
    """Find FFmpeg binary across app directories, assets, imageio_ffmpeg, and system PATH."""
    app_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else app_dir

    # 1. Check local assets and app directory
    search_paths = [
        os.path.join(exe_dir, "assets", "ffmpeg.exe"),
        os.path.join(app_dir, "assets", "ffmpeg.exe"),
        os.path.join(exe_dir, "ffmpeg.exe"),
        os.path.join(app_dir, "ffmpeg.exe"),
    ]
    for p in search_paths:
        if os.path.exists(p) and os.path.isfile(p):
            f_dir = os.path.dirname(p)
            if f_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = f_dir + os.path.pathsep + os.environ.get("PATH", "")
            return p

    # 2. Check bundled imageio_ffmpeg
    try:
        import imageio_ffmpeg
        raw_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        if raw_ffmpeg and os.path.exists(raw_ffmpeg):
            ffmpeg_dir = os.path.dirname(raw_ffmpeg)
            std_ffmpeg = os.path.join(ffmpeg_dir, "ffmpeg.exe")
            if not os.path.exists(std_ffmpeg):
                try:
                    shutil.copyfile(raw_ffmpeg, std_ffmpeg)
                except Exception:
                    pass
            chosen = std_ffmpeg if os.path.exists(std_ffmpeg) else raw_ffmpeg
            if ffmpeg_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = ffmpeg_dir + os.path.pathsep + os.environ.get("PATH", "")
            return chosen
    except Exception:
        pass

    # 3. Check system PATH
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    return None

FFMPEG_PATH = find_ffmpeg_path()

def find_node_path() -> Optional[str]:
    """Find Node.js binary for solving modern YouTube JS challenges."""
    node = shutil.which("node")
    if node:
        return node
    candidates = [
        r"C:\nvm4w\nodejs\node.exe",
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
        os.path.expanduser(r"~\AppData\Roaming\nvm\current\node.exe"),
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isfile(c):
            return c
    return None

# Check for ImpersonateTarget from yt_dlp
IMPERSONATE_TARGET = None
try:
    from yt_dlp.networking.impersonate import ImpersonateTarget
    IMPERSONATE_TARGET = ImpersonateTarget.from_str("chrome")
except Exception:
    pass

import yt_dlp


class SecurityValidator:
    """Enterprise security validator for SocialDart."""

    MAX_URL_LENGTH = 2048

    @classmethod
    def is_safe_url(cls, url: str) -> Tuple[bool, str]:
        """Validate URL to prevent SSRF, protocol injection, and loopback attacks."""
        if not url or not isinstance(url, str):
            return False, "URL cannot be empty."

        clean_url = url.strip()
        if len(clean_url) > cls.MAX_URL_LENGTH:
            return False, f"URL exceeds maximum allowed length of {cls.MAX_URL_LENGTH} characters."

        # Check for control characters or non-printable ASCII
        if any(ord(c) < 32 or ord(c) == 127 for c in clean_url):
            return False, "URL contains invalid or hidden control characters."

        try:
            parsed = urllib.parse.urlparse(clean_url)
        except Exception:
            return False, "Malformed URL format."

        # Scheme check: Strictly enforce HTTP or HTTPS
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            return False, f"Insecure protocol '{scheme}'. Only HTTP and HTTPS are permitted."

        hostname = parsed.hostname
        if not hostname:
            return False, "Missing or invalid domain host in URL."

        host_lower = hostname.lower()

        # Block localhost and standard loopback identifiers
        if host_lower in ("localhost", "127.0.0.1", "::1", "0.0.0.0", "local"):
            return False, "Access to localhost or internal loopback targets is prohibited."

        # Block private IP ranges (RFC 1918, Link-Local, CGNAT, Broadcast)
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False, "Access to private or reserved internal network addresses is prohibited."
        except ValueError:
            # Hostname is a domain name (not an IP literal), which is standard
            pass

        return True, "Safe"

    @classmethod
    def is_safe_directory(cls, path: str) -> Tuple[bool, str]:
        """Validate destination folder to prevent path traversal and OS corruption."""
        if not path or not isinstance(path, str):
            return False, "Directory path cannot be empty."

        try:
            norm_path = os.path.abspath(os.path.normpath(path.strip()))

            # Disallow writing directly to drive root (e.g. C:\)
            drive, tail = os.path.splitdrive(norm_path)
            if tail in ("", "\\", "/"):
                return False, "Saving directly to the drive root folder is not permitted for security."

            # Disallow protected Windows System directories
            windir = os.path.normpath(os.environ.get("WINDIR", "C:\\Windows")).lower()
            progfiles = os.path.normpath(os.environ.get("ProgramFiles", "C:\\Program Files")).lower()
            progfiles_x86 = os.path.normpath(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")).lower()

            target_lower = norm_path.lower()
            if (
                target_lower.startswith(windir)
                or target_lower.startswith(progfiles)
                or target_lower.startswith(progfiles_x86)
            ):
                return False, "Saving directly into protected Windows operating system folders is prohibited."

            return True, norm_path
        except Exception as e:
            return False, f"Invalid destination path: {str(e)}"

    @classmethod
    def sanitize_error_message(cls, err: Exception) -> str:
        """Sanitize error messages to avoid leaking sensitive internal system paths and format user-actionable alerts."""
        raw_msg = str(err)
        lower_msg = raw_msg.lower()

        # YouTube Bot Verification / Login Required Check
        if (
            "sign in to confirm you’re not a bot" in lower_msg
            or "sign in to confirm you're not a bot" in lower_msg
            or ("bot" in lower_msg and "confirm" in lower_msg)
            or "login_required" in lower_msg
        ):
            return "YouTube Bot Verification: YouTube blocked this request with a bot check. You can attach cookies via the top bar or try another network."

        # Strip user home directory path if present
        home_dir = os.path.expanduser("~")
        if home_dir in raw_msg:
            raw_msg = raw_msg.replace(home_dir, "~")
        # Keep clean message length
        return raw_msg[:140]


class PlatformInfo:
    """Platform detection and metadata."""
    
    PLATFORMS = {
        "tiktok": {
            "name": "TikTok",
            "badge": "🎵 TikTok (No Watermark)",
            "color": "#00F2FE",
            "regex": r"(?:tiktok\.com|douyin\.com)",
            "no_watermark": True,
        },
        "youtube": {
            "name": "YouTube",
            "badge": "▶ YouTube",
            "color": "#FF0000",
            "regex": r"(?:youtube\.com|youtu\.be)",
            "no_watermark": False,
        },
        "instagram": {
            "name": "Instagram",
            "badge": "📸 Instagram",
            "color": "#E1306C",
            "regex": r"instagram\.com",
            "no_watermark": True,
        },
        "facebook": {
            "name": "Facebook",
            "badge": "👥 Facebook",
            "color": "#1877F2",
            "regex": r"(?:facebook\.com|fb\.watch|fb\.com)",
            "no_watermark": True,
        },
        "twitter": {
            "name": "X (Twitter)",
            "badge": "𝕏 Twitter / X",
            "color": "#1DA1F2",
            "regex": r"(?:twitter\.com|x\.com)",
            "no_watermark": False,
        },
        "threads": {
            "name": "Threads",
            "badge": "🧵 Threads",
            "color": "#9333EA",
            "regex": r"threads\.net",
            "no_watermark": True,
        },
        "linkedin": {
            "name": "LinkedIn",
            "badge": "💼 LinkedIn",
            "color": "#0A66C2",
            "regex": r"linkedin\.com",
            "no_watermark": False,
        },
        "pinterest": {
            "name": "Pinterest",
            "badge": "📌 Pinterest",
            "color": "#E60023",
            "regex": r"(?:pinterest\.com|pin\.it)",
            "no_watermark": False,
        },
        "reddit": {
            "name": "Reddit",
            "badge": "🤖 Reddit",
            "color": "#FF4500",
            "regex": r"reddit\.com",
            "no_watermark": False,
        },
    }

    @classmethod
    def detect(cls, url: str) -> Dict[str, Any]:
        """Detect the platform of a URL."""
        if not url:
            return {
                "name": "Unknown",
                "badge": "🌐 Media Link",
                "color": "#3B82F6",
                "no_watermark": False,
            }
        
        url_lower = url.lower()
        for key, p in cls.PLATFORMS.items():
            if re.search(p["regex"], url_lower):
                return p
                
        return {
            "name": "Universal",
            "badge": "🌐 Universal Video",
            "color": "#06B6D4",
            "no_watermark": False,
        }


class DownloaderEngine:
    """Core yt-dlp downloading and inspection engine for SocialDart."""
    
    def __init__(self):
        self.ffmpeg_path = FFMPEG_PATH
        self.node_path = find_node_path()
        self._cancel_event = threading.Event()
        self.cookie_file: Optional[str] = self._discover_cookie_file()

    @staticmethod
    def validate_cookie_file(path: Optional[str]) -> Tuple[bool, bool, str]:
        """
        Validate whether cookie file exists and check if it contains YouTube/Google cookies.
        Returns: (is_valid_file, has_youtube_cookies, summary_message)
        """
        if not path or not os.path.exists(path) or not os.path.isfile(path) or os.path.getsize(path) < 10:
            return False, False, "No cookies loaded."
        
        has_yt = False
        total_cookies = 0
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) >= 7:
                        total_cookies += 1
                        domain = parts[0].lower()
                        if "youtube.com" in domain or "google.com" in domain:
                            has_yt = True
            if has_yt:
                return True, True, f"Active: Valid ({total_cookies} cookies, YouTube Session Verified ✅)"
            else:
                return True, False, f"Notice: {total_cookies} cookies found, but no YouTube session detected ⚠️"
        except Exception as e:
            return False, False, f"Failed to read cookies file: {str(e)}"

    def _discover_cookie_file(self) -> Optional[str]:
        """Automatically discover valid cookies.txt files with real YouTube credentials."""
        candidates = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "cookies.txt")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "cookies.txt")),
            os.path.abspath(os.path.join(os.path.expanduser("~"), ".socialdart", "cookies.txt")),
            os.path.abspath(os.path.join(os.path.expanduser("~"), "Downloads", "cookies.txt")),
        ]
        for path in candidates:
            is_valid, has_yt, _ = self.validate_cookie_file(path)
            # Only auto-bind cookie file if it actually contains YouTube cookies
            if is_valid and has_yt:
                return path
        return None

    def set_cookie_file(self, path: Optional[str]) -> bool:
        """Set or update the active cookie file."""
        if path and os.path.exists(path) and os.path.isfile(path) and os.path.getsize(path) > 10:
            self.cookie_file = os.path.abspath(path)
            return True
        elif path is None:
            self.cookie_file = None
            return True
        return False

    def get_cookie_file(self) -> Optional[str]:
        """Return the path to active cookie file if valid."""
        if self.cookie_file and os.path.exists(self.cookie_file) and os.path.isfile(self.cookie_file):
            return self.cookie_file
        return None

    def get_base_ydl_opts(self, platform_name: str = "") -> Dict[str, Any]:
        """Generate base yt-dlp options with anti-bot, ffmpeg, security, and turbo speed configs."""
        opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": False,
            "ignoreerrors": False,
            # Security: Sanitize Windows filenames and strip illegal characters
            "windowsfilenames": True,
            # Security: Prevent arbitrary external command execution
            "external_downloader": None,
            # Multi-threaded fragment downloads without socket saturation
            "concurrent_fragment_downloads": 4,
            "buffersize": 1048576,        # 1MB buffer for fast I/O throughput
            "http_chunk_size": 10485760,   # 10MB chunks to prevent CDN speed throttling
            "extractor_retries": 3,
            "file_access_retries": 3,
            "fragment_retries": 5,
            "retries": 5,
        }

        # Inject trusted CA certificate bundle if available
        if CA_BUNDLE and os.path.exists(CA_BUNDLE):
            opts["ca_bundle"] = CA_BUNDLE

        # Inject bundled FFmpeg if available
        if self.ffmpeg_path and os.path.exists(self.ffmpeg_path):
            opts["ffmpeg_location"] = os.path.dirname(self.ffmpeg_path)

        # Inject Node.js runtime for JavaScript challenges if available
        if self.node_path:
            opts["js_runtimes"] = {"node": {"path": self.node_path}}

        # Enable remote EJS challenge solver for YouTube (solves player JS challenges automatically)
        opts["remote_components"] = ["ejs:github"]

        is_youtube = platform_name.lower() == "youtube"

        # Inject Chrome Impersonation via curl_cffi for TikTok & others,
        # but avoid on YouTube where it causes connection timeouts
        if IMPERSONATE_TARGET and not is_youtube:
            opts["impersonate"] = IMPERSONATE_TARGET

        # Inject active cookies file if available and verified
        active_cookie = self.get_cookie_file()
        if active_cookie:
            is_valid, has_yt, _ = self.validate_cookie_file(active_cookie)
            if is_youtube:
                if is_valid and has_yt:
                    opts["cookiefile"] = active_cookie
            else:
                if is_valid:
                    opts["cookiefile"] = active_cookie

        # Extractor specific args for TikTok no-watermark bypass
        opts["extractor_args"] = {
            "tiktok": {
                "app_version": ["latest"],
            },
        }

        return opts

    def fetch_metadata(self, url: str) -> Dict[str, Any]:
        """Fetch media metadata securely without downloading."""
        # 1. Security Input Validation
        is_safe, reason = SecurityValidator.is_safe_url(url)
        if not is_safe:
            return {
                "success": False,
                "error": f"Security Notice: {reason}",
                "platform": "Unknown",
                "platform_badge": "⚠️ Insecure URL",
                "platform_color": "#EF4444",
                "no_watermark": False,
            }

        platform_meta = PlatformInfo.detect(url)
        opts = self.get_base_ydl_opts(platform_name=platform_meta["name"])
        opts["extract_flat"] = False

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise ValueError("Could not retrieve information for this URL.")

                # If playlist or multi-entry, pick the first video
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]

                # Duration formatting
                duration_sec = info.get("duration")
                if duration_sec is not None:
                    try:
                        d = int(duration_sec)
                        if d >= 3600:
                            duration_str = f"{d // 3600:02d}:{(d % 3600) // 60:02d}:{d % 60:02d}"
                        else:
                            duration_str = f"{d // 60:02d}:{d % 60:02d}"
                    except Exception:
                        duration_str = "Live / Unknown"
                else:
                    duration_str = "Unknown"

                # Creator / Uploader
                uploader = (
                    info.get("uploader")
                    or info.get("channel")
                    or info.get("creator")
                    or info.get("uploader_id")
                    or "Social Media Creator"
                )

                # Thumbnail URL validation
                thumbnail_url = (
                    info.get("thumbnail")
                    or (info.get("thumbnails") and info["thumbnails"][-1].get("url"))
                    or ""
                )
                if thumbnail_url:
                    is_thumb_safe, _ = SecurityValidator.is_safe_url(thumbnail_url)
                    if not is_thumb_safe:
                        thumbnail_url = ""

                # Available resolutions
                formats = info.get("formats", [])
                has_1080p = False
                has_720p = False
                has_480p = False

                for f in formats:
                    height = f.get("height")
                    if height:
                        if height >= 1080:
                            has_1080p = True
                        if height >= 720:
                            has_720p = True
                        if height >= 480:
                            has_480p = True

                return {
                    "success": True,
                    "title": info.get("title", "Social Video"),
                    "uploader": uploader,
                    "duration": duration_str,
                    "thumbnail_url": thumbnail_url,
                    "platform": platform_meta["name"],
                    "platform_badge": platform_meta["badge"],
                    "platform_color": platform_meta["color"],
                    "no_watermark": platform_meta["no_watermark"],
                    "has_1080p": has_1080p,
                    "has_720p": has_720p,
                    "has_480p": has_480p,
                    "original_url": url,
                }
        except Exception as e:
            return {
                "success": False,
                "error": SecurityValidator.sanitize_error_message(e),
                "platform": platform_meta["name"],
                "platform_badge": platform_meta["badge"],
                "platform_color": platform_meta["color"],
                "no_watermark": platform_meta["no_watermark"],
            }

    def download_media(
        self,
        url: str,
        quality: str,
        save_directory: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        finished_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Download media with live progress updates and enterprise security controls."""
        self._cancel_event.clear()

        # 1. URL Security Check
        is_safe_url, url_reason = SecurityValidator.is_safe_url(url)
        if not is_safe_url:
            if error_callback:
                error_callback(f"Security Rejection: {url_reason}")
            return

        # 2. Directory Security & Traversal Check
        is_safe_dir, safe_dir = SecurityValidator.is_safe_directory(save_directory)
        if not is_safe_dir:
            if error_callback:
                error_callback(f"Security Rejection: {safe_dir}")
            return

        platform_meta = PlatformInfo.detect(url)
        opts = self.get_base_ydl_opts(platform_name=platform_meta["name"])
        
        # Ensure save directory exists safely
        os.makedirs(safe_dir, exist_ok=True)
        opts["outtmpl"] = os.path.join(safe_dir, "%(title).80s [%(id)s].%(ext)s")

        # Configure Quality & Format
        clean_selector = "[format_note!*=watermarked]"
        is_audio = "Audio" in quality or "MP3" in quality or "M4A" in quality
        
        if "320k" in quality:
            opts["format"] = "bestaudio/best"
            if self.ffmpeg_path:
                opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }]
        elif "192k" in quality or "MP3" in quality:
            opts["format"] = "bestaudio/best"
            if self.ffmpeg_path:
                opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
        elif "M4A" in quality:
            opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
        elif "1080p" in quality:
            opts["format"] = f"bestvideo[height<=1080]{clean_selector}+bestaudio/best[height<=1080]{clean_selector}/best[height<=1080]/best"
        elif "720p" in quality:
            opts["format"] = f"bestvideo[height<=720]{clean_selector}+bestaudio/best[height<=720]{clean_selector}/best[height<=720]/best"
        elif "480p" in quality:
            opts["format"] = f"bestvideo[height<=480]{clean_selector}+bestaudio/best[height<=480]{clean_selector}/best[height<=480]/best"
        else:
            opts["format"] = f"bestvideo{clean_selector}+bestaudio/best{clean_selector}/best"

        # Merge container configuration if FFmpeg is available
        if self.ffmpeg_path and not is_audio:
            opts["merge_output_format"] = "mp4"

        last_filename = [None]

        def _progress_hook(d: Dict[str, Any]):
            if self._cancel_event.is_set():
                raise yt_dlp.utils.DownloadCancelled("Download cancelled by user")

            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                speed = d.get("_speed_str") or "Calculating..."
                eta = d.get("_eta_str") or "--:--"

                ratio = 0.0
                if total > 0:
                    ratio = min(1.0, max(0.0, downloaded / total))
                
                percent_str = f"{int(ratio * 100)}%" if total > 0 else "Downloading..."
                
                downloaded_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024) if total > 0 else 0
                size_str = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB" if total > 0 else f"{downloaded_mb:.1f} MB"

                if progress_callback:
                    progress_callback({
                        "progress": ratio,
                        "percent_str": percent_str,
                        "speed_str": speed,
                        "size_str": size_str,
                        "eta_str": eta,
                        "status": "Downloading at turbo speed...",
                    })

            elif status == "finished":
                filename = d.get("filename")
                if filename:
                    last_filename[0] = filename
                if progress_callback:
                    progress_callback({
                        "progress": 1.0,
                        "percent_str": "100%",
                        "speed_str": "Done",
                        "size_str": "Finalizing",
                        "eta_str": "00:00",
                        "status": "Merging & finalizing file with FFmpeg...",
                    })

        opts["progress_hooks"] = [_progress_hook]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                downloaded_file = None
                if info_dict:
                    downloaded_file = ydl.prepare_filename(info_dict)
                    if "MP3" in quality:
                        base, _ = os.path.splitext(downloaded_file)
                        downloaded_file = base + ".mp3"
                    elif not is_audio and self.ffmpeg_path:
                        base, _ = os.path.splitext(downloaded_file)
                        if os.path.exists(base + ".mp4"):
                            downloaded_file = base + ".mp4"

                if finished_callback:
                    finished_callback(downloaded_file or last_filename[0] or safe_dir)

        except yt_dlp.utils.DownloadCancelled:
            self._cleanup_partial_files(safe_dir)
            if error_callback:
                error_callback("Download was cancelled.")
        except Exception as e:
            self._cleanup_partial_files(safe_dir)
            if error_callback:
                error_callback(f"Download Error: {SecurityValidator.sanitize_error_message(e)}")

    def _cleanup_partial_files(self, directory: str):
        """Safely clean up incomplete .part and .ytdl fragments."""
        try:
            if os.path.exists(directory):
                for f in os.listdir(directory):
                    if f.endswith((".part", ".ytdl")):
                        filepath = os.path.join(directory, f)
                        try:
                            # Only clean fragments modified in the last 15 minutes
                            if time.time() - os.path.getmtime(filepath) < 900:
                                os.remove(filepath)
                        except Exception:
                            pass
        except Exception:
            pass

    def cancel_download(self):
        """Request immediate download cancellation."""
        self._cancel_event.set()
