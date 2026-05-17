# Initial Concept

**Mochi** — An ultra-lightweight, cross-platform desktop companion cat pet that lives natively on the user's workspace. Operating under a controlled-chaos behavior model, the pet provides a sense of digital life by dynamically interacting with open application windows and screen boundaries without interrupting the user's actual productivity or workflow. The cat treats the user's desktop environment as a physical playground — walking on window title bars, climbing screen edges, falling when platforms disappear, and sleeping when bored.

---

# Product Guide

## Product Vision
Build a charming, non-intrusive digital pet that lives on the user's desktop, bringing warmth and personality to the workspace without compromising productivity. Mochi should feel like a real, autonomous creature exploring the digital environment — not a distracting game.

## Target Users
| Persona | Description |
|---|---|
| **Developer / Power User** | Spends 8+ hours at a desktop with multiple windows. Wants ambient entertainment and a sense of digital life without productivity loss |
| **Casual Desktop User** | Enjoys virtual pets and desktop customization. Values low-friction setup and minimal configuration |

## Key Features (MVP)

### Feline State Machine (FSM)
Mochi transitions smoothly between 7 behavior states based on environmental context and internal metrics:
1. **Idle (Loaf)** — Sits with subtle breathing/tail-flick micro-animation
2. **Walk** — Moves horizontally along window top edges or screen bottom
3. **Fall** — Descends with gravity acceleration until landing on a surface
4. **Climb** — Scales vertical surfaces (screen edges, window sides)
5. **Wall Slide** — Slowly slides down vertical surfaces
6. **Sleep** — Curls up with slow breathing animation (lowest CPU mode)
7. **Grabbed** — User picks up and drags the cat (Alt+Click)

### Environmental Awareness
- Walks on top edges of visible application windows
- Climbs screen bezels and window side borders
- Falls with realistic gravity when support surfaces disappear
- Automatically hides during fullscreen applications (games, videos, presentations)

### User Interaction
- **Hotkey Toolbox** (`Ctrl+Shift+P`): Floating menu with Food Dish, Yarn Ball, Pet/Stroke, and Cardboard Box items
- **Boss Key** (`Ctrl+Shift+H`): Instant hide with zero visual trace — perfect for professional contexts
- **Drag Interaction** (Alt+Click): Pick up and reposition the cat anywhere on screen
- **System Tray Icon**: Persistent control surface with Show/Hide, Stats, About, and Quit

### Tamagotchi Lifecycle
- Three metrics: Hunger, Boredom, Affection (0–100 range)
- Real-time decay while running and offline decay across sessions
- Metrics directly affect cat behavior (speed, sleepiness, affection responses)
- Persistence via local JSON storage with corruption recovery

## User Experience Flow
1. **First Launch:** Transparent overlay appears, cat spawns on screen bottom, onboarding tooltip shows hotkey bindings for 8 seconds, tray icon appears
2. **Passive Engagement:** Cat autonomously explores the desktop — walking on windows, climbing edges, sleeping when bored
3. **Active Intervention:** User opens toolbox, deploys items, interacts with the cat
4. **Emergency Hide:** Boss Key instantly hides all traces; second press restores everything

## Non-Functional Requirements
| Metric | Target |
|---|---|
| Idle CPU | < 1% single core |
| Active CPU (walking/climbing) | < 3% single core |
| RAM | < 80 MB resident set |
| Startup to visible | < 2 seconds |
| GPU | Software rendering only — no GPU acceleration required |

## Constraints
- Single monitor only (MVP), multi-monitor deferred
- No Wayland support (MVP) — Linux X11 only
- No admin/root privileges required
- No network access — fully offline, no telemetry
- No global keyboard hook — platform-native hotkey registration only
- Sprite sheet is pre-authored (no runtime generation)
