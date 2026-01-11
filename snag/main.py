"""CLI entry point for Snag."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .config import (
    CONFIG_DIR,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    ENV_FILE,
    GOOGLE_MODELS,
    get_config,
    get_default_model,
    get_default_provider,
    save_config,
    set_default_model,
    set_default_provider,
)

# Git repository for updates
GIT_REPO = "git+https://github.com/am-will/snag.git"

# Standard config locations for .env file
ENV_LOCATIONS = [
    CONFIG_DIR / ".env",
    Path.home() / ".snag.env",
    Path.cwd() / ".env",
]


def has_api_key(provider: str = "google") -> bool:
    """Check if API key for provider is available (env or .env)."""
    key_map = {
        "google": "GEMINI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "zai": "Z_AI_API_KEY",
    }
    key_name = key_map.get(provider, f"{provider.upper()}_API_KEY")

    # Check env var first
    if os.environ.get(key_name):
        return True
    # Check .env files in standard locations
    for env_file in ENV_LOCATIONS:
        if env_file.exists():
            content = env_file.read_text()
            for line in content.splitlines():
                if line.strip().startswith(f"{key_name}="):
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if value:
                        return True
    return False


def run_update() -> int:
    """Update snag to the latest version using uv."""
    print("Updating snag...")
    try:
        result = subprocess.run(
            ["uv", "tool", "install", "--force", GIT_REPO],
            check=False,
        )
        if result.returncode == 0:
            print("\nSnag updated successfully!")
        else:
            print("\nUpdate failed. Make sure 'uv' is installed.", file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: 'uv' not found. Install it from https://docs.astral.sh/uv/", file=sys.stderr)
        return 1


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
        env_file.write_text(
            '# API Keys for Snag\n'
            '# Google Gemini: https://aistudio.google.com/apikey\n'
            'GEMINI_API_KEY=""\n'
            '# OpenRouter: https://openrouter.ai/keys\n'
            'OPENROUTER_API_KEY=""\n'
            '# Z.AI (GLM-4.6V): https://open.bigmodel.cn/\n'
            'Z_AI_API_KEY=""\n'
        )
    return env_file


def _get_env_content() -> dict[str, str]:
    """Read current .env file content as dict."""
    env_file = CONFIG_DIR / ".env"
    content = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                content[key.strip()] = value.strip().strip('"').strip("'")
    return content


def _save_env_content(content: dict[str, str]) -> None:
    """Save dict to .env file."""
    env_file = CONFIG_DIR / ".env"
    lines = [
        "# API Keys for Snag",
        "# Google Gemini: https://aistudio.google.com/apikey",
        f'GEMINI_API_KEY="{content.get("GEMINI_API_KEY", "")}"',
        "# OpenRouter: https://openrouter.ai/keys",
        f'OPENROUTER_API_KEY="{content.get("OPENROUTER_API_KEY", "")}"',
        "# Z.AI (GLM-4.6V): https://open.bigmodel.cn/",
        f'Z_AI_API_KEY="{content.get("Z_AI_API_KEY", "")}"',
    ]
    env_file.write_text("\n".join(lines) + "\n")


def _configure_api_key(provider: str) -> bool:
    """Configure API key for a provider. Returns True if successful."""
    import getpass

    env_content = _get_env_content()
    key_map = {
        "google": ("GEMINI_API_KEY", "https://aistudio.google.com/apikey"),
        "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/keys"),
        "zai": ("Z_AI_API_KEY", "https://open.bigmodel.cn/"),
    }
    key_name, url = key_map.get(provider, (f"{provider.upper()}_API_KEY", ""))

    print(f"\nGet your API key at: {url}\n")

    try:
        api_key = getpass.getpass(f"Enter your {provider.upper()} API key: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return False

    if not api_key:
        print("Error: API key cannot be empty.")
        return False

    env_content[key_name] = api_key
    _save_env_content(env_content)
    print(f"\n{provider.capitalize()} API key saved!")
    return True


def _show_current_settings() -> None:
    """Display current configuration."""
    config = get_config()
    defaults = config.get("defaults", {})

    print("\n" + "=" * 50)
    print("  Current Settings")
    print("=" * 50)

    # API Keys status
    gemini_ok = has_api_key("google")
    openrouter_ok = has_api_key("openrouter")
    zai_ok = has_api_key("zai")
    print(f"\n  API Keys:")
    print(f"    Google Gemini:  {'configured' if gemini_ok else 'not configured'}")
    print(f"    OpenRouter:     {'configured' if openrouter_ok else 'not configured'}")
    print(f"    Z.AI:           {'configured' if zai_ok else 'not configured'}")

    # Defaults
    print(f"\n  Defaults:")
    print(f"    Provider: {defaults.get('provider', DEFAULT_PROVIDER)}")
    print(f"    Model:    {defaults.get('model', DEFAULT_MODEL)}")

    print(f"\n  Config files:")
    print(f"    {CONFIG_DIR / '.env'}")
    print(f"    {CONFIG_DIR / 'config.toml'}")
    print()


def run_setup() -> int:
    """Run interactive setup for configuration."""
    ensure_config_exists()

    print(get_logo())

    while True:
        _show_current_settings()

        print("=" * 50)
        print("  Setup Menu")
        print("=" * 50)
        print("\n  1. Configure Google Gemini API key")
        print("  2. Configure OpenRouter API key")
        print("  3. Configure Z.AI API key")
        print("  4. Set default provider")
        print("  5. Set default model")
        print("  6. Exit setup")
        print()

        try:
            choice = input("Select option [1-6]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSetup cancelled.")
            return 0

        if choice == "1":
            _configure_api_key("google")

        elif choice == "2":
            _configure_api_key("openrouter")

        elif choice == "3":
            _configure_api_key("zai")

        elif choice == "4":
            print("\n  Available providers:")
            print("    1. google (Google Gemini)")
            print("    2. openrouter (OpenRouter)")
            print("    3. zai (Z.AI GLM-4.6V)")
            try:
                p_choice = input("\n  Select provider [1-3]: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled.")
                continue

            if p_choice == "1":
                set_default_provider("google")
                print("\n  Default provider set to: google")
            elif p_choice == "2":
                set_default_provider("openrouter")
                print("\n  Default provider set to: openrouter")
            elif p_choice == "3":
                set_default_provider("zai")
                print("\n  Default provider set to: zai")
            else:
                print("\n  Invalid option.")

        elif choice == "5":
            current_provider = get_default_provider()
            print(f"\n  Current provider: {current_provider}")

            if current_provider == "google":
                print("  Available Google models:")
                for i, model in enumerate(GOOGLE_MODELS.keys(), 1):
                    print(f"    {i}. {model}")
                print(f"    {len(GOOGLE_MODELS) + 1}. Enter custom model name")
            elif current_provider == "zai":
                print("  Z.AI uses GLM-4.6V via MCP. Model is fixed.")
                print("  Press Enter to continue...")
                try:
                    input()
                except (KeyboardInterrupt, EOFError):
                    pass
                continue
            else:
                print("  OpenRouter supports many models. Enter the full model name.")
                print("  Examples: google/gemini-2.5-flash-lite, anthropic/claude-3.5-sonnet")

            try:
                if current_provider == "google":
                    m_choice = input("\n  Select model or enter number: ").strip()
                    model_list = list(GOOGLE_MODELS.keys())
                    try:
                        idx = int(m_choice) - 1
                        if 0 <= idx < len(model_list):
                            model = model_list[idx]
                        elif idx == len(model_list):
                            model = input("  Enter custom model name: ").strip()
                        else:
                            print("\n  Invalid option.")
                            continue
                    except ValueError:
                        model = m_choice  # Treat as custom model name
                else:
                    model = input("\n  Enter model name: ").strip()

                if model:
                    set_default_model(model)
                    print(f"\n  Default model set to: {model}")
                else:
                    print("\n  Model name cannot be empty.")
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled.")
                continue

        elif choice == "6":
            print("\nSetup complete! Run 'snag' to capture a screenshot.")
            return 0

        else:
            print("\nInvalid option. Please enter 1-6.")


def main() -> int:
    """Main entry point for the Snag CLI."""
    from .capture import CaptureError, SelectionCancelled, capture_region
    from .clipboard import copy_to_clipboard
    from .notify import notify_error, notify_processing, notify_success
    from .vision import VisionError, describe_image

    # Get defaults from config
    config_provider = get_default_provider()
    config_model = get_default_model()

    parser = argparse.ArgumentParser(
        description="Screenshot to text using vision AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  snag                                          # Use defaults from config
  snag --provider google --model gemini-2.5-flash
  snag --provider openrouter --model google/gemini-2.5-flash-lite
  snag --provider zai                           # Z.AI GLM-4.6V via MCP
  snag --setup                                  # Configure API keys and defaults

Current defaults (from config):
  Provider: {config_provider}
  Model:    {config_model}

Environment:
  GEMINI_API_KEY       Google Gemini API key (https://aistudio.google.com/apikey)
  OPENROUTER_API_KEY   OpenRouter API key (https://openrouter.ai/keys)
  Z_AI_API_KEY         Z.AI API key (https://open.bigmodel.cn/)
""",
    )

    parser.add_argument(
        "--provider",
        choices=["google", "openrouter", "zai"],
        default=None,
        help=f"Vision provider to use (default: {config_provider})",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=f"Model to use (default: {config_model})",
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run interactive setup to configure API keys and defaults",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="snag 0.1.0",
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help="Update snag to the latest version",
    )

    args = parser.parse_args()

    # Run update if requested (do this first, before config)
    if args.update:
        return run_update()

    # Ensure config file exists (creates placeholder on first run)
    ensure_config_exists()

    # Run setup if requested
    if args.setup:
        return run_setup()

    # Determine provider and model to use
    provider = args.provider or config_provider
    model = args.model or config_model

    # Check if API key is configured for the chosen provider
    if not has_api_key(provider):
        key_map = {
            "google": "GEMINI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "zai": "Z_AI_API_KEY",
        }
        key_name = key_map.get(provider, f"{provider.upper()}_API_KEY")
        print(f"Error: {key_name} not found for provider '{provider}'.", file=sys.stderr)
        print(f"Run 'snag --setup' to configure your API key.", file=sys.stderr)
        return 1

    try:
        # 1. Capture screenshot region
        image = capture_region()

        # 2. Send to vision API for description (notify while waiting)
        notify_processing()
        result = describe_image(image, model=model, provider=provider)

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
