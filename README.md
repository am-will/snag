# Snag

<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/9d2c88ab-b139-430b-9518-43203c265a3e" />

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

  1. Use exported shell API key (export GEMINI_API_KEY="YOUR-API-KEY")
  2. Enter GEMINI API key now (saves to .env file)
  3. Manually create .env file later (See README)
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

## API Key Priority

If both are set, `.env` file takes priority over shell environment:

1. `.env` file in current directory (highest priority)
2. Exported `GEMINI_API_KEY` environment variable

This lets you use a specific key for snag without affecting other tools.

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
