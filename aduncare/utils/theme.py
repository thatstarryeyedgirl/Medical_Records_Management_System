"""
Central theme module for AdunCare.

Holds the brand color palette and a cross-platform Poppins font loader.
Import COLOR_* constants for styling and use get_font(...) instead of
calling ctk.CTkFont(...) directly, so every window stays visually consistent
and automatically benefits from Poppins when it's available on the host
machine, falling back gracefully when it isn't.
"""

import os
import sys
import shutil
import customtkinter as ctk

# --------------------------------------------------------------------------
# Brand colors
# --------------------------------------------------------------------------
COLOR_PRIMARY_DARK = "#3A5A78"      # Headings, buttons, primary text accents
COLOR_BACKGROUND_LIGHT = "#88C9F9"  # Outer window / app background
COLOR_PANEL_LIGHT = "#D9F1FC"       # Card panels, input field backgrounds
COLOR_GOLD_ACCENT = "#D4AF37"       # Confirmation screen success heading

# Kept as named constants (not part of the 3-color brand palette, but used
# consistently across the app for feedback states)
COLOR_ERROR = "red"
COLOR_SUCCESS = "green"
COLOR_INPUT_BORDER_DEFAULT = ["#979DA2", "#565B5E"]

# --------------------------------------------------------------------------
# Font handling
# --------------------------------------------------------------------------
_FONT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts"
)

_FONT_FILES = [
    "Poppins-Regular.ttf",
    "Poppins-Medium.ttf",
    "Poppins-SemiBold.ttf",
    "Poppins-Bold.ttf",
    "Poppins-Italic.ttf",
]

_FALLBACK_FAMILY = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"

_poppins_ready = False  # cached result so we only attempt registration once


def _register_windows_font(font_path: str) -> bool:
    """Registers a font for the current process on Windows using the real
    Win32 GDI API. Does not require admin rights or a permanent install."""
    try:
        import ctypes
        FR_PRIVATE = 0x10
        added = ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
        return added > 0
    except Exception:
        return False


def _register_macos_font(font_path: str) -> bool:
    """Copies the font into the user's Fonts folder so macOS's font
    system picks it up. Requires no elevated permissions."""
    try:
        target_dir = os.path.expanduser("~/Library/Fonts")
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, os.path.basename(font_path))
        if not os.path.exists(target_path):
            shutil.copy(font_path, target_path)
        return True
    except Exception:
        return False


def _register_linux_font(font_path: str) -> bool:
    """Copies the font into the user's local fontconfig directory and
    refreshes the font cache using the standard fc-cache tool."""
    try:
        target_dir = os.path.expanduser("~/.local/share/fonts")
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, os.path.basename(font_path))
        if not os.path.exists(target_path):
            shutil.copy(font_path, target_path)
            os.system(f'fc-cache -f "{target_dir}" > /dev/null 2>&1')
        return True
    except Exception:
        return False


def ensure_poppins_loaded() -> bool:
    """
    Attempts to register the bundled Poppins font files for the current
    process/user so 'Poppins' becomes usable as a font family name.

    Must be called AFTER a Tk/CTk root window has been created (font
    registration and lookup requires an active Tk interpreter), and should
    be called once, near the start of the app (e.g. in MainWindow.__init__
    before _build_ui() runs).

    Safe to call multiple times - the result is cached after the first run.
    Returns True if Poppins is confirmed available afterwards, False if the
    app should rely on the fallback family instead.
    """
    global _poppins_ready
    if _poppins_ready:
        return _is_poppins_available()

    any_missing = False
    for fname in _FONT_FILES:
        fpath = os.path.join(_FONT_DIR, fname)
        if not os.path.exists(fpath):
            any_missing = True
            continue

        if sys.platform.startswith("win"):
            _register_windows_font(fpath)
        elif sys.platform == "darwin":
            _register_macos_font(fpath)
        else:
            _register_linux_font(fpath)

    if any_missing:
        print(
            "Warning: one or more bundled Poppins font files are missing "
            f"from {_FONT_DIR}. Falling back to {_FALLBACK_FAMILY} where "
            "Poppins isn't already installed on the system."
        )

    _poppins_ready = True
    return _is_poppins_available()


def _is_poppins_available() -> bool:
    """Checks the live Tk font database for 'Poppins'. Requires a Tk root
    to already exist, which is guaranteed once ensure_poppins_loaded() has
    been called from inside a CTk window's __init__."""
    try:
        import tkinter.font as tkfont
        return "Poppins" in tkfont.families()
    except Exception:
        return False


def font_family() -> str:
    """Returns 'Poppins' if it was successfully registered/found, otherwise
    a safe platform-appropriate fallback."""
    return "Poppins" if _is_poppins_available() else _FALLBACK_FAMILY


def get_font(size: int = 14, weight: str = "normal", slant: str = "roman") -> ctk.CTkFont:
    """
    Convenience wrapper around ctk.CTkFont that always applies the resolved
    brand font family. Use this everywhere in place of ctk.CTkFont(...).

    weight: "normal" or "bold" (matches CTkFont's accepted values)
    slant: "roman" or "italic"
    """
    kwargs = {"family": font_family(), "size": size, "weight": weight}
    if slant == "italic":
        kwargs["slant"] = "italic"
    return ctk.CTkFont(**kwargs)
