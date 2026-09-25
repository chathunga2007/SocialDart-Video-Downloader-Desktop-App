"""
SocialDart - Desktop Social Media Video Downloader
A fast, beautiful, and feature-rich desktop video downloader for YouTube,
TikTok, Instagram, Facebook, X/Twitter, Threads, LinkedIn, Pinterest, and more.

Developed by Chathunga Bimsara
"""

import os
import sys
import ctypes
from ctypes import wintypes
import threading
import io
import time
import urllib.request
import webbrowser
import subprocess
from typing import Optional
from PIL import Image, ImageTk

# Set Windows AppUserModelID at process level
APP_AUMID = "SocialDart.Desktop.VideoDownloader.Pro"
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_AUMID)
except Exception:
    pass

import customtkinter as ctk
from tkinter import filedialog, messagebox

from downloader_engine import DownloaderEngine, PlatformInfo, FFMPEG_PATH, SecurityValidator


# Configure initial appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# ---------------------------------------------------------------------------
# Windows Native Property Store & Shell Integration for Taskbar Icon
# ---------------------------------------------------------------------------

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


class PROPERTYKEY(ctypes.Structure):
    _fields_ = [
        ("fmtid", wintypes.BYTE * 16),
        ("pid", wintypes.DWORD),
    ]


class PROPVARIANT(ctypes.Structure):
    _fields_ = [
        ("vt", wintypes.WORD),
        ("wReserved1", wintypes.WORD),
        ("wReserved2", wintypes.WORD),
        ("wReserved3", wintypes.WORD),
        ("pwszVal", wintypes.LPWSTR),
        ("dummy", wintypes.BYTE * 8),
    ]


class IPropertyStoreVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", ctypes.c_void_p),
        ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p),
        ("GetCount", ctypes.c_void_p),
        ("GetAt", ctypes.c_void_p),
        ("GetValue", ctypes.c_void_p),
        ("SetValue", ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(PROPERTYKEY), ctypes.POINTER(PROPVARIANT))),
        ("Commit", ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)),
    ]


class IPropertyStore(ctypes.Structure):
    _fields_ = [("lpVtbl", ctypes.POINTER(IPropertyStoreVtbl))]


def set_window_taskbar_identity(hwnd: int, app_id: str, ico_path: str):
    """Explicitly assign Taskbar identity and custom icon resource to the window."""
    try:
        ole32 = ctypes.windll.ole32
        propsys = ctypes.windll.propsys
        shell32 = ctypes.windll.shell32

        iid_propstore = GUID()
        ole32.IIDFromString("{886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99}", ctypes.byref(iid_propstore))

        pPropStore = ctypes.POINTER(IPropertyStore)()
        hr = shell32.SHGetPropertyStoreForWindow(hwnd, ctypes.byref(iid_propstore), ctypes.byref(pPropStore))

        if hr == 0 and pPropStore:
            # 1. Set PKEY_AppUserModel_ID
            pkey_app_id = PROPERTYKEY()
            propsys.PSPropertyKeyFromString("{9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3} 5", ctypes.byref(pkey_app_id))
            var_app_id = PROPVARIANT()
            var_app_id.vt = 31  # VT_LPWSTR
            var_app_id.pwszVal = app_id
            pPropStore.contents.lpVtbl.contents.SetValue(pPropStore, ctypes.byref(pkey_app_id), ctypes.byref(var_app_id))

            # 2. Set PKEY_AppUserModel_RelaunchIconResource with taskbar icon
            if ico_path and os.path.exists(ico_path):
                pkey_icon = PROPERTYKEY()
                propsys.PSPropertyKeyFromString("{9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3} 2", ctypes.byref(pkey_icon))
                var_icon = PROPVARIANT()
                var_icon.vt = 31
                var_icon.pwszVal = f"{ico_path},0"
                pPropStore.contents.lpVtbl.contents.SetValue(pPropStore, ctypes.byref(pkey_icon), ctypes.byref(var_icon))

            pPropStore.contents.lpVtbl.contents.Commit(pPropStore)
    except Exception:
        pass


