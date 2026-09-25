# 🎯 SocialDart - Universal HD & No-Watermark Desktop Video Downloader

<p align="center">
  <img src="assets/social-dart-logo.png" alt="SocialDart Logo" width="200" />
</p>

<p align="center">
  <b>A Fast, Beautiful, and Enterprise-Hardened Desktop Video Downloader for Windows</b><br>
  <i>Download • Save • Enjoy — Seamlessly download videos and audio from YouTube, TikTok, Instagram, Facebook, and 1000+ sites.</i>
</p>

<p align="center">
  <a href="https://github.com/chathunga2007/SocialDart-Video-Downloader-Desktop-App/releases"><img src="https://img.shields.io/badge/Release-v1.0.0_Ultra-0284C7?style=for-the-badge&logo=windows&logoColor=white" alt="Release" /></a>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/GUI-CustomTkinter-065F46?style=for-the-badge" alt="CustomTkinter" />
  <img src="https://img.shields.io/badge/Engine-yt--dlp-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="yt-dlp" />
  <img src="https://img.shields.io/badge/FFmpeg-7.1_Bundled-10B981?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="FFmpeg" />
  <img src="https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge" alt="License" />
</p>

---

## ⚡ Developed by
**Chathunga Bimsara** ([@chathunga2007](https://github.com/chathunga2007))

---

## 🌟 Why SocialDart?

Most online video downloaders are bloated with intrusive ads, malicious pop-ups, slow download speeds, or require sketchy browser extensions. **SocialDart** provides a clean, native Windows desktop application with zero advertisements, maximum network bandwidth utilization, automated anti-bot challenge solvers, and studio-grade media post-processing.

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           SocialDart v1.0.0                            │
  │  🔗 Paste Link ──► 🔍 Auto-Detect ──► 🎬 Select Quality ──► ⚡ Download │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🚀 Platform Coverage & Watermark Removal
- **🎵 TikTok**: Downloads pristine, clean HD videos **without any watermark**.
- **▶️ YouTube**: Full support for standard videos, YouTube Shorts, music tracks, and livestreams up to **4K Ultra HD** and **1080p Full HD**.
- **📸 Instagram**: High-definition download for Reels, Posts, Carousels, and Stories.
- **👥 Facebook**: Seamless extraction of public Videos, Watch clips, and Reels.
- **𝕏 Twitter / X**: Video clips, animations, and high-definition GIFs.
- **🧵 Threads**: Direct video post extraction.
- **💼 LinkedIn**: High-definition educational and business media.
- **📌 Pinterest**: High-bitrate video pins.
- **🌐 1000+ Additional Platforms**: Powered by the battle-tested `yt-dlp` core.

---

### 📦 Supported Platforms Matrix

| Platform | Content Supported | Max Quality | Watermark Removed? | Audio Only Extraction? |
| :--- | :--- | :--- | :---: | :---: |
| **YouTube** | Videos, Shorts, Music | **4K / 1080p / 720p** | N/A | ✅ (MP3 320k / M4A) |
| **TikTok** | Videos, Slideshows | **1080p / 720p HD** | **YES (No WM)** | ✅ (MP3 320k / M4A) |
| **Instagram** | Reels, Posts, Stories | **Original HD** | **YES** | ✅ (MP3 320k / M4A) |
| **Facebook** | Reels, Watch, Videos | **1080p / 720p HD** | **YES** | ✅ (MP3 320k / M4A) |
| **X (Twitter)** | Video Posts, GIFs | **Best Available** | N/A | ✅ (MP3 320k / M4A) |
| **Threads** | Video Posts | **Original HD** | **YES** | ✅ (MP3 320k / M4A) |
| **LinkedIn** | Videos & Presentations| **Original HD** | N/A | ✅ (MP3 320k / M4A) |
| **Pinterest** | Video Pins | **Best Available** | **YES** | ✅ (MP3 320k / M4A) |

---

### 🧩 Automated Anti-Bot & Player Challenge Solvers
- **⚡ Node.js JavaScript Solver**: Integrates automated EJS runtime challenge handling (`--remote-components ejs:github`) to resolve YouTube player signature and n-token challenges without manual interventions.
- **🍪 Smart YouTube Cookie Manager**:
  - Live session validation checking for genuine `.youtube.com` / `.google.com` authentication tokens.
  - Interactive cookie status badge in the top navigation bar (`Cookies Active ✅` / `No Cookies ⚪`).
  - Persistent, permission-safe storage in user profile (`~/.socialdart/cookies.txt`), ensuring complete compatibility with standard Windows non-admin accounts.
  - Built-in 20-second step-by-step export guide with a 1-click Web Store extension launcher.
- **🌐 Network-Adaptive Impersonation**: Uses modern TLS fingerprint impersonation (`curl_cffi`) tailored for platforms like TikTok while maintaining direct, native socket streams for Google Video CDNs to eliminate timeouts.

---

### 🎨 Modern Cyber-Luxe User Interface
- **🌓 Dynamic Dark & Light Theme**: Effortless 1-click theme switcher with harmonious HSL dark palettes and high-contrast light aesthetics.
- **✨ Micro-Animations & Glow Effects**:
  - Glowing colored card borders matching the detected platform brand.
  - Visual button feedback and smooth loading indicators.
  - Live download speed (`MB/s`), total size, ETA, and real-time progress bar.
- **🖼️ Rich Media Inspection**: Live video thumbnail preview, channel/creator title, exact duration, and detected platform badge upon link inspection.

---

### 🛠️ Integrated Zero-Config FFmpeg 7.1
- **Bundled FFmpeg Binary**: Includes full standalone FFmpeg binaries directly inside the installer package (`assets/ffmpeg.exe`).
- **Zero Configuration Required**: Users do not need to install FFmpeg or set up Windows environment PATH variables manually.
- **Pristine Merging**: Merges independent high-definition DASH video streams and high-bitrate audio streams into standard, universally playable MP4 containers.
- **Studio-Quality Audio Extraction**: One-click extraction to MP3 (320 kbps Studio Quality or 192 kbps Standard) and original M4A (AAC).

---

### 🛡️ Enterprise Security & Hardening
- **🔒 SSRF & Loopback Protection**: Blocks loopback (`127.0.0.1`, `localhost`) and private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) to guard against server-side request forgery.
- **📂 Path Traversal & OS Folder Shield**: Restricts downloads to user-chosen directories and strictly prevents accidental writes to protected Windows system folders (`C:\Windows`, `Program Files`, root directories).
- **🛡️ Command Injection Shield**: Direct process execution via parameter arrays (`subprocess.Popen` without `shell=True`).
- **💣 Decompression Bomb Prevention**: Strict Pillow pixel limits (`25,000,000 max pixels`) and 5MB network caps for image previews.
- **🧹 Auto-Cleanup**: Automatically cleans up unfinished `.part` and `.ytdl` cache fragments upon download completion or user cancellation.

---

## 💻 Installation & Setup

### 🥇 Option 1: Standalone Windows Installer (Recommended for Users)
No Python, Git, or dependencies required!
1. Download **`SocialDart-Setup-v1.0.0.exe`** from the [Releases](https://github.com/chathunga2007/SocialDart-Video-Downloader-Desktop-App/releases) page (or compile it via Inno Setup).
2. Run the setup installer and follow the prompt.
3. Launch **SocialDart** directly from your Desktop or Start Menu!

---

### 🥈 Option 2: Run from Source (Developers)

#### Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.10 or higher
- Git

#### Step-by-Step Guide
1. **Clone the repository:**
   ```powershell
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

4. **Launch SocialDart:**
   - Double-click **`SocialDart.bat`** (or `SocialDart.vbs` for silent background execution), **OR**
   - Run from terminal:
     ```powershell
     python app.py
     ```

---

## 🔨 Building from Source

### 1. Build Standalone Portable Executable (`app.exe`)
To package SocialDart into a standalone, single-file Windows executable:
```powershell
python -m PyInstaller app.spec --clean -y
```
The compiled executable will be generated at `dist/app.exe`.

### 2. Compile Windows Setup Installer (`SocialDart-Setup-v1.0.0.exe`)
Make sure [Inno Setup 7](https://jrsoftware.org/isdl.php) is installed:
```powershell
& "C:\Program Files\Inno Setup 7\ISCC.exe" installer_script.iss
```
This packages the freshly built `dist/app.exe`, bundled `assets/ffmpeg.exe`, icons, and generates `SocialDart-Setup-v1.0.0.exe` in the root directory.

---

## 📁 Repository Structure

```
SocialDart-Desktop-Video-Downloader/
├── assets/
│   ├── ffmpeg.exe             # Bundled standalone FFmpeg 7.1 binary
│   ├── social-dart-logo.png   # Main official in-app vector-rendered logo
│   ├── taskbar_logo.png       # Dedicated Windows taskbar squircle icon
│   ├── social-dart.ico        # Multi-resolution window icon
│   └── taskbar.ico            # Taskbar multi-size application icon
├── app.py                     # Main CustomTkinter desktop UI application
├── downloader_engine.py       # Core yt-dlp downloading, anti-bot, & security engine
├── app.spec                   # PyInstaller bundle specification
├── installer_script.iss       # Inno Setup 7 installer compilation script
├── requirements.txt           # Python dependency requirements
├── SocialDart.bat             # Quick launch script (uses virtual environment)
├── SocialDart.vbs             # Silent windowless launcher
├── SocialDart.lnk             # Direct desktop shortcut
├── .gitignore                 # Git ignore rules (protects credentials & temp files)
└── README.md                  # Project documentation & guide
```

---

## 💡 Quick Tips & Troubleshooting

- **Direct Downloads:** For 95%+ of YouTube videos, TikToks, and Instagram Reels, simply paste the link and hit Download. **No cookies are needed!**
- **Bot Check Bypass:** If YouTube ever prompts a *"Sign in to confirm you're not a bot"* challenge (common on age-restricted or copyright-restricted music videos), click **`🍪 YT Cookies`** in the top bar and attach an exported `cookies.txt`.
- **Clipboard Paste:** Click the **Paste** button next to the input field to automatically insert your copied link and trigger instant inspection.
- **Destination Folder:** Click **Open Folder** anytime to view your downloaded videos in Windows File Explorer.

---

## 📜 License
Distributed under the **MIT License**. See `LICENSE` for details.

---

<p align="center">
  Crafted with ❤️ by <b>Chathunga Bimsara</b><br>
  <sub>If you find SocialDart useful, don't forget to star ⭐ this repository!</sub>
</p>
