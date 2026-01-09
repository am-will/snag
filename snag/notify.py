"""Desktop notifications for Snag."""

import subprocess
import sys
import warnings


def _notify_macos(title: str, message: str) -> bool:
    """Show notification on macOS using osascript."""
    try:
        # Escape quotes for AppleScript
        title = title.replace('"', '\\"')
        message = message.replace('"', '\\"')
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
        )
        return True
    except Exception:
        return False


def _notify_plyer(title: str, message: str, timeout: int) -> bool:
    """Show notification using plyer (Linux/Windows)."""
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*dbus.*")
            from plyer import notification
            notification.notify(
                title=title,
                message=message[:256],
                app_name="Snag",
                timeout=timeout,
            )
        return True
    except Exception:
        return False


def notify(title: str, message: str, timeout: int = 5) -> None:
    """Show a desktop notification.

    Args:
        title: Notification title
        message: Notification body text
        timeout: How long to show (seconds)
    """
    if sys.platform == "darwin":
        _notify_macos(title, message)
    else:
        _notify_plyer(title, message, timeout)


def notify_processing() -> None:
    """Show a processing notification."""
    notify("Snag", "Processing screenshot...")


def notify_success(preview: str) -> None:
    """Show a success notification with text preview."""
    # Show first 100 chars as preview
    if len(preview) > 100:
        preview = preview[:100] + "..."
    notify("Snag", f"Copied to clipboard:\n{preview}")


def notify_error(error: str) -> None:
    """Show an error notification."""
    notify("Snag - Error", error, timeout=10)
