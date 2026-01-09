"""Screenshot capture with region selection for Snag."""

import subprocess
import sys
from io import BytesIO
from typing import Optional

import mss
from PIL import Image

from .platform import Platform, detect_platform


class CaptureError(Exception):
    """Error during screenshot capture."""

    pass


class SelectionCancelled(Exception):
    """User cancelled the region selection."""

    pass


def capture_region() -> Image.Image:
    """Capture a region of the screen selected by the user.

    Returns:
        PIL Image of the selected region

    Raises:
        CaptureError: If capture fails
        SelectionCancelled: If user cancels selection
    """
    platform = detect_platform()

    if platform == Platform.LINUX_WAYLAND:
        return _capture_wayland()
    elif platform in (Platform.LINUX_X11, Platform.WINDOWS, Platform.MACOS):
        return _capture_with_overlay()
    else:
        raise CaptureError(f"Unsupported platform: {platform}")


def _capture_wayland() -> Image.Image:
    """Capture region on Wayland using slurp + grim."""
    # Check for required tools
    try:
        subprocess.run(["which", "slurp"], check=True, capture_output=True)
        subprocess.run(["which", "grim"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        raise CaptureError(
            "Wayland capture requires 'slurp' and 'grim'.\n"
            "Install with: sudo apt install slurp grim  # Debian/Ubuntu\n"
            "             sudo dnf install slurp grim   # Fedora"
        )

    # Get region selection with slurp
    try:
        result = subprocess.run(
            ["slurp"], capture_output=True, text=True, check=True
        )
        region = result.stdout.strip()
    except subprocess.CalledProcessError:
        raise SelectionCancelled()

    if not region:
        raise SelectionCancelled()

    # Capture region with grim
    try:
        result = subprocess.run(
            ["grim", "-g", region, "-"],
            capture_output=True,
            check=True,
        )
        return Image.open(BytesIO(result.stdout))
    except subprocess.CalledProcessError as e:
        raise CaptureError(f"grim capture failed: {e}")


def _capture_with_overlay() -> Image.Image:
    """Capture region using mss + tkinter overlay for X11/Windows/macOS."""
    import tkinter as tk

    from PIL import ImageEnhance, ImageTk
    from pynput import keyboard

    # First, take a full screenshot of ALL monitors
    with mss.mss() as sct:
        # monitors[0] is the full virtual screen spanning all monitors
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)
        full_image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    # Get the virtual screen bounds (may have negative coordinates for left monitors)
    screen_x = monitor["left"]
    screen_y = monitor["top"]
    screen_width = monitor["width"]
    screen_height = monitor["height"]

    # Create darkened version for display (reduce brightness to ~40%)
    darkened = ImageEnhance.Brightness(full_image).enhance(0.4)

    # Create selection overlay
    selection = {"start": None, "end": None, "cancelled": True}

    root = tk.Tk()
    root.overrideredirect(True)  # Remove window decorations
    root.attributes("-topmost", True)
    root.configure(cursor="cross")

    # Position window to cover ALL monitors (including negative coordinates)
    root.geometry(f"{screen_width}x{screen_height}+{screen_x}+{screen_y}")

    # Convert darkened screenshot to PhotoImage
    photo = ImageTk.PhotoImage(darkened)

    canvas = tk.Canvas(
        root,
        width=screen_width,
        height=screen_height,
        highlightthickness=0,
    )
    canvas.pack()

    # Display darkened screenshot as background
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)

    rect_id = None

    def cancel():
        selection["cancelled"] = True
        root.quit()

    # For selection rectangle - use two rectangles for better visibility
    rect_border = None
    rect_inner = None

    def on_mouse_press(event):
        nonlocal rect_border, rect_inner
        # Store absolute screen coordinates
        selection["start"] = (event.x_root, event.y_root)
        selection["cancelled"] = False
        if rect_border:
            canvas.delete(rect_border)
            canvas.delete(rect_inner)
        # Black outer border for contrast
        rect_border = canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="black", width=3
        )
        # White inner border
        rect_inner = canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="white", width=1
        )

    def on_mouse_drag(event):
        nonlocal rect_border, rect_inner
        if selection["start"] and rect_border:
            # Convert start position to canvas coordinates
            x1 = selection["start"][0] - screen_x
            y1 = selection["start"][1] - screen_y
            canvas.coords(rect_border, x1, y1, event.x, event.y)
            canvas.coords(rect_inner, x1, y1, event.x, event.y)

    def on_mouse_release(event):
        selection["end"] = (event.x_root, event.y_root)
        root.quit()

    def on_right_click(event):
        cancel()

    # Global keyboard listener using pynput (captures keys regardless of focus)
    def on_key_press(key):
        if key == keyboard.Key.esc:
            # Schedule cancel on main thread
            root.after(0, cancel)
            return False  # Stop listener
        # Also check for 'q' key
        try:
            if key.char == 'q':
                root.after(0, cancel)
                return False
        except AttributeError:
            pass
        return True

    # Start keyboard listener in background thread
    kb_listener = keyboard.Listener(on_press=on_key_press)
    kb_listener.start()

    # Bind mouse events to canvas
    canvas.bind("<ButtonPress-1>", on_mouse_press)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_release)
    canvas.bind("<ButtonPress-3>", on_right_click)  # Right-click to cancel

    root.mainloop()

    # Cleanup
    kb_listener.stop()
    root.destroy()

    if selection["cancelled"] or not selection["start"] or not selection["end"]:
        raise SelectionCancelled()

    # Calculate region in absolute screen coordinates
    x1 = min(selection["start"][0], selection["end"][0])
    y1 = min(selection["start"][1], selection["end"][1])
    x2 = max(selection["start"][0], selection["end"][0])
    y2 = max(selection["start"][1], selection["end"][1])

    # Ensure we have a valid region
    if x2 - x1 < 5 or y2 - y1 < 5:
        raise SelectionCancelled()

    # Convert to image coordinates (relative to screenshot origin)
    img_x1 = x1 - screen_x
    img_y1 = y1 - screen_y
    img_x2 = x2 - screen_x
    img_y2 = y2 - screen_y

    # Crop the ORIGINAL (non-darkened) screenshot
    return full_image.crop((img_x1, img_y1, img_x2, img_y2))
