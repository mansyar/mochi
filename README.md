# 🐱 Mochi — Desktop Cat Companion

A lightweight, cross-platform desktop pet that lives on your workspace. Mochi walks on application windows, climbs screen edges, falls with gravity, and requires occasional care — all without interrupting your workflow.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Qt](https://img.shields.io/badge/PySide6-Qt%206-41CD52?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20|%20macOS%20|%20Linux-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Window Platforming** — Mochi treats your open windows as physical surfaces, walking along title bars and falling when windows close
- **Physics Engine** — Gravity, terminal velocity, and collision detection against real window geometry
- **7-State FSM** — Idle, Walk, Fall, Climb, Wall Slide, Sleep, and Grabbed states with smooth transitions
- **Inventory Toolbox** (`Ctrl+Shift+P`) — Feed, entertain, and pet Mochi with deployable items
- **Tamagotchi Metrics** — Hunger, Boredom, and Affection persist across restarts with offline decay
- **Boss Key** (`Ctrl+Shift+H`) — Instantly hide everything for screen sharing or presentations
- **Click-Through Overlay** — Mochi never blocks your mouse or keyboard input
- **Alt+Click Drag** — Pick up and reposition Mochi anywhere on screen
- **Auto-Hide in Fullscreen** — Automatically hides during games, videos, and presentations
- **System Tray** — Convenient menu for show/hide, stats, and settings

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| UI Engine | PySide6-Essentials (Qt 6) |
| Window Polling | PyWinCtl + PyMonCtl |
| Global Hotkeys | Platform-native APIs via ctypes |
| Package Manager | uv |
| Linter/Formatter | Ruff |
| Type Checker | mypy |
| Testing | pytest + pytest-qt + pytest-cov |
| Packaging | PyInstaller (dev) / Nuitka (release) |

## 📋 Prerequisites

- **Python 3.11+**
- **uv** — [Install guide](https://docs.astral.sh/uv/getting-started/installation/)

### Install uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repo-url> && cd mochi

# Install all dependencies (creates .venv automatically)
uv sync --extra dev

# Run Mochi
uv run python -m mochi
```

## 🧑‍💻 Development

```bash
# Lint
uv run ruff check src/

# Format
uv run ruff format src/

# Type check
uv run mypy src/mochi/

# Run tests with coverage
uv run pytest

# Run tests in parallel
uv run pytest -n auto
```

## 🎮 Controls

| Action | Input |
|---|---|
| Open Toolbox | `Ctrl + Shift + P` |
| Boss Key (hide all) | `Ctrl + Shift + H` |
| Pick up Mochi | `Alt + Click` on the cat |
| Drop Mochi | Release mouse button |
| Tray menu | Right-click the system tray icon |

## 📁 Project Structure

```
mochi/
├── docs/
│   ├── PRD.md              # Product Requirements Document
│   ├── TDD.md              # Technical Design Document
│   └── ROADMAP.md          # Development Roadmap
├── src/
│   └── mochi/
│       ├── main.py          # Entry point
│       ├── config.py        # Tunable constants
│       ├── models/          # FSM, pet state
│       ├── core/            # Canvas, physics, environment, hotkeys
│       ├── ui/              # Toolbox, tray, onboarding, sprites
│       └── utils/           # Logger, platform shims
├── assets/
│   └── sprites/             # Sprite sheets
├── tests/                   # pytest test suite
└── pyproject.toml           # Project config (deps, ruff, mypy, pytest)
```

## 📖 Documentation

- [**PRD**](docs/PRD.md) — Product requirements, features, UX flows, and MVP definition
- [**TDD**](docs/TDD.md) — Architecture, data model, subsystem designs, and build configuration
- [**Roadmap**](docs/ROADMAP.md) — 6 phases, 20 testable tracks from scaffold to shipping

## 🏗️ Building

### Development Build (PyInstaller)

```bash
uv run pyinstaller --onefile --windowed \
  --add-data "assets/sprites:assets/sprites" \
  --exclude-module PySide6.QtWebEngine \
  --exclude-module PySide6.QtMultimedia \
  --name Mochi \
  src/mochi/main.py
```

### Release Build (Nuitka)

```bash
uv run python -m nuitka \
  --onefile \
  --windows-disable-console \
  --include-data-dir=assets/sprites=assets/sprites \
  --enable-plugin=pyside6 \
  --output-filename=Mochi \
  src/mochi/main.py
```

## 📄 License

MIT
