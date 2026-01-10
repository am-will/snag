# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Snag is a screenshot-to-text CLI tool powered by vision AI (Google Gemini or OpenRouter). It captures a screen region, sends it to a vision model for analysis, and copies the markdown result to the clipboard.

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
snag --setup                                      # Configure API keys and defaults
snag --update                                     # Update to latest version
```

## Architecture

The codebase is in `snag/` with a simple pipeline:

```
main.py → capture.py → vision.py → clipboard.py
              ↓            ↓
         platform.py   config.py
```

- **main.py**: CLI entry point, setup wizard, orchestrates the capture→vision→clipboard flow
- **config.py**: Configuration management (TOML for settings, .env for API keys)
- **capture.py**: Platform-specific screenshot capture with region selection
  - Wayland: uses `slurp` + `grim` subprocess calls
  - macOS: uses native `screencapture -i -s`
  - X11/Windows: uses `mss` + tkinter overlay with `pynput` for keyboard events
- **vision.py**: Vision API integration (Google Gemini and OpenRouter) with retry logic
- **clipboard.py**: Thin wrapper around `pyperclip`
- **notify.py**: Desktop notifications (osascript on macOS, plyer elsewhere)
- **platform.py**: Platform/display server detection (X11, Wayland, macOS, Windows)

## Key Implementation Details

- Config stored at `~/.config/snag/` (works with keyboard shortcuts that lack shell env)
  - `.env` - API keys (GEMINI_API_KEY, OPENROUTER_API_KEY)
  - `config.toml` - Default provider and model settings
- Multi-monitor support via mss's `monitors[0]` which spans all displays
- Region selection uses absolute screen coordinates (important for multi-monitor with negative coords)
- Vision API has exponential backoff retry for rate limits and timeouts
- Supports two providers: `google` (direct Gemini API) and `openrouter` (OpenAI-compatible)
