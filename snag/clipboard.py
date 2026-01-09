"""Clipboard operations for Click."""

import pyperclip


def copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard.

    On Linux X11, requires xclip or xsel.
    On Linux Wayland, requires wl-clipboard.
    """
    pyperclip.copy(text)


def get_clipboard() -> str:
    """Get current clipboard contents."""
    return pyperclip.paste()
