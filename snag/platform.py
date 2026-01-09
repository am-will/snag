"""Platform detection for Click."""

import os
import sys
from enum import Enum


class Platform(Enum):
    """Supported platforms."""

    LINUX_X11 = "linux_x11"
    LINUX_WAYLAND = "linux_wayland"
    WINDOWS = "windows"
    MACOS = "macos"
    UNKNOWN = "unknown"


def detect_platform() -> Platform:
    """Detect the current platform and display server."""
    if sys.platform == "win32":
        return Platform.WINDOWS
    elif sys.platform == "darwin":
        return Platform.MACOS
    elif sys.platform.startswith("linux"):
        # Check for Wayland first
        if os.environ.get("WAYLAND_DISPLAY"):
            return Platform.LINUX_WAYLAND
        elif os.environ.get("XDG_SESSION_TYPE") == "wayland":
            return Platform.LINUX_WAYLAND
        elif os.environ.get("DISPLAY"):
            return Platform.LINUX_X11
        elif os.environ.get("XDG_SESSION_TYPE") == "x11":
            return Platform.LINUX_X11
        # Default to X11 if we can't determine
        return Platform.LINUX_X11
    return Platform.UNKNOWN


def is_wayland() -> bool:
    """Check if running on Wayland."""
    return detect_platform() == Platform.LINUX_WAYLAND


def is_x11() -> bool:
    """Check if running on X11."""
    return detect_platform() == Platform.LINUX_X11
