<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/9d2c88ab-b139-430b-9518-43203c265a3e" />

# Snag

> **Beta** - This tool is in active development. If you encounter any issues, please [report them](https://github.com/am-will/snag/issues).

Screenshot-to-text CLI tool powered by vision AI (Google Gemini, OpenRouter, or Z.AI).

Capture any region of your screen and instantly get a markdown description in your clipboard - ready to paste into an LLM, document, or anywhere else.

## Features

- **Region selection** - Click and drag to capture any part of your screen
- **Multi-monitor support** - Works across all your displays
- **Smart transcription** - Handles text, code, diagrams, charts, UI elements, and images
- **Instant clipboard** - Results copied automatically, ready to paste
- **Multiple providers** - Google Gemini, OpenRouter, or Z.AI (GLM-4.6V)
- **Cross-platform** - Linux (X11/Wayland), Windows, macOS

## Installation

```bash
# Install with uv (recommended)
uv tool install git+https://github.com/am-will/snag.git

# Update to latest version
snag --update
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

Run `snag --setup` to configure your API keys and defaults:

```
$ snag --setup

==================================================
  Current Settings
==================================================

  API Keys:
    Google Gemini:  not configured
    OpenRouter:     not configured
    Z.AI:           not configured

  Defaults:
    Provider: google
    Model:    gemini-2.5-flash

==================================================
  Setup Menu
==================================================

  1. Configure Google Gemini API key
  2. Configure OpenRouter API key
  3. Configure Z.AI API key
  4. Set default provider
  5. Set default model
  6. Exit setup
```

Get your API keys:
- **Google Gemini**: https://aistudio.google.com/apikey (free)
- **OpenRouter**: https://openrouter.ai/keys
- **Z.AI**: https://open.bigmodel.cn/ (requires GLM Coding Plan)

## Usage

```bash
# Capture a region (uses defaults from config)
snag

# Use Google Gemini directly
snag --provider google --model gemini-2.5-flash

# Use OpenRouter with any supported model
snag --provider openrouter --model google/gemini-2.5-flash-lite
snag --provider openrouter --model anthropic/claude-3.5-sonnet

# Use Z.AI (GLM-4.6V via MCP) - requires Node.js >= 22
snag --provider zai

# Configure API keys and defaults
snag --setup

# Update to latest version
snag --update
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

## Config Files

Configuration is stored in `~/.config/snag/`:

**API Keys** (`.env`):
```bash
GEMINI_API_KEY="your-gemini-key"
OPENROUTER_API_KEY="your-openrouter-key"
Z_AI_API_KEY="your-zai-key"
```

**Settings** (`config.toml`):
```toml
[defaults]
provider = "google"
model = "gemini-2.5-flash"
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
