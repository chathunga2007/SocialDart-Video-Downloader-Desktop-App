# 🎯 SocialDart - Universal HD & No-Watermark Desktop Video Downloader

<p align="center">
  <img src="assets/social-dart-logo.png" alt="SocialDart Logo" width="180" />
</p>

<p align="center">
  <b>Universal Social Media Media Downloader for Windows</b><br>
  <i>Download • Save • Enjoy</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Framework-CustomTkinter-0284C7?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Engine-yt--dlp-FF0000?style=for-the-badge" />
  <img src="https://img.shields.io/badge/FFmpeg-7.1_Bundled-059669?style=for-the-badge&logo=ffmpeg&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-Windows_10_|_11-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
</p>

---

## ⚡ Developed by
**Chathunga Bimsara**

---

## ✨ Features

- **🚫 Automatic Watermark Removal**: Direct clean stream extraction for TikTok, Instagram Reels, and Facebook videos.
- **🌐 Wide Platform Coverage**:
  - ▶️ **YouTube**: Videos, Shorts, and High-Bitrate Audio
  - 🎵 **TikTok**: Clean No-Watermark HD Videos
  - 📸 **Instagram**: Reels, Posts, and Stories
  - 👥 **Facebook**: Public Posts and Reels
  - 𝕏 **Twitter / X**: Videos and GIFs
  - 🧵 **Threads**: Direct Video Downloads
  - 💼 **LinkedIn**: Educational and Post Videos
  - 📌 **Pinterest**: Video Pins and Ideas
  - 🌐 **1000+ Websites** supported via the underlying engine
- **📦 Bundled FFmpeg 7.1**: Integrated zero-config audio-video stream merging and studio-grade MP3 audio conversion without requiring manual system PATH setup.
- **⚡ Turbo Speed Downloader**: 8 multi-threaded concurrent fragment streams with 10MB chunk buffering for blazing download throughput.
- **🎨 Modern Cyber-Luxe UI**:
  - High-contrast **Dark Mode** & **Light Mode** one-click switcher.
  - Interactive button micro-animations (Flash click effects, cyclic loading spinners).
  - Glowing active card borders on video detection.
  - Live metadata inspection: Video thumbnail, Title, Creator, Duration, and Platform badge.
- **🎛️ Dynamic Format Selection**:
  - **🎬 Video (MP4)**: Best Available (4K / 1080p), 1080p Full HD, 720p HD, 480p SD.
  - **🎵 Audio Only**: MP3 320kbps (Studio High Quality), MP3 192kbps (Standard), M4A (Original AAC).
- **🛡️ Enterprise Security & Hardening**:
  - **SSRF & Loopback Shield**: Strict protocol enforcement (HTTP/HTTPS only). Prohibits loopback (`127.0.0.1`, `localhost`) and private RFC 1918 internal subnets (`10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`).
  - **Path Traversal & System Folder Protection**: Blocks output to Windows system directories (`C:\Windows`, `Program Files`, root drive).
  - **Command Injection Prevention**: Pure `subprocess` parameter arrays without `shell=True` for external processes (File Explorer).
  - **Decompression Bomb Protection**: Pillow pixel limits (`25,000,000 max pixels`) and 5MB network caps for image previews.
  - **SSL/TLS Integrity**: CA bundle verification via `certifi` and anti-MITM protection.
  - **Automatic Fragment Cleanup**: Cleans up abandoned `.part` and `.ytdl` files on user cancellation or unexpected error.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chathunga2007/SocialDart-Video-Downloader-Desktop-App.git
   cd SocialDart-Video-Downloader-Desktop-App
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

---

## 💻 Running the App

### Option 1: Direct Shortcut
Double-click `SocialDart.lnk` or `SocialDart.vbs` for a native application experience without terminal popups.

### Option 2: Terminal
```powershell
python app.py
```

---

## 📁 Project Structure

```
SocialDart-Desktop-Video-Downloader/
├── assets/
│   ├── social-dart-logo.png   # Main official in-app logo
│   ├── taskbar_logo.png       # Dedicated Windows taskbar squircle logo
│   ├── social-dart.ico        # Multi-resolution icon for window
│   └── taskbar.ico            # Multi-resolution taskbar icon (16-256px)
├── app.py                     # Main CustomTkinter desktop GUI application
├── downloader_engine.py       # Core yt-dlp downloading and inspection engine
├── requirements.txt           # Project dependencies
├── SocialDart.vbs             # Silent background launcher
├── SocialDart.bat             # Batch launcher script
├── SocialDart.lnk             # Direct Windows Desktop shortcut
├── .gitignore                 # Git ignore configurations
└── README.md                  # Project documentation
```

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.

<p align="center">
  Crafted with ❤️ by <b>Chathunga Bimsara</b>
</p>
