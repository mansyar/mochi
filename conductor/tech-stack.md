# Technology Stack

## Overview
Mochi is a cross-platform Python desktop application built for minimal resource consumption and broad OS compatibility (Windows 10+, macOS 12+, Linux X11).

## Core Technologies

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Language** | Python | >= 3.11 | Primary development language |
| **UI Engine** | PySide6-Essentials (Qt 6) | >= 6.7, < 7.0 | Frameless transparent overlay window, sprite rendering, animation timer, system tray. Essentials variant excludes WebEngine/Multimedia to reduce binary size |
| **Window Polling** | PyWinCtl | >= 0.4, < 1.0 | Cross-platform OS window position/size/state queries |
| **Monitor Geometry** | PyMonCtl | >= 0.4, < 1.0 | Monitor geometry queries for fullscreen detection |
| **Global Input** | Platform-native APIs (ctypes) | — | OS-native hotkey registration: Win32 `RegisterHotKey`, macOS `RegisterEventHotKey`, X11 `XGrabKey`. Zero external dependencies |
| **Config/State** | JSON (stdlib) | — | Lightweight persistence with no external dependencies |

## Development Tooling

| Tool | Role | Replaces |
|---|---|---|
| **uv** | Package manager, virtualenv, Python version management | pip + venv + pyenv + pip-tools |
| **Ruff** | Linter + formatter + import sorter (Rust-based) | flake8 + black + isort |
| **mypy** | Static type checker (strict mode) | — |
| **pytest** | Test runner with Qt and coverage plugins | unittest |

## Dev Dependencies
- pytest >= 8.0
- pytest-qt >= 4.4
- pytest-cov >= 6.0
- pytest-xdist >= 3.5
- mypy >= 1.13
- ruff >= 0.9.0
- PyInstaller >= 6.0

## Release Dependencies
- Nuitka >= 2.0 (compiles Python to C for smaller binaries)

## Key Design Decisions

### Why no pynput?
pynput installs a global keyboard hook intercepting ALL keystrokes — unnecessary when only 2 hotkeys are needed. Platform-native APIs avoid antivirus false positives on Windows, reduce macOS permission requirements, and eliminate thread-safety hazards.

### Why PySide6-Essentials?
The Essentials variant excludes Qt WebEngine, Multimedia, and Network modules, reducing binary size by ~100 MB while retaining all needed functionality (widgets, core, GUI).

### Why uv?
A single Rust binary replacing pip, venv, pyenv, and pip-tools. Resolves dependencies 10-100x faster with deterministic lockfile.

### Packaging Strategy
- **Dev builds:** PyInstaller for fast iteration
- **Release builds:** Nuitka for smaller binaries (30-50% smaller), faster startup, and 10-30% better runtime performance

## Platform Support

| Platform | Minimum Version | Architecture |
|---|---|---|
| Windows | 10 21H2+ / 11 | x64 |
| macOS | 12 Monterey+ | ARM64 and x64 |
| Linux | Ubuntu 22.04+, Fedora 38+ | X11 only (Wayland: post-MVP) |
| Display | Single monitor (MVP) | Multi-monitor: post-MVP |

## Target Binary Sizes

| Platform | Nuitka | PyInstaller |
|---|---|---|
| Windows x64 | < 25 MB | < 45 MB |
| macOS ARM64 | < 30 MB | < 50 MB |
| Linux x64 | < 25 MB | < 45 MB |
