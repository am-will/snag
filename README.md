<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/9d2c88ab-b139-430b-9518-43203c265a3e" />

# Snag

> **Beta** - This tool is in active development. If you encounter any issues, please [report them](https://github.com/am-will/snag/issues).

Screenshot-to-text CLI tool powered by Google Gemini vision.

Capture any region of your screen and instantly get a markdown description in your clipboard - ready to paste into an LLM, document, or anywhere else.

## Features

- **Region selection** - Click and drag to capture any part of your screen
- **Multi-monitor support** - Works across all your displays
- **Smart transcription** - Handles text, code, diagrams, charts, UI elements, and images
- **Instant clipboard** - Results copied automatically, ready to paste
- **Multiple models** - Choose between Gemini 2.5 Flash (default) or Gemini 3 Flash Preview
- **Cross-platform** - Linux (X11/Wayland), Windows, macOS

## Installation

```bash
# Install with pip
pip install git+https://github.com/am-will/snag.git

# Or with uv (recommended)
uv pip install git+https://github.com/am-will/snag.git
```

### Linux Dependencies

**X11:**
```bash
# For clipboard support
sudo apt install xclip  # or xsel
```

**Wayland:**
```bash
sudo apt install slurp grim wl-clipboard
```

### macOS Permissions

On first run, macOS will prompt for Screen Recording permissions:

1. Grant permission when prompted
2. **Restart the app** (required for permissions to take effect)
3. On second run, grant "bypass screen capture restrictions" if prompted

You can manage these in: System Settings → Privacy & Security → Screen Recording

## Setup

Run `snag` for the first time to configure your API key:

```
$ snag

  ███████╗███╗   ██╗ █████╗  ██████╗
  ██╔════╝████╗  ██║██╔══██╗██╔════╝
  ███████╗██╔██╗ ██║███████║██║  ███╗
  ╚════██║██║╚██╗██║██╔══██║██║   ██║
  ███████║██║ ╚████║██║  ██║╚██████╔╝
  ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝

  Screenshot → Text → Clipboard

==================================================
  Configure your Gemini API Key
==================================================

Get your API key at: https://aistudio.google.com/apikey

How would you like to configure your API key?

  1. Enter API key now
  2. Manually edit config file

Config location: ~/.config/snag/.env
```

Get your free API key at: https://aistudio.google.com/apikey

## Usage

```bash
# Capture a region (default model: gemini-2.5-flash)
snag

# Use Gemini 3 Flash Preview
snag --model gemini-3-flash-preview

# Re-run setup
snag --setup
```

### Controls

| Action | Result |
|--------|--------|
| **Left-click + drag** | Select region |
| **Release mouse** | Capture and process |
| **Right-click** | Cancel |
| **Escape** or **q** | Cancel |

### Keyboard Shortcut (Recommended)

Set up a global keyboard shortcut in your desktop environment to run `snag`:

**GNOME:**
Settings → Keyboard → Custom Shortcuts → Add:
- Name: `Snag`
- Command: `/path/to/snag` (or just `snag` if in PATH)
- Shortcut: Your choice (e.g., `Super+Shift+S`)

**KDE:**
System Settings → Shortcuts → Custom Shortcuts → Add

## Config File

Your API key is stored in `~/.config/snag/.env`:

```bash
GEMINI_API_KEY="your-key-here"
```

This location works with keyboard shortcuts (which don't have access to shell environment variables).

## Example Output

Capture a code snippet:
```markdown
**Python Code:**
def hello_world():
    print("Hello, World!")
```

Capture a diagram:
```markdown
**Flowchart showing:**
- Start → Process A → Decision
- If yes → Process B → End
- If no → Process C → End
```

## License

MIT
