"""Configuration management for Snag."""

import sys
from pathlib import Path
from typing import Any

# Use tomllib (3.11+) or tomli for TOML reading
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

CONFIG_DIR = Path.home() / ".config" / "snag"
CONFIG_FILE = CONFIG_DIR / "config.toml"
ENV_FILE = CONFIG_DIR / ".env"

# Defaults
DEFAULT_PROVIDER = "google"
DEFAULT_MODEL = "gemini-2.5-flash"
ZAI_DEFAULT_MODEL = "glm-4.6v"  # Z.AI uses fixed model via MCP

# Google Gemini model configurations (for validation when using google provider)
GOOGLE_MODELS = {
    "gemini-2.5-flash": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        "version": "2.5",
    },
    "gemini-3-flash-preview": {
        "endpoint": "https://generativelanguage.googleapis.com/v1alpha/models/gemini-3-flash-preview:generateContent",
        "version": "3.x",
    },
}


def get_config() -> dict[str, Any]:
    """Load config from TOML file, returning defaults if not found."""
    if not CONFIG_FILE.exists():
        return {"defaults": {"provider": DEFAULT_PROVIDER, "model": DEFAULT_MODEL}}

    try:
        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)
        # Ensure defaults section exists
        if "defaults" not in config:
            config["defaults"] = {}
        # Fill in missing defaults
        config["defaults"].setdefault("provider", DEFAULT_PROVIDER)
        config["defaults"].setdefault("model", DEFAULT_MODEL)
        return config
    except Exception:
        return {"defaults": {"provider": DEFAULT_PROVIDER, "model": DEFAULT_MODEL}}


def save_config(config: dict[str, Any]) -> None:
    """Save config to TOML file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Simple TOML writing (avoiding extra dependency for simple config)
    lines = ["[defaults]"]
    defaults = config.get("defaults", {})
    if "provider" in defaults:
        lines.append(f'provider = "{defaults["provider"]}"')
    if "model" in defaults:
        lines.append(f'model = "{defaults["model"]}"')

    CONFIG_FILE.write_text("\n".join(lines) + "\n")


def get_default_provider() -> str:
    """Get the default provider from config."""
    config = get_config()
    return config.get("defaults", {}).get("provider", DEFAULT_PROVIDER)


def get_default_model() -> str:
    """Get the default model from config."""
    config = get_config()
    return config.get("defaults", {}).get("model", DEFAULT_MODEL)


def set_default_provider(provider: str) -> None:
    """Set the default provider in config."""
    config = get_config()
    config["defaults"]["provider"] = provider
    save_config(config)


def set_default_model(model: str) -> None:
    """Set the default model in config."""
    config = get_config()
    config["defaults"]["model"] = model
    save_config(config)
