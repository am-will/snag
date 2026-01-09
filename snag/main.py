"""CLI entry point for Snag."""

import argparse
import os
import sys
from pathlib import Path


# Standard config locations for .env file
CONFIG_DIR = Path.home() / ".config" / "snag"
ENV_LOCATIONS = [
    CONFIG_DIR / ".env",
    Path.home() / ".snag.env",
    Path.cwd() / ".env",
]


def has_api_key() -> bool:
    """Check if GEMINI_API_KEY is available (env or .env)."""
    # Check env var first
    if os.environ.get("GEMINI_API_KEY"):
        return True
    # Check .env files in standard locations
    for env_file in ENV_LOCATIONS:
        if env_file.exists():
            content = env_file.read_text()
            for line in content.splitlines():
                if line.strip().startswith("GEMINI_API_KEY="):
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if value:
                        return True
    return False


def get_logo() -> str:
    """Generate colored ASCII art logo."""
    # ANSI color codes for gradient effect (blue -> cyan -> green)
    c1 = "\033[38;5;33m"   # Blue
    c2 = "\033[38;5;39m"   # Light blue
    c3 = "\033[38;5;44m"   # Cyan
    c4 = "\033[38;5;49m"   # Cyan-green
    c5 = "\033[38;5;83m"   # Green
    r = "\033[0m"          # Reset

    return f"""
{c1}  ███████╗{c2}███╗   ██╗{c3} █████╗ {c4} ██████╗ {r}
{c1}  ██╔════╝{c2}████╗  ██║{c3}██╔══██╗{c4}██╔════╝ {r}
{c1}  ███████╗{c2}██╔██╗ ██║{c3}███████║{c4}██║  ███╗{r}
{c1}  ╚════██║{c2}██║╚██╗██║{c3}██╔══██║{c4}██║   ██║{r}
{c1}  ███████║{c2}██║ ╚████║{c3}██║  ██║{c4}╚██████╔╝{r}
{c1}  ╚══════╝{c2}╚═╝  ╚═══╝{c3}╚═╝  ╚═╝{c4} ╚═════╝ {r}

{c3}  Screenshot → Text → Clipboard{r}
"""


def ensure_config_exists() -> Path:
    """Ensure config directory and .env file exist with placeholder."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    env_file = CONFIG_DIR / ".env"
    if not env_file.exists():
        env_file.write_text('# Get your API key at: https://aistudio.google.com/apikey\nGEMINI_API_KEY=""\n')
    return env_file


def run_setup() -> int:
    """Run interactive setup for API key configuration."""
    env_file = ensure_config_exists()

    print(get_logo())
    print("=" * 50)
    print("  Configure your Gemini API Key")
    print("=" * 50)
    print("\nGet your API key at: https://aistudio.google.com/apikey\n")
    print("How would you like to configure your API key?\n")
    print("  1. Enter API key now")
    print(f"  2. Manually edit config file")
    print(f"\nConfig location: {env_file}")
    print()

    while True:
        try:
            choice = input("Select option [1-2]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSetup cancelled.")
            return 1

        if choice == "1":
            print()
            try:
                api_key = input("Enter your GEMINI API key: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\nSetup cancelled.")
                return 1

            if not api_key:
                print("Error: API key cannot be empty.")
                continue

            # Save to config file
            env_file.write_text(f'# Get your API key at: https://aistudio.google.com/apikey\nGEMINI_API_KEY="{api_key}"\n')

            print(f"\nAPI key saved to: {env_file}")
            print("\nSetup complete! Run 'snag' to capture a screenshot.")
            return 0

        elif choice == "2":
            print("\n" + "-" * 50)
            print(f"Edit this file and add your API key:\n")
            print(f"  {env_file}")
            print("\nReplace the empty quotes with your key:")
            print('  GEMINI_API_KEY="your-key-here"')
            print("-" * 50)
            print("\nRun 'snag' after adding your key.")
            return 0

        else:
            print("Invalid option. Please enter 1 or 2.")


def main() -> int:
    """Main entry point for the Snag CLI."""
    from .capture import CaptureError, SelectionCancelled, capture_region
    from .clipboard import copy_to_clipboard
    from .notify import notify_error, notify_processing, notify_success
    from .vision import DEFAULT_MODEL, MODELS, VisionError, describe_image

    parser = argparse.ArgumentParser(
        description="Screenshot to text using Gemini vision",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  snag                              # Use default model (gemini-2.5-flash)
  snag --model gemini-3-flash-preview   # Use Gemini 3 Flash
  snag --setup                      # Configure API key

Environment:
  GEMINI_API_KEY    Your Gemini API key (required)
                    Get one at: https://aistudio.google.com/apikey
""",
    )

    parser.add_argument(
        "--model",
        choices=list(MODELS.keys()),
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})",
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run interactive setup to configure API key",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="snag 0.1.0",
    )

    args = parser.parse_args()

    # Ensure config file exists (creates placeholder on first run)
    ensure_config_exists()

    # Run setup if requested
    if args.setup:
        return run_setup()

    # Auto-trigger setup if no API key configured
    if not has_api_key():
        print("No GEMINI_API_KEY found. Running setup...\n")
        return run_setup()

    try:
        # 1. Capture screenshot region
        image = capture_region()

        # 2. Send to Gemini for description (notify while waiting)
        notify_processing()
        result = describe_image(image, model=args.model)

        # 3. Copy to clipboard
        copy_to_clipboard(result)

        # 4. Show success notification
        notify_success(result)

        return 0

    except SelectionCancelled:
        # User cancelled - exit silently
        return 0

    except CaptureError as e:
        notify_error(str(e))
        print(f"Capture error: {e}", file=sys.stderr)
        return 1

    except VisionError as e:
        notify_error(str(e))
        print(f"Vision error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        notify_error(f"Unexpected error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
