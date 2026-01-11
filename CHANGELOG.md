# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2025-01-06

### Added
- **Z.AI provider** - GLM-4.6V integration via Model Context Protocol (MCP)
- `--changelog` flag to view release notes
- `--changelog-full` flag to view full changelog history

## [1.1.0] - 2025-01-04

### Added
- **OpenRouter provider** - Access to multiple vision models via OpenAI-compatible API
- Self-update feature (`snag --update`) via uv tool installer

## [1.0.1] - 2025-01-03

### Fixed
- macOS: Use native `screencapture` instead of tkinter for better compatibility
- macOS: Use native `osascript` for reliable notifications
- Escape key handling with pynput global keyboard listener
- Selection box visibility improvements

### Security
- API keys hidden during input using `getpass`
- API keys masked in setup confirmation display

## [1.0.0] - 2025-01-01

### Added
- Initial release of Snag screenshot-to-text CLI tool
- **Google Gemini provider** - Direct API integration with Gemini 2.5/3.x models
- Cross-platform screen region capture:
  - Wayland: `slurp` + `grim`
  - macOS: Native `screencapture -i -s`
  - X11/Windows: `mss` + tkinter overlay with `pynput` keyboard events
- Interactive setup wizard (`snag --setup`) for API key configuration
- Multi-monitor support with absolute screen coordinates
- Desktop notifications for processing status and results
- Automatic clipboard copy of extracted text
- Configuration stored in `~/.config/snag/` for keyboard shortcut compatibility

[Unreleased]: https://github.com/am-will/snag/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/am-will/snag/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/am-will/snag/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/am-will/snag/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/am-will/snag/releases/tag/v1.0.0
