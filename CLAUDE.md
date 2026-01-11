# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Snag is a screenshot-to-text CLI tool powered by vision AI (Google Gemini, OpenRouter, or Z.AI). It captures a screen region, sends it to a vision model for analysis, and copies the markdown result to the clipboard.

## Installation

```bash
# Install as a uv tool (recommended)
uv tool install git+https://github.com/am-will/snag.git

# Update to latest version
snag --update
```

## Development Commands

```bash
# Install in development mode
uv pip install -e .

# Run the tool
snag                                              # Use defaults from config
snag --provider google --model gemini-2.5-flash   # Google Gemini
snag --provider openrouter --model google/gemini-2.5-flash-lite  # OpenRouter
snag --provider zai                               # Z.AI GLM-4.6V via MCP
snag --setup                                      # Configure API keys and defaults
snag --update                                     # Update to latest version

# Test module imports
python -c "from snag.main import main; print('OK')"

# Test API without screen capture
python -c "
from PIL import Image
from snag.vision import describe_image
img = Image.new('RGB', (100, 100), color='red')
result = describe_image(img, provider='google', model='gemini-2.5-flash')
print(result)
"
```

## Architecture

The codebase is in `snag/` with a simple pipeline:

```
main.py → capture.py → vision.py → clipboard.py
              ↓            ↓
         platform.py   config.py
                           ↓
                      mcp_client.py (for Z.AI)
```

- **main.py**: CLI entry point, setup wizard, orchestrates the capture→vision→clipboard flow
- **config.py**: Configuration management (TOML for settings, .env for API keys)
- **capture.py**: Platform-specific screenshot capture with region selection
  - Wayland: uses `slurp` + `grim` subprocess calls
  - macOS: uses native `screencapture -i -s`
  - X11/Windows: uses `mss` + tkinter overlay with `pynput` for keyboard events
- **vision.py**: Vision API integration (Google Gemini, OpenRouter, Z.AI) with retry logic
- **mcp_client.py**: MCP (Model Context Protocol) client for Z.AI integration
- **clipboard.py**: Thin wrapper around `pyperclip`
- **notify.py**: Desktop notifications (osascript on macOS, plyer elsewhere)
- **platform.py**: Platform/display server detection (X11, Wayland, macOS, Windows)

## Key Implementation Details

- Config stored at `~/.config/snag/` (works with keyboard shortcuts that lack shell env)
  - `.env` - API keys (GEMINI_API_KEY, OPENROUTER_API_KEY, Z_AI_API_KEY)
  - `config.toml` - Default provider and model settings
- Multi-monitor support via mss's `monitors[0]` which spans all displays
- Region selection uses absolute screen coordinates (important for multi-monitor with negative coords)
- Vision API has exponential backoff retry for rate limits and timeouts
- Supports three providers: `google` (direct Gemini API), `openrouter` (OpenAI-compatible), and `zai` (MCP-based)

## Provider Details

### Google Gemini (provider: "google")
- Direct REST API calls to `generativelanguage.googleapis.com`
- Models defined in `config.py` `GOOGLE_MODELS` dict with endpoint and version
- Gemini 2.5 uses `inline_data` format, Gemini 3.x uses `inlineData` (camelCase)
- API key passed as query param: `?key=API_KEY`

### OpenRouter (provider: "openrouter")
- OpenAI-compatible API at `https://openrouter.ai/api/v1/chat/completions`
- Accepts any model string (e.g., `google/gemini-2.5-flash-lite`, `anthropic/claude-3.5-sonnet`)
- Images sent as base64 data URLs in content array
- API key in Authorization header: `Bearer API_KEY`

### Z.AI (provider: "zai")
- Uses Model Context Protocol (MCP) via `@z_ai/mcp-server` npm package
- Requires Node.js >= v22.0.0
- Communicates via JSON-RPC over stdio (subprocess)
- Model: GLM-4.6V (fixed, not configurable)
- Tool used: `analyze_image` for general-purpose image understanding
- API key env var: `Z_AI_API_KEY`
- MCP server launched via: `npx -y @z_ai/mcp-server`

## Adding New Google Models

Edit `GOOGLE_MODELS` in `snag/config.py`:

```python
GOOGLE_MODELS = {
    "gemini-2.5-flash": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        "version": "2.5",
    },
    # Add new model here:
    "gemini-new-model": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-new-model:generateContent",
        "version": "2.5",  # or "3.x" for different payload format
    },
}
```

## Dependencies

Key dependencies (see `pyproject.toml`):
- `mss` - Cross-platform screen capture
- `Pillow` - Image processing
- `pynput` - Keyboard/mouse events (X11/Windows)
- `pyperclip` - Clipboard access
- `requests` - HTTP client for API calls
- `python-dotenv` - .env file loading
- `plyer` - Cross-platform notifications
- `tomli` - TOML parsing (Python < 3.11 only)

## Git Repository

- Remote: `git+https://github.com/am-will/snag.git`
- Used by `snag --update` for self-updating via `uv tool install --force`