class SocialDartApp(ctk.CTk):
    """Main Application Window for SocialDart with dynamic animations."""

    def __init__(self):
        super().__init__()

        # Engine initialization
        self.engine = DownloaderEngine()
        self.active_download_thread: Optional[threading.Thread] = None
        self.active_inspect_thread: Optional[threading.Thread] = None
        self.last_downloaded_path: Optional[str] = None
        self.current_thumbnail_img: Optional[ctk.CTkImage] = None
        self._url_debounce_timer: Optional[threading.Timer] = None
        self._last_inspected_url: str = ""
        self._is_inspecting: bool = False
        self._is_downloading: bool = False
        self._spinner_index: int = 0
        self._spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

        # Window Setup
        self.title("SocialDart - Universal HD & No-Watermark Downloader")
        self.geometry("1020x780")
        self.minsize(880, 660)
        self.resizable(True, True)

        # Default save directory (user's Downloads folder)
        self.save_dir = os.path.join(os.path.expanduser("~"), "Downloads")

        # Icons: Header uses official logo, Taskbar uses new taskbar-specific icon
        self.header_logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "social-dart-logo.png"))
        self.taskbar_ico_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "taskbar.ico"))
        if not os.path.exists(self.taskbar_ico_path):
            self.taskbar_ico_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "social-dart.ico"))

        # Set Window & Taskbar Icon
        self._set_app_icon()

        # Build UI
        self._build_ui()

        # Apply Native Windows Taskbar Integration
        self.after(100, self._apply_native_taskbar_integration)

    def _set_app_icon(self):
        """Set window icon using the new taskbar-specific icon."""
        if os.path.exists(self.taskbar_ico_path):
            try:
                self.iconbitmap(default=self.taskbar_ico_path)
                self.iconbitmap(self.taskbar_ico_path)
            except Exception:
                pass

    def _apply_native_taskbar_integration(self):
        """Apply Windows 10/11 Taskbar icon, AUMID, and WM_SETICON."""
        if not os.path.exists(self.taskbar_ico_path):
            return

        try:
            hwnd = int(self.wm_frame(), 16)
            if not hwnd:
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if not hwnd:
                hwnd = self.winfo_id()

            set_window_taskbar_identity(hwnd, APP_AUMID, self.taskbar_ico_path)

            user32 = ctypes.windll.user32
            LR_LOADFROMFILE = 0x00000010
            IMAGE_ICON = 1
            WM_SETICON = 0x0080

            hicon_big = user32.LoadImageW(None, self.taskbar_ico_path, IMAGE_ICON, 48, 48, LR_LOADFROMFILE)
            hicon_small = user32.LoadImageW(None, self.taskbar_ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)

            if hicon_big:
                user32.SendMessageW(hwnd, WM_SETICON, 1, hicon_big)
            if hicon_small:
                user32.SendMessageW(hwnd, WM_SETICON, 0, hicon_small)
        except Exception:
            pass

    def _build_ui(self):
        """Construct modern cyber-sleek UI layout with dynamic micro-animations."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------------------------------------------
        # 1. HEADER SECTION
        # ----------------------------------------------------
        header_frame = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#0D1117"),
            corner_radius=0,
            height=90,
            border_width=1,
            border_color=("#E2E8F0", "#1F2937"),
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)

        # Header Logo (Main Official SocialDart Logo)
        if os.path.exists(self.header_logo_path):
            try:
                pil_logo = Image.open(self.header_logo_path)
                self.logo_img = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(58, 58))
                logo_lbl = ctk.CTkLabel(header_frame, image=self.logo_img, text="")
                logo_lbl.grid(row=0, column=0, padx=(20, 14), pady=12)
            except Exception:
                pass

        # Title, Creator Credit & Tagline
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=1, sticky="w", pady=10)

        title_row = ctk.CTkFrame(title_box, fg_color="transparent")
        title_row.pack(anchor="w")

        app_title = ctk.CTkLabel(
            title_row,
            text="SocialDart",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=("#0284C7", "#38BDF8"),
        )
        app_title.pack(side="left")

        # Developer Credit Badge
        self.dev_pill = ctk.CTkLabel(
            title_row,
            text="⚡ Developed by Chathunga Bimsara",
            fg_color=("#EEF2FF", "#1E1B4B"),
            text_color=("#4F46E5", "#A5B4FC"),
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            padx=10,
            pady=3,
        )
        self.dev_pill.pack(side="left", padx=10)

        app_subtitle = ctk.CTkLabel(
            title_box,
            text="Universal HD & No-Watermark Media Downloader • Download • Save • Enjoy",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#475569", "#94A3B8"),
        )
        app_subtitle.pack(anchor="w", pady=(2, 0))

        # Header Right Controls: Theme Switcher & Engine Status
        right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_box.grid(row=0, column=2, padx=20, pady=12, sticky="e")

        # High-Contrast Theme Switcher
        theme_box = ctk.CTkFrame(right_box, fg_color="transparent")
        theme_box.pack(side="top", anchor="e", pady=(0, 6))

        theme_lbl = ctk.CTkLabel(
            theme_box,
            text="Theme Mode:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#334155", "#94A3B8"),
        )
        theme_lbl.pack(side="left", padx=(0, 6))

        self.theme_selector = ctk.CTkSegmentedButton(
            theme_box,
            values=["🌙 Dark", "☀️ Light"],
            command=self._on_theme_toggle,
            width=140,
            height=30,
            corner_radius=8,
            selected_color="#0284C7",
            selected_hover_color="#0369A1",
            unselected_color=("#E2E8F0", "#1E293B"),
            unselected_hover_color=("#CBD5E1", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        )
        self.theme_selector.set("🌙 Dark")
        self.theme_selector.pack(side="left")

        # Header Tools Row: Cookie Manager Button & Engine Badge
        tools_row = ctk.CTkFrame(right_box, fg_color="transparent")
        tools_row.pack(side="top", anchor="e")

        self.cookie_btn = ctk.CTkButton(
            tools_row,
            text="🍪 YT Cookies",
            command=self._open_cookie_modal,
            height=28,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            border_width=1,
            cursor="hand2",
        )
        self.cookie_btn.pack(side="left", padx=(0, 8))

        # Engine Status Badge
        badge_text = "⚡ FFmpeg 7.1 Ready" if FFMPEG_PATH else "⚡ Standard Engine Ready"
        self.engine_badge = ctk.CTkLabel(
            tools_row,
            text=badge_text,
            fg_color=("#ECFDF5", "#064E3B"),
            text_color=("#059669", "#34D399"),
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            padx=10,
            pady=4,
        )
        self.engine_badge.pack(side="left")

        self._update_cookie_button_state()

        # ----------------------------------------------------
        # 2. SCROLLABLE BODY
        # ----------------------------------------------------
        self.scroll_body = ctk.CTkScrollableFrame(
            self,
            fg_color=("#F1F5F9", "#0B0F19"),
            corner_radius=0,
            scrollbar_button_color=("#CBD5E1", "#334155"),
            scrollbar_button_hover_color=("#94A3B8", "#475569"),
        )
        self.scroll_body.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.scroll_body.grid_columnconfigure(0, weight=1)

        # Platform Supported Pills Bar with interactive micro-animations
        self._build_platform_chips(self.scroll_body)

        # Input Box & Action Controls
        self._build_input_section(self.scroll_body)

        # Video Preview & Details Card
        self._build_preview_card(self.scroll_body)

        # Download Options & Folder Selector
        self._build_options_card(self.scroll_body)

        # Progress Bar & Control Buttons
        self._build_progress_section(self.scroll_body)

        # ----------------------------------------------------
        # 3. BOTTOM STATUS BAR
        # ----------------------------------------------------
        status_bar = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#0D1117"),
            height=34,
            corner_radius=0,
            border_width=1,
            border_color=("#E2E8F0", "#1F2937"),
        )
        status_bar.grid(row=2, column=0, sticky="ew")
        status_bar.grid_columnconfigure(0, weight=1)

        self.footer_status = ctk.CTkLabel(
            status_bar,
            text="Ready • Paste any video link (YouTube, TikTok, Instagram, FB, X, Threads) for instant auto-detection",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#475569", "#94A3B8"),
            anchor="w",
        )
        self.footer_status.grid(row=0, column=0, padx=20, pady=6, sticky="w")

        version_lbl = ctk.CTkLabel(
            status_bar,
            text="SocialDart v1.0 Ultra • By Chathunga Bimsara",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#0284C7", "#38BDF8"),
        )
        version_lbl.grid(row=0, column=1, padx=20, pady=6, sticky="e")

    def _on_theme_toggle(self, value):
        """Toggle between Dark Mode and Light Mode."""
        if "Dark" in value:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")
        self.after(50, self._apply_native_taskbar_integration)

    def _update_cookie_button_state(self):
        """Update the cookie button label and color based on active cookies."""
        cookie_file = self.engine.get_cookie_file()
        if cookie_file:
            is_valid, has_yt, _ = self.engine.validate_cookie_file(cookie_file)
            if has_yt:
                self.cookie_btn.configure(
                    text="🍪 Cookies Active ✅",
                    fg_color=("#ECFDF5", "#064E3B"),
                    hover_color=("#D1FAE5", "#065F46"),
                    text_color=("#059669", "#34D399"),
                    border_color=("#6EE7B7", "#059669"),
                )
            else:
                self.cookie_btn.configure(
                    text="🍪 Cookies (No YT) ⚠️",
                    fg_color=("#FEF3C7", "#78350F"),
                    hover_color=("#FDE68A", "#92400E"),
                    text_color=("#D97706", "#FBBF24"),
                    border_color=("#FCD34D", "#D97706"),
                )
        else:
            self.cookie_btn.configure(
                text="🍪 YT Cookies ⚙️",
                fg_color=("#F8FAFC", "#1E293B"),
                hover_color=("#F1F5F9", "#334155"),
                text_color=("#475569", "#94A3B8"),
                border_color=("#CBD5E1", "#475569"),
            )

    def _open_cookie_modal(self):
        """Open modern YouTube Cookie Manager modal dialog."""
        modal = ctk.CTkToplevel(self)
        modal.title("YouTube Cookie Manager - SocialDart")
        modal.geometry("620x540")
        modal.minsize(580, 500)
        modal.resizable(False, False)
        modal.transient(self)
        modal.grab_set()

        # Center modal over main window
        try:
            x = self.winfo_x() + (self.winfo_width() // 2) - 310
            y = self.winfo_y() + (self.winfo_height() // 2) - 270
            modal.geometry(f"+{max(50, x)}+{max(50, y)}")
        except Exception:
            pass

        content = ctk.CTkFrame(
            modal,
            fg_color=("#FFFFFF", "#0D1117"),
            corner_radius=0,
        )
        content.pack(fill="both", expand=True, padx=22, pady=22)

        # Header Title
        title_lbl = ctk.CTkLabel(
            content,
            text="🍪 YouTube Cookie Manager",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=("#0284C7", "#38BDF8"),
        )
        title_lbl.pack(anchor="w", pady=(0, 4))

        desc_lbl = ctk.CTkLabel(
            content,
            text="Bypass YouTube 'Sign in to confirm you're not a bot' challenges & download restricted / music videos seamlessly.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#64748B", "#94A3B8"),
            wraplength=560,
            justify="left",
        )
        desc_lbl.pack(anchor="w", pady=(0, 15))

        # Status Card
        status_card = ctk.CTkFrame(
            content,
            fg_color=("#F8FAFC", "#161B22"),
            corner_radius=10,
            border_width=1,
            border_color=("#E2E8F0", "#30363D"),
        )
        status_card.pack(fill="x", pady=(0, 15), padx=2)

        status_header = ctk.CTkLabel(
            status_card,
            text="Active Status:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#475569", "#94A3B8"),
        )
        status_header.pack(anchor="w", padx=14, pady=(10, 2))

        status_val_lbl = ctk.CTkLabel(
            status_card,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            wraplength=540,
            justify="left",
        )
        status_val_lbl.pack(anchor="w", padx=14, pady=(0, 10))

        def _refresh_status():
            cookie = self.engine.get_cookie_file()
            if cookie:
                try:
                    size_kb = os.path.getsize(cookie) / 1024
                    filename = os.path.basename(cookie)
                    is_valid, has_yt, msg = self.engine.validate_cookie_file(cookie)
                    if has_yt:
                        status_val_lbl.configure(
                            text=f"✅ Active: {filename} ({size_kb:.1f} KB)\n📍 Status: Verified YouTube Session Active!\n📁 Path: {cookie}",
                            text_color=("#15803D", "#34D399"),
                        )
                    else:
                        status_val_lbl.configure(
                            text=f"⚠️ Notice: {filename} ({size_kb:.1f} KB)\n⚠️ Warning: No YouTube cookies detected in this file!\n📁 Path: {cookie}",
                            text_color=("#D97706", "#FBBF24"),
                        )
                except Exception:
                    status_val_lbl.configure(
                        text=f"✅ Active: {cookie}",
                        text_color=("#15803D", "#34D399"),
                    )
            else:
                status_val_lbl.configure(
                    text="⚡ Standard Engine Ready (Direct YouTube downloads enabled).\n💡 If YouTube prompts a bot check, attach your exported cookies.txt here.",
                    text_color=("#0284C7", "#38BDF8"),
                )

        _refresh_status()

        # Action Buttons
        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 15))

        def _import_cookie():
            selected = filedialog.askopenfilename(
                title="Select Exported cookies.txt",
                filetypes=[("Text / Cookie Files", "*.txt"), ("All Files", "*.*")],
                parent=modal,
            )
            if selected and os.path.exists(selected):
                is_valid, has_yt, msg = self.engine.validate_cookie_file(selected)
                dest = os.path.abspath(os.path.join(os.path.dirname(__file__), "cookies.txt"))
                try:
                    import shutil
                    shutil.copy2(selected, dest)
                    self.engine.set_cookie_file(dest)
                except Exception:
                    self.engine.set_cookie_file(selected)

                self._update_cookie_button_state()
                _refresh_status()
                if has_yt:
                    messagebox.showinfo(
                        "Cookies Loaded Successfully",
                        "cookies.txt is now active with verified YouTube session credentials!\n\nAll YouTube videos can now be downloaded without bot interruptions.",
                        parent=modal,
                    )
                else:
                    messagebox.showwarning(
                        "Cookie Notice",
                        "The imported cookies.txt does not appear to contain YouTube session cookies.\n\nMake sure to visit youtube.com while logged in before exporting cookies.",
                        parent=modal,
                    )

        def _clear_cookie():
            local_dest = os.path.abspath(os.path.join(os.path.dirname(__file__), "cookies.txt"))
            if os.path.exists(local_dest):
                try:
                    os.remove(local_dest)
                except Exception:
                    pass
            self.engine.set_cookie_file(None)
            self._update_cookie_button_state()
            _refresh_status()
            messagebox.showinfo("Cookies Removed", "YouTube cookies have been cleared.", parent=modal)

        import_btn = ctk.CTkButton(
            btn_row,
            text="📁 Import cookies.txt File",
            command=_import_cookie,
            height=34,
            corner_radius=8,
            fg_color="#0284C7",
            hover_color="#0369A1",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            cursor="hand2",
        )
        import_btn.pack(side="left", padx=(0, 10))

        clear_btn = ctk.CTkButton(
            btn_row,
            text="🗑️ Remove Cookies",
            command=_clear_cookie,
            height=34,
            corner_radius=8,
            fg_color=("#F1F5F9", "#21262D"),
            hover_color=("#E2E8F0", "#30363D"),
            text_color=("#EF4444", "#F87171"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            cursor="hand2",
        )
        clear_btn.pack(side="left")

        # Guide / Instructions Card
        guide_card = ctk.CTkFrame(
            content,
            fg_color=("#F1F5F9", "#161B22"),
            corner_radius=10,
            border_width=1,
            border_color=("#E2E8F0", "#30363D"),
        )
        guide_card.pack(fill="both", expand=True, pady=(0, 15), padx=2)

        guide_title = ctk.CTkLabel(
            guide_card,
            text="⚡ How to export cookies in 20 seconds (Quick & Easy Guide):",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        guide_title.pack(anchor="w", padx=14, pady=(10, 4))

        guide_steps = (
            "1. In Chrome, Brave or Edge, install the free extension 'Get cookies.txt LOCALLY'.\n"
            "2. Visit youtube.com while logged into your Google / YouTube account.\n"
            "3. Click the extension icon and click 'Export' to download cookies.txt.\n"
            "4. Click 'Import cookies.txt File' above and select your downloaded file."
        )
        guide_steps_lbl = ctk.CTkLabel(
            guide_card,
            text=guide_steps,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#475569", "#94A3B8"),
            justify="left",
        )
        guide_steps_lbl.pack(anchor="w", padx=14, pady=(0, 6))

        ext_url = "https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
        ext_btn = ctk.CTkButton(
            guide_card,
            text="🌐 Get Extension for Chrome / Brave / Edge (Web Store)",
            command=lambda: webbrowser.open(ext_url),
            height=28,
            corner_radius=6,
            fg_color=("#E0F2FE", "#1E293B"),
            hover_color=("#BAE6FD", "#334155"),
            text_color=("#0284C7", "#38BDF8"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            cursor="hand2",
        )
        ext_btn.pack(anchor="w", padx=14, pady=(0, 10))

        # Close button
        close_btn = ctk.CTkButton(
            content,
            text="Close",
            command=modal.destroy,
            height=30,
            width=100,
            corner_radius=8,
            fg_color=("#E2E8F0", "#21262D"),
            hover_color=("#CBD5E1", "#30363D"),
            text_color=("#334155", "#E6EDF3"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            cursor="hand2",
        )
        close_btn.pack(anchor="e")

    def _build_platform_chips(self, parent):
        """Render supported social media platform badges with hover animations."""
        chips_frame = ctk.CTkFrame(
            parent,
            fg_color=("#FFFFFF", "#111827"),
            corner_radius=12,
            border_width=1,
            border_color=("#E2E8F0", "#1F2937"),
        )
        chips_frame.pack(fill="x", padx=20, pady=(15, 10))

        lbl = ctk.CTkLabel(
            chips_frame,
            text="Supported Platforms:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#334155", "#94A3B8"),
        )
        lbl.pack(side="left", padx=(16, 10), pady=10)

        platforms = [
            ("▶ YouTube", "#DC2626"),
            ("🎵 TikTok (No-WM)", "#0891B2"),
            ("📸 Instagram", "#DB2777"),
            ("👥 Facebook", "#2563EB"),
            ("𝕏 Twitter", "#0284C7"),
            ("🧵 Threads", "#7C3AED"),
            ("💼 LinkedIn", "#0369A1"),
            ("📌 Pinterest", "#E11D48"),
        ]

        self.platform_pills = []
        for name, col in platforms:
            pill = ctk.CTkButton(
                chips_frame,
                text=name,
                fg_color=("#F1F5F9", "#1E293B"),
                hover_color=("#E2E8F0", "#334155"),
                text_color=col,
                corner_radius=8,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                height=28,
                width=10,
                command=lambda n=name: self._on_platform_chip_clicked(n),
            )
            pill.pack(side="left", padx=4, pady=8)
            self.platform_pills.append(pill)

    def _on_platform_chip_clicked(self, platform_name: str):
        """Quick interaction when clicking a platform badge."""
        self.footer_status.configure(
            text=f"Ready to download from {platform_name} • Paste your link above!"
        )

    def _build_input_section(self, parent):
        """Render URL entry bar with auto-detect and animated action buttons."""
        self.input_card = ctk.CTkFrame(
            parent,
            fg_color=("#FFFFFF", "#161E2E"),
            corner_radius=14,
            border_width=1,
            border_color=("#E2E8F0", "#1F293D"),
        )
        self.input_card.pack(fill="x", padx=20, pady=10)
        self.input_card.grid_columnconfigure(0, weight=1)

        input_title = ctk.CTkLabel(
            self.input_card,
            text="Enter Video or Media Link (Auto-Detect Enabled):",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#0F172A", "#E2E8F0"),
        )
        input_title.grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(14, 6))

        # Input Row with high-contrast borders and text
        self.url_entry = ctk.CTkEntry(
            self.input_card,
            placeholder_text="Paste your video link here (YouTube, TikTok, Instagram, FB, X, Threads...)",
            placeholder_text_color=("#94A3B8", "#64748B"),
            height=46,
            corner_radius=10,
            fg_color=("#F8FAFC", "#0F172A"),
            border_color=("#CBD5E1", "#334155"),
            border_width=1.5,
            text_color=("#0F172A", "#F8FAFC"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=(16, 8), pady=(0, 16))
        self.url_entry.bind("<Return>", lambda e: self.start_inspect_thread())
        self.url_entry.bind("<KeyRelease>", self._on_url_key_release)

        # Paste Button with click micro-animation
        self.paste_btn = ctk.CTkButton(
            self.input_card,
            text="📋 Paste",
            command=self.paste_from_clipboard,
            width=92,
            height=46,
            corner_radius=10,
            fg_color=("#F1F5F9", "#1E293B"),
            hover_color=("#E2E8F0", "#334155"),
            text_color=("#0284C7", "#38BDF8"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        )
        self.paste_btn.grid(row=1, column=1, padx=(0, 8), pady=(0, 16))

        # Inspect Button with animated loading state
        self.inspect_btn = ctk.CTkButton(
            self.input_card,
            text="🔍 Inspect",
            command=self.start_inspect_thread,
            width=96,
            height=46,
            corner_radius=10,
            fg_color="#0284C7",
            hover_color="#0369A1",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        )
        self.inspect_btn.grid(row=1, column=2, padx=(0, 8), pady=(0, 16))

        # Clear Button with flash animation
        self.clear_btn = ctk.CTkButton(
            self.input_card,
            text="✕ Clear",
            command=self.clear_input,
            width=80,
            height=46,
            corner_radius=10,
            fg_color=("#FEE2E2", "#1E293B"),
            hover_color=("#FECACA", "#334155"),
            text_color=("#DC2626", "#F87171"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        )
        self.clear_btn.grid(row=1, column=3, padx=(0, 16), pady=(0, 16))

    def _build_preview_card(self, parent):
        """Render live video metadata preview card with crisp high contrast and dynamic border glow."""
        self.preview_frame = ctk.CTkFrame(
            parent,
            fg_color=("#FFFFFF", "#161E2E"),
            corner_radius=14,
            border_width=1.5,
            border_color=("#E2E8F0", "#1F293D"),
        )
        self.preview_frame.pack(fill="x", padx=20, pady=10)
        self.preview_frame.grid_columnconfigure(1, weight=1)

        # 16:9 Thumbnail Box
        self.thumb_container = ctk.CTkFrame(
            self.preview_frame,
            width=176,
            height=106,
            corner_radius=10,
            fg_color=("#E2E8F0", "#0F172A"),
            border_width=1,
            border_color=("#CBD5E1", "#1E293B"),
        )
        self.thumb_container.grid(row=0, column=0, padx=16, pady=16, sticky="nw")
        self.thumb_container.grid_propagate(False)

        # Blank placeholder
        blank_pil = Image.new("RGBA", (176, 106), (226, 232, 240, 255))
        self.empty_thumb = ctk.CTkImage(light_image=blank_pil, dark_image=blank_pil, size=(176, 106))

        self.thumb_label = ctk.CTkLabel(
            self.thumb_container,
            text="🎬 No Preview",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#64748B", "#64748B"),
        )
        self.thumb_label.place(relx=0.5, rely=0.5, anchor="center")

        # Metadata container
        meta_box = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        meta_box.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        meta_box.grid_columnconfigure(0, weight=1)

        # Platform Badge & Watermark Badge Row
        badges_row = ctk.CTkFrame(meta_box, fg_color="transparent")
        badges_row.pack(fill="x", anchor="w")

        self.platform_badge = ctk.CTkLabel(
            badges_row,
            text="🌐 Media Link",
            fg_color=("#E0F2FE", "#1E293B"),
            text_color=("#0284C7", "#38BDF8"),
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            padx=10,
            pady=4,
        )
        self.platform_badge.pack(side="left", padx=(0, 8))

        self.wm_badge = ctk.CTkLabel(
            badges_row,
            text="✨ No Watermark Clean Download",
            fg_color=("#DCFCE7", "#064E3B"),
            text_color=("#15803D", "#34D399"),
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            padx=10,
            pady=4,
        )
        self.wm_badge.pack(side="left")

        # Video Title
        self.preview_title = ctk.CTkLabel(
            meta_box,
            text="Paste a link to view title and details",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=("#0F172A", "#F1F5F9"),
            anchor="w",
            wraplength=540,
            justify="left",
        )
        self.preview_title.pack(fill="x", anchor="w", pady=(8, 4))

        # Channel & Duration Info
        self.preview_details = ctk.CTkLabel(
            meta_box,
            text="Creator: --  •  Duration: --:--",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#475569", "#94A3B8"),
            anchor="w",
        )
        self.preview_details.pack(fill="x", anchor="w")

    def _build_options_card(self, parent):
        """Render download format options (Video vs Audio) and save directory."""
        card = ctk.CTkFrame(
            parent,
            fg_color=("#FFFFFF", "#161E2E"),
            corner_radius=14,
            border_width=1,
            border_color=("#E2E8F0", "#1F293D"),
        )
        card.pack(fill="x", padx=20, pady=10)
        card.grid_columnconfigure(0, weight=1)

        # Format & Type Selector
        type_header_row = ctk.CTkFrame(card, fg_color="transparent")
        type_header_row.pack(fill="x", padx=16, pady=(14, 8))

        sec1 = ctk.CTkLabel(
            type_header_row,
            text="Select Download Type:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#0F172A", "#E2E8F0"),
        )
        sec1.pack(side="left")

        # Video vs Audio Tab with explicit text_color for both Light and Dark modes
        self.media_type_var = ctk.StringVar(value="🎬 Video (MP4)")
        self.media_type_selector = ctk.CTkSegmentedButton(
            type_header_row,
            values=["🎬 Video (MP4)", "🎵 Audio Only"],
            variable=self.media_type_var,
            command=self._on_media_type_changed,
            width=280,
            height=34,
            corner_radius=8,
            selected_color="#0284C7",
            selected_hover_color="#0369A1",
            unselected_color=("#E2E8F0", "#1E293B"),
            unselected_hover_color=("#CBD5E1", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        )
        self.media_type_selector.pack(side="right")

        # Quality Selector with explicit text_color
        self.quality_var = ctk.StringVar(value="⭐ Best Available")
        self.video_qualities = [
            "⭐ Best Available",
            "📺 1080p Full HD",
            "📱 720p HD",
            "⚡ 480p SD",
        ]
        self.audio_qualities = [
            "🎧 MP3 (320k High Quality)",
            "🎼 MP3 (192k Standard)",
            "📻 M4A (Original Quality)",
        ]

        self.quality_selector = ctk.CTkSegmentedButton(
            card,
            values=self.video_qualities,
            variable=self.quality_var,
            corner_radius=10,
            selected_color="#0284C7",
            selected_hover_color="#0369A1",
            unselected_color=("#E2E8F0", "#1E293B"),
            unselected_hover_color=("#CBD5E1", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=40,
        )
        self.quality_selector.pack(fill="x", padx=16, pady=(0, 16))

        # Save Directory Section
        sec2 = ctk.CTkLabel(
            card,
            text="Save Destination Folder:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#0F172A", "#E2E8F0"),
        )
        sec2.pack(anchor="w", padx=16, pady=(4, 6))

        dir_frame = ctk.CTkFrame(card, fg_color="transparent")
        dir_frame.pack(fill="x", padx=16, pady=(0, 16))
        dir_frame.grid_columnconfigure(0, weight=1)

        self.path_entry = ctk.CTkEntry(
            dir_frame,
            height=40,
            corner_radius=8,
            fg_color=("#F8FAFC", "#0F172A"),
            border_color=("#CBD5E1", "#334155"),
            border_width=1.5,
            text_color=("#0F172A", "#F8FAFC"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.path_entry.insert(0, self.save_dir)
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        browse_btn = ctk.CTkButton(
            dir_frame,
            text="📂 Browse",
            command=self.choose_save_directory,
            width=100,
            height=40,
            corner_radius=8,
            fg_color=("#F1F5F9", "#1E293B"),
            hover_color=("#E2E8F0", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        )
        browse_btn.grid(row=0, column=1, padx=(0, 8))

        self.open_folder_btn = ctk.CTkButton(
            dir_frame,
            text="📁 Open Folder",
            command=self.open_download_folder,
            width=110,
            height=40,
            corner_radius=8,
            fg_color=("#F1F5F9", "#1E293B"),
            hover_color=("#E2E8F0", "#334155"),
            text_color=("#15803D", "#34D399"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        )
        self.open_folder_btn.grid(row=0, column=2)

    def _on_media_type_changed(self, value):
        """Switch between Video and Audio format selections with preserved text_color."""
        if "Audio" in value:
            self.quality_selector.configure(
                values=self.audio_qualities,
                text_color=("#0F172A", "#F8FAFC"),
            )
            self.quality_var.set("🎧 MP3 (320k High Quality)")
            self.download_btn.configure(text="⬇️ Download Audio (High Quality)")
        else:
            self.quality_selector.configure(
                values=self.video_qualities,
                text_color=("#0F172A", "#F8FAFC"),
            )
            self.quality_var.set("⭐ Best Available")
            self.download_btn.configure(text="⬇️ Download Video (No Watermark)")

    def _build_progress_section(self, parent):
        """Render download progress bar, stats, and primary action buttons."""
        card = ctk.CTkFrame(
            parent,
            fg_color=("#FFFFFF", "#161E2E"),
            corner_radius=14,
            border_width=1,
            border_color=("#E2E8F0", "#1F293D"),
        )
        card.pack(fill="x", padx=20, pady=(10, 20))
        card.grid_columnconfigure(0, weight=1)

        # Progress Header (Status & Speed)
        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(14, 6))

        self.progress_status_lbl = ctk.CTkLabel(
            header_row,
            text="Status: Ready",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#0284C7", "#38BDF8"),
            anchor="w",
        )
        self.progress_status_lbl.pack(side="left")

        self.progress_stats_lbl = ctk.CTkLabel(
            header_row,
            text="Speed: --  |  Size: --  |  ETA: --",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#475569", "#94A3B8"),
            anchor="e",
        )
        self.progress_stats_lbl.pack(side="right")

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            card,
            height=16,
            corner_radius=8,
            progress_color="#0284C7",
            fg_color=("#E2E8F0", "#0F172A"),
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=16, pady=(4, 16))

        # Action Buttons Row
        action_row = ctk.CTkFrame(card, fg_color="transparent")
        action_row.pack(fill="x", padx=16, pady=(0, 16))
        action_row.grid_columnconfigure(0, weight=1)

        # Primary Download Button with Vibrant Hover & Glow
        self.download_btn = ctk.CTkButton(
            action_row,
            text="⬇️ Download Video (No Watermark)",
            command=self.start_download_thread,
            height=50,
            corner_radius=12,
            fg_color="#0284C7",
            hover_color="#0369A1",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        )
        self.download_btn.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            action_row,
            text="⏹ Cancel",
            command=self.cancel_download,
            height=50,
            width=120,
            corner_radius=12,
            fg_color=("#F1F5F9", "#1E293B"),
            hover_color=("#EF4444", "#DC2626"),
            text_color=("#64748B", "#94A3B8"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            state="disabled",
        )
        self.cancel_btn.grid(row=0, column=1)

    # ----------------------------------------------------
    # UI EVENT HANDLERS & MICRO-ANIMATIONS
    # ----------------------------------------------------

    def _on_url_key_release(self, event=None):
        """Update platform badge dynamically and debounce auto-inspection."""
        url = self.url_entry.get().strip()
        
        if not url:
            self._reset_preview_card()
            return

        meta = PlatformInfo.detect(url)
        self.platform_badge.configure(text=meta["badge"], text_color=meta["color"])
        if meta["no_watermark"]:
            self.wm_badge.configure(text="✨ No Watermark Clean Download", text_color=("#15803D", "#34D399"))
        else:
            self.wm_badge.configure(text="✓ High Definition Stream", text_color=("#0284C7", "#38BDF8"))

        # Highlight input card border with active glow
        self.input_card.configure(border_color=("#0284C7", "#38BDF8"))

        # Auto-detect Debounce
        if url != self._last_inspected_url and (url.startswith("http://") or url.startswith("https://")):
            if self._url_debounce_timer:
                self._url_debounce_timer.cancel()
            self._url_debounce_timer = threading.Timer(0.4, self._trigger_auto_inspect, args=(url,))
            self._url_debounce_timer.start()

    def _trigger_auto_inspect(self, url: str):
        """Callback from debounce timer on background thread."""
        current_url = self.url_entry.get().strip()
        if current_url == url:
            self.after(0, self.start_inspect_thread)

    def _reset_preview_card(self):
        """Completely reset the preview card back to clean initial state."""
        self._last_inspected_url = ""
        self.input_card.configure(border_color=("#E2E8F0", "#1F293D"))
        self.preview_frame.configure(border_color=("#E2E8F0", "#1F293D"))
        self.platform_badge.configure(text="🌐 Media Link", text_color=("#0284C7", "#38BDF8"))
        self.wm_badge.configure(text="✨ No Watermark Clean Download", text_color=("#15803D", "#34D399"))
        self.preview_title.configure(text="Paste a link to view title and details")
        self.preview_details.configure(text="Creator: --  •  Duration: --:--")
        
        # Wipe thumbnail clean
        self.current_thumbnail_img = None
        self.thumb_label.configure(image=self.empty_thumb, text="🎬 No Preview")
        
        self.progress_bar.set(0)
        self.progress_status_lbl.configure(text="Status: Ready", text_color=("#0284C7", "#38BDF8"))
        self.progress_stats_lbl.configure(text="Speed: --  |  Size: --  |  ETA: --")
        self.footer_status.configure(text="Ready • Paste any video link to inspect")

    def paste_from_clipboard(self):
        """Paste clipboard content into URL entry with flash micro-animation."""
        try:
            clipboard_text = self.clipboard_get().strip()
            if clipboard_text:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, clipboard_text)
                
                # Visual click flash animation on Paste Button
                self.paste_btn.configure(text="✓ Pasted!", fg_color="#10B981", text_color="#FFFFFF")
                self.after(700, lambda: self.paste_btn.configure(
                    text="📋 Paste",
                    fg_color=("#F1F5F9", "#1E293B"),
                    text_color=("#0284C7", "#38BDF8")
                ))
                
                self._on_url_key_release()
                self.start_inspect_thread()
        except Exception:
            pass

    def clear_input(self):
        """Clear URL input with flash micro-animation."""
        self.url_entry.delete(0, "end")
        self._reset_preview_card()
        
        # Visual flash animation on Clear Button
        self.clear_btn.configure(text="✓ Cleared", fg_color="#EF4444", text_color="#FFFFFF")
        self.after(600, lambda: self.clear_btn.configure(
            text="✕ Clear",
            fg_color=("#FEE2E2", "#1E293B"),
            text_color=("#DC2626", "#F87171")
        ))

    def choose_save_directory(self):
        """Open folder browser dialog to pick download directory with security checks."""
        chosen = filedialog.askdirectory(initialdir=self.save_dir, title="Select Download Folder")
        if chosen:
            is_safe, res = SecurityValidator.is_safe_directory(chosen)
            if not is_safe:
                messagebox.showerror("Security Warning", f"Cannot save to the selected folder:\n\n{res}")
                return
            self.save_dir = res
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, res)

    def open_download_folder(self):
        """Open the downloads directory or reveal downloaded file in File Explorer securely without shell=True."""
        folder = self.path_entry.get().strip() or self.save_dir
        if self.last_downloaded_path and os.path.exists(self.last_downloaded_path):
            try:
                norm_file = os.path.abspath(os.path.normpath(self.last_downloaded_path))
                subprocess.Popen(["explorer.exe", f"/select,{norm_file}"], shell=False)
                return
            except Exception:
                pass

        if os.path.exists(folder):
            try:
                norm_folder = os.path.abspath(os.path.normpath(folder))
                subprocess.Popen(["explorer.exe", norm_folder], shell=False)
            except Exception:
                webbrowser.open(folder)
        else:
            messagebox.showwarning("Folder Not Found", f"Directory does not exist:\n{folder}")

    # ----------------------------------------------------
    # MEDIA INSPECTION & ANIMATIONS
    # ----------------------------------------------------

    def start_inspect_thread(self):
        """Start metadata extraction with animated spinner state."""
        url = self.url_entry.get().strip()
        if not url:
            return

        self._last_inspected_url = url
        self._is_inspecting = True
        self.inspect_btn.configure(state="disabled")
        self.footer_status.configure(text="Fetching video details and formats...")
        self.progress_status_lbl.configure(text="Status: Inspecting link...", text_color=("#0284C7", "#38BDF8"))
        
        # Start spinner animation on inspect button
        self._animate_inspect_button()

        thread = threading.Thread(target=self._run_inspect, args=(url,))
        thread.daemon = True
        thread.start()

    def _animate_inspect_button(self):
        """Looping spinner animation while inspecting."""
        if self._is_inspecting:
            char = self._spinner_chars[self._spinner_index % len(self._spinner_chars)]
            self._spinner_index += 1
            self.inspect_btn.configure(text=f"{char} Checking...")
            self.after(100, self._animate_inspect_button)

    def _run_inspect(self, url: str):
        """Background metadata inspection worker."""
        meta = self.engine.fetch_metadata(url)
        self.after(0, lambda: self._on_inspect_complete(meta))

    def _on_inspect_complete(self, meta: dict):
        """Update UI with fetched metadata on the main thread."""
        self._is_inspecting = False
        self.inspect_btn.configure(state="normal", text="🔍 Inspect")
        
        current_url = self.url_entry.get().strip()
        if not current_url:
            self._reset_preview_card()
            return

        if meta.get("success"):
            # Glowing border animation on preview card
            self.preview_frame.configure(border_color=("#0284C7", "#38BDF8"))

            self.preview_title.configure(text=meta["title"])
            self.preview_details.configure(
                text=f"Creator: {meta['uploader']}  •  Duration: {meta['duration']}  •  Platform: {meta['platform']}"
            )
            self.platform_badge.configure(text=meta["platform_badge"], text_color=meta["platform_color"])
            
            if meta.get("no_watermark"):
                self.wm_badge.configure(text="✨ No Watermark Clean Stream", text_color=("#15803D", "#34D399"))
            else:
                self.wm_badge.configure(text="✓ High Definition Stream", text_color=("#0284C7", "#38BDF8"))

            # Load thumbnail asynchronously
            thumb_url = meta.get("thumbnail_url")
            if thumb_url:
                threading.Thread(target=self._load_thumbnail, args=(thumb_url,), daemon=True).start()
            else:
                self.thumb_label.configure(image=self.empty_thumb, text="🎬 No Preview")

            self.footer_status.configure(text=f"Ready to download: {meta['title'][:60]}")
            self.progress_status_lbl.configure(text="Status: Video details loaded ✨", text_color=("#15803D", "#34D399"))
        else:
            err_msg = meta.get("error", "Failed to fetch metadata")
            lower_err = err_msg.lower()
            if "bot" in lower_err or "cookies" in lower_err:
                self.preview_frame.configure(border_color=("#F59E0B", "#D97706"))
                self.footer_status.configure(text="YouTube Bot Verification required for this video.")
                self.progress_status_lbl.configure(
                    text="⚠️ YouTube Bot Check: Click '🍪 Cookies' in top bar to unlock!",
                    text_color="#F59E0B",
                )
                self.preview_title.configure(text="🔒 YouTube Sign-in Verification Required")
                self.preview_details.configure(
                    text="YouTube requires an authenticated session for this video. Click '🍪 Cookies' in the top bar to attach cookies.txt."
                )
            else:
                self.preview_frame.configure(border_color=("#E2E8F0", "#1F293D"))
                self.footer_status.configure(text=f"Inspection note: {err_msg[:60]}")
                self.progress_status_lbl.configure(text="Status: Ready (Metadata skipped)", text_color=("#64748B", "#94A3B8"))

    def _load_thumbnail(self, thumb_url: str):
        """Fetch and render thumbnail image safely with decompression bomb and memory protections."""
        is_safe, _ = SecurityValidator.is_safe_url(thumb_url)
        if not is_safe:
            return

        try:
            # Prevent decompression bomb attacks
            Image.MAX_IMAGE_PIXELS = 25_000_000

            req = urllib.request.Request(thumb_url, headers={"User-Agent": "SocialDart-App/1.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                # Limit thumbnail download to max 5MB
                img_data = response.read(5 * 1024 * 1024)
            pil_img = Image.open(io.BytesIO(img_data))
            
            pil_img.thumbnail((176, 106))
            ctk_thumb = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(176, 106))
            
            def _update():
                if self.url_entry.get().strip():
                    self.current_thumbnail_img = ctk_thumb
                    self.thumb_label.configure(image=ctk_thumb, text="")
            self.after(0, _update)
        except Exception:
            pass

    # ----------------------------------------------------
    # MEDIA DOWNLOAD LOGIC & ANIMATIONS
    # ----------------------------------------------------

    def start_download_thread(self):
        """Initiate download in background thread with input validation and security checks."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Please enter or paste a valid social media video link!")
            return

        # Security check on URL
        is_safe_url, url_reason = SecurityValidator.is_safe_url(url)
        if not is_safe_url:
            messagebox.showerror("Security Warning", f"The entered link failed security verification:\n\n{url_reason}")
            return

        save_directory = self.path_entry.get().strip() or self.save_dir
        # Security check on directory
        is_safe_dir, safe_dir = SecurityValidator.is_safe_directory(save_directory)
        if not is_safe_dir:
            messagebox.showerror("Security Warning", f"The chosen save directory failed security verification:\n\n{safe_dir}")
            return

        quality = self.quality_var.get()

        self._is_downloading = True
        self.download_btn.configure(state="disabled", fg_color="#0369A1")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_status_lbl.configure(text="Status: Initializing turbo download...", text_color=("#0284C7", "#38BDF8"))
        self.footer_status.configure(text="Downloading media stream at high speed...")

        # Start download button pulse animation
        self._animate_download_button()

        thread = threading.Thread(
            target=self._run_download,
            args=(url, quality, safe_dir),
        )
        self.active_download_thread = thread
        thread.daemon = True
        thread.start()

    def _animate_download_button(self):
        """Looping pulse animation on download button while downloading."""
        if self._is_downloading:
            char = self._spinner_chars[self._spinner_index % len(self._spinner_chars)]
            self._spinner_index += 1
            btn_prefix = "Turbo Downloading Audio" if "Audio" in self.media_type_var.get() else "Turbo Downloading Video"
            self.download_btn.configure(text=f"{char} {btn_prefix}...")
            self.after(120, self._animate_download_button)

    def _run_download(self, url: str, quality: str, save_directory: str):
        """Background download worker."""
        def progress_cb(data):
            self.after(0, lambda: self._on_download_progress(data))

        def finished_cb(saved_file):
            self.after(0, lambda: self._on_download_finished(saved_file))

        def error_cb(err):
            self.after(0, lambda: self._on_download_error(err))

        self.engine.download_media(
            url=url,
            quality=quality,
            save_directory=save_directory,
            progress_callback=progress_cb,
            finished_callback=finished_cb,
            error_callback=error_cb,
        )

    def _on_download_progress(self, data: dict):
        """Update progress bar and stats dynamically."""
        self.progress_bar.set(data["progress"])
        self.progress_status_lbl.configure(
            text=f"Status: {data['status']} ({data['percent_str']})",
            text_color=("#0284C7", "#38BDF8"),
        )
        self.progress_stats_lbl.configure(
            text=f"Speed: {data['speed_str']}  |  Size: {data['size_str']}  |  ETA: {data['eta_str']}"
        )

    def _on_download_finished(self, saved_file: str):
        """Handle download completion with celebratory visual state."""
        self._is_downloading = False
        self.last_downloaded_path = saved_file
        
        # Celebration visual on download button
        self.download_btn.configure(
            state="normal",
            text="✓ Download Complete! 🎉",
            fg_color="#10B981",
            hover_color="#059669",
        )
        self.cancel_btn.configure(state="disabled")
        self.progress_bar.set(1.0)
        self.progress_status_lbl.configure(
            text="Status: Download Complete! 🎉",
            text_color=("#15803D", "#34D399"),
        )
        self.progress_stats_lbl.configure(text="Speed: Done  |  Size: Complete  |  ETA: 00:00")
        
        file_name = os.path.basename(saved_file)
        self.footer_status.configure(text=f"Saved: {file_name}")

        # Reset button text after 3 seconds
        def _restore_button():
            btn_text = "⬇️ Download Audio (High Quality)" if "Audio" in self.media_type_var.get() else "⬇️ Download Video (No Watermark)"
            self.download_btn.configure(text=btn_text, fg_color="#0284C7", hover_color="#0369A1")
        self.after(3000, _restore_button)

        messagebox.showinfo(
            "Download Complete!",
            f"Media successfully downloaded at turbo speed!\n\nSaved to:\n{saved_file}",
        )

    def _on_download_error(self, err_msg: str):
        """Handle download failure or cancellation."""
        self._is_downloading = False
        btn_text = "⬇️ Download Audio (High Quality)" if "Audio" in self.media_type_var.get() else "⬇️ Download Video (No Watermark)"
        self.download_btn.configure(state="normal", text=btn_text, fg_color="#0284C7", hover_color="#0369A1")
        self.cancel_btn.configure(state="disabled")
        self.progress_status_lbl.configure(
            text=f"Status: Error occurred",
            text_color="#EF4444",
        )
        self.footer_status.configure(text=err_msg[:80])
        
        if "cancelled" not in err_msg.lower():
            lower_err = err_msg.lower()
            if "youtube requires sign-in cookies" in lower_err or "bot" in lower_err or "login_required" in lower_err:
                resp = messagebox.askyesno(
                    "YouTube Bot Verification",
                    f"{err_msg}\n\nWould you like to open the YouTube Cookie Manager now to attach your cookies.txt?",
                )
                if resp:
                    self._open_cookie_modal()
            else:
                messagebox.showerror("Download Error", f"Could not complete download:\n\n{err_msg}")

    def cancel_download(self):
        """Cancel the ongoing download."""
        self.engine.cancel_download()
        self.cancel_btn.configure(state="disabled")
        self.progress_status_lbl.configure(text="Status: Cancelling download...", text_color="#F59E0B")


if __name__ == "__main__":
    app = SocialDartApp()
    app.mainloop()