# Click: Screenshot-to-Text CLI Tool

## Overview
A cross-platform CLI tool that captures a screen region, uses Google Gemini Flash to **describe and transcribe any visual content** (text, diagrams, charts, UI, images, etc.), and copies the result to clipboard as markdown.

**Usage**: `click [--model MODEL]` - user configures keyboard shortcut in their desktop environment.

**Model selection**:
- `--model gemini-2.5-flash` (default) - fast, cheap
- `--model gemini-3-flash-preview` - newer, potentially better quality

## Architecture

```
click/
├── pyproject.toml           # Project config, dependencies
├── click/
│   ├── __init__.py
│   ├── main.py              # CLI entry point (argparse)
│   ├── capture.py           # Screenshot + region selection
│   ├── vision.py            # Gemini API - describe visual content
│   ├── clipboard.py         # Clipboard operations
│   ├── notify.py            # Desktop notifications
│   └── platform.py          # Platform detection (X11/Wayland/Win/Mac)
```

## Implementation Steps

### Step 1: Project Setup
Create `pyproject.toml` with dependencies:
- `mss` - cross-platform screenshots
- `Pillow` - image handling
- `pyperclip` - clipboard access
- `requests` - HTTP requests to Gemini API
- `plyer` - desktop notifications

### Step 2: Platform Detection (`platform.py`)
Detect runtime environment:
- `linux_x11` - X11 display server
- `linux_wayland` - Wayland (needs grim/slurp)
- `windows` / `macos`

### Step 3: Screenshot Capture (`capture.py`)
**X11/Windows/macOS:**
- Use `mss` library for screenshot
- Create fullscreen transparent tkinter overlay
- User clicks and drags to select region
- Capture selected region

**Wayland:**
- Shell out to `slurp` for region selection
- Shell out to `grim -g <region>` for capture
- Return PIL Image

### Step 4: Vision/Description (`vision.py`)
- Read API key from `GEMINI_API_KEY` env var
- Use direct REST API calls (no SDK needed) with `requests` library
- **Model-specific endpoints**:
  - `gemini-2.5-flash`: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
  - `gemini-3-flash-preview`: `https://generativelanguage.googleapis.com/v1alpha/models/gemini-3-flash-preview:generateContent`
- **Payload differences**:
  - 2.5: `inline_data` with `mime_type` and `data`
  - 3.x: `inlineData` with `mimeType`, `data`, and `mediaResolution`
- Send image (base64) with prompt that instructs Gemini to describe/transcribe content
- Output as clean markdown suitable for pasting into an LLM

### Step 5: Clipboard (`clipboard.py`)
- Use `pyperclip.copy()` to set clipboard
- Linux X11 requires `xclip` or `xsel`
- Linux Wayland requires `wl-clipboard`

### Step 6: Notifications (`notify.py`)
- Use `plyer.notification` for cross-platform notifications
- Show "Processing..." on capture
- Show success with text preview, or error message

### Step 7: CLI Entry Point (`main.py`)
```python
def main():
    # 1. Detect platform
    # 2. Capture region screenshot
    # 3. Send to Gemini to describe/transcribe content
    # 4. Copy result to clipboard
    # 5. Show notification
```

## Dependencies

**Python packages:**
```
mss>=9.0.0
Pillow>=10.0.0
pyperclip>=1.9.0
requests>=2.31.0
plyer>=2.1.0
```

**System dependencies by platform:**
| Platform | Required packages |
|----------|------------------|
| Linux X11 | `xclip` or `xsel` |
| Linux Wayland | `wl-clipboard`, `grim`, `slurp` |
| Windows | None |
| macOS | None |

## User Setup

1. Install: `pip install -e .` (or `uv pip install -e .`)
2. Set API key: `export GEMINI_API_KEY="your-key"`
3. Configure keyboard shortcut in DE settings to run `click`

**Example GNOME setup:**
Settings → Keyboard → Custom Shortcuts → Add:
- Name: "Screenshot to Text"
- Command: `/path/to/click`
- Shortcut: Ctrl+Shift+S

## Error Handling

- Missing API key → clear error message with setup instructions
- Region selection cancelled → exit silently
- API failure → retry with exponential backoff (3 attempts)
- Clipboard failure → show notification with error
- Missing system deps (grim/slurp/xclip) → helpful error message

## Files to Create

1. `pyproject.toml`
2. `click/__init__.py`
3. `click/main.py`
4. `click/platform.py`
5. `click/capture.py`
6. `click/vision.py`
7. `click/clipboard.py`
8. `click/notify.py`
