"""Desktop notifications for Snag."""

import warnings

from plyer import notification


def notify(title: str, message: str, timeout: int = 5) -> None:
    """Show a desktop notification.

    Args:
        title: Notification title
        message: Notification body text
        timeout: How long to show (seconds)
    """
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*dbus.*")
            notification.notify(
                title=title,
                message=message[:256],  # Truncate long messages
                app_name="Snag",
                timeout=timeout,
            )
    except Exception:
        # Silently fail if notifications aren't available
        pass


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
