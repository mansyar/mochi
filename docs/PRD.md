# Product Requirements Document (PRD)

## Desktop Cat Pet — "Mochi"

**Version:** 1.0
**Last Updated:** 2026-05-17
**Status:** Phase 2, Track 2.1 Complete — Active Development

> **Project Status:** Phase 0 (Project Foundation) is complete. **Tracks 1.1, 1.2, and 1.3** are complete — the transparent overlay renders the cat sprite with a looping idle breathing animation (8 frames at 250ms intervals, auto-centered frames). The cat autonomously walks left and right along the screen bottom using an FSM-driven Idle→Walk→EdgePause cycle, reversing direction at screen edges with a brief pause. The walk animation uses direction-aware sprite flipping via `QPainter.scale(-1, 1)` and an adaptive tick rate (100ms during Walk, 250ms during Idle). The green test rectangle has been removed.
>
> **Track 2.1 (Window Polling & Surface Detection)** is complete — a background `EnvironmentPoller` thread queries `pywinctl.getAllWindows()` every 300ms, filters out minimized/empty-title/Mochi windows, builds a `list[Surface]` (window tops, window sides, screen edges), and emits a `platforms_updated` signal to the main thread via Qt's cross-thread signal-slot mechanism. Canvas stores the surface list and logs update counts. Error handling gracefully degrades on permission errors. **153 tests passing with 91% coverage, zero lint/type errors.** The cat does NOT yet walk on window surfaces — ground snapping is deferred to Track 2.2. See `ROADMAP.md` for the full development plan.

---

## 1. Objective & Purpose

Build an ultra-lightweight, cross-platform desktop companion ("Mochi") that lives natively on the user's workspace. Operating under a controlled-chaos behavior model, the pet provides a sense of digital life by dynamically interacting with open application windows and screen boundaries without interrupting the user's actual productivity or workflow.

The cat treats the user's desktop environment as a physical playground — walking on window title bars, climbing screen edges, falling when platforms disappear, and sleeping when bored.

---

## 2. Target Users

| Persona | Description |
|---|---|
| **Developer / Power User** | Spends 8+ hours at a desktop, multiple windows open, wants ambient entertainment without productivity loss |
| **Casual Desktop User** | Enjoys virtual pets and desktop customization, values low-friction setup |

---

## 3. Platform & Environment Requirements

| Requirement | Specification |
|---|---|
| **Windows** | Windows 10 21H2+ / Windows 11 (x64) |
| **macOS** | macOS 12 Monterey+ (ARM64 and x64) |
| **Linux** | X11-based desktops (Ubuntu 22.04+, Fedora 38+). Wayland deferred to post-MVP |
| **Python** | 3.11+ |
| **Display** | Single monitor (MVP). Multi-monitor deferred to post-MVP |
| **Permissions** | macOS: Accessibility permission required for window polling. Global hotkeys use native OS APIs with minimal permission scope |

---

## 4. Scope of Features

### 4.1 Core MVP Features

#### 4.1.1 Feline State Machine (FSM)

The pet transitions smoothly between 7 foundational behavior states based on environmental context, internal metric thresholds, and randomized timers:

| State | Description | Animation |
|---|---|---|
| **Idle (Loaf)** | Cat sits in loaf position with subtle breathing/tail-flick micro-animation | Loaf sprite + breathing cycle |
| **Walk** | Cat moves horizontally along a surface (window top edge, screen bottom) | Walk cycle (left/right variants) |
| **Fall** | Cat descends with gravity acceleration until intercepting a surface | Fall sprite with limbs spread |
| **Climb** | Cat scales a vertical surface (screen edge or window side border) upward | Climb cycle sprite |
| **Wall Slide** | Cat slowly slides down a vertical surface with claws extended | Slide sprite |
| **Sleep** | Cat curls up and sleeps with a breathing animation. Non-disruptive idle loop | Sleep sprite + zzz particle |
| **Grabbed** | Cat is picked up by the user (drag interaction). Limbs dangle | Grabbed/dangling sprite |

**State Transition Rules:**

| From | To | Trigger |
|---|---|---|
| Idle | Walk | Random timer: 2–5 seconds |
| Idle | Sleep | Boredom < 30 OR random timer: 15–30 seconds of continuous idle |
| Walk | Idle | Random timer: 3–8 seconds |
| Walk | Fall | Supporting surface lost (window moved/closed/minimized) |
| Walk | Climb | Leading edge reaches a vertical surface (screen bezel or window side) |
| Fall | Idle | Ground found (window top edge or screen bottom boundary) |
| Fall | Climb | Lateral edge contact during descent |
| Climb | Walk | Reached top edge of climbed surface |
| Climb | Wall Slide | Random timer: 1–3 seconds OR climb duration exceeds 10–15 seconds |
| Climb | Fall | Supporting window closed/moved during climb |
| Wall Slide | Fall | Reached bottom of surface OR supporting window closed |
| Wall Slide | Climb | Random timer: 0.5–2 seconds |
| Sleep | Idle | User interaction (feed/pet) OR sleep timer: 8–15 seconds |
| Any | Grabbed | User Alt+clicks and drags the cat |
| Grabbed | Fall | User releases the cat (drops from cursor position) |

> **Note:** All timer ranges are tunable configuration constants, not hardcoded values.

#### 4.1.2 Window & Screen Edge Interaction

- **Grounded Platforming:** The cat treats the top borders of all active, visible, non-minimized application windows as physical walking platforms.
- **Border Climbing:** Upon colliding with the left/right screen bezels or the vertical sides of an application window, the cat transitions into a vertical climbing state to scale the surface.
- **Surface Loss Handling:** If a window currently supporting the cat is moved, closed, minimized, or resized such that the cat no longer has footing, the cat immediately transitions to the Fall state.
- **Landing Priority:** When falling, the cat lands on the first solid surface it intersects — in order: another window's top edge, then the screen bottom boundary (above the OS taskbar).

#### 4.1.3 Physics Model

- **Gravity:** The cat accelerates downward at a configurable rate (`GRAVITY = 980 px/s²`) during the Fall state.
- **Terminal Velocity:** Capped at `TERMINAL_VELOCITY = 600 px/s` to prevent teleportation on large displays.
- **Walk Speed:** `WALK_SPEED = 60 px/s` (horizontal).
- **Climb Speed:** `CLIMB_SPEED = 40 px/s` (vertical).
- **Wall Slide Speed:** `WALL_SLIDE_SPEED = 20 px/s` (vertical, downward).

> All values in `px/s` are logical pixels. On HiDPI displays, the engine uses logical coordinates.

#### 4.1.4 Hotkey-Activated Inventory Toolbox

A global keyboard shortcut instantly summons a floating, context-aware toolbox menu at the user's current mouse cursor position.

| Property | Specification |
|---|---|
| **Default Hotkey** | `Ctrl + Shift + P` |
| **Hotkey Remapping** | Configurable via system tray settings (post-MVP: config file) |
| **Appearance** | Small floating panel (max 200×150px), semi-transparent, rounded corners |
| **Dismiss** | Click outside the panel, press Escape, or press the hotkey again |
| **Click-Through** | Opening the toolbox temporarily disables click-through on the overlay. Dismissing the toolbox re-enables it. The dismiss-click is intentionally consumed (not forwarded to underlying windows) |

**Inventory Items (MVP):**

| Item | Icon | Mechanical Effect | Cooldown |
|---|---|---|---|
| **Food Dish** | 🍖 | Sets Hunger to 100. Cat walks to dish and plays eating animation (3s) | 30 seconds |
| **Yarn Ball** | 🧶 | Sets Boredom to 100. Cat bats at yarn with paw animation (5s) | 20 seconds |
| **Pet / Stroke** | 🐾 | Increases Affection by +25 (capped at 100). Cat purrs and leans into hand | 10 seconds |
| **Cardboard Box** | 📦 | Places a box item on screen. Cat prioritizes walking into the box, locking into a non-disruptive idle loop. Removes box after 30s or on user dismiss | 60 seconds |

#### 4.1.5 Tamagotchi Attribute Persistence

The cat maintains three virtual pet metrics that persist across application restarts via local JSON storage.

| Metric | Range | Decay Rate | Recovery Method |
|---|---|---|---|
| **Hunger** | 0–100 (100 = full) | −8 per real-world hour | Food Dish item |
| **Boredom** | 0–100 (100 = entertained) | −6 per real-world hour | Yarn Ball item |
| **Affection** | 0–100 (100 = loved) | −4 per real-world hour | Pet/Stroke item, drag interaction (+5) |

**Offline Decay:** On application startup, the engine calculates elapsed real-world time since last exit and applies accumulated decay. Metrics floor at 0. Offline decay is capped at a maximum of **48 hours** — after that, the cat is considered to have fended for itself. This prevents punishing users who don't launch the app for extended periods.

**Metric Effects on Behavior:**

| Condition | Behavioral Change |
|---|---|
| Hunger < 20 | Walk speed reduced by 50%. Cat occasionally pauses and meows (visual indicator) |
| Boredom < 30 | Cat prioritizes Sleep state. Reduced walk/climb duration |
| Affection < 20 | Cat avoids cursor position (walks away when cursor approaches) |
| All metrics > 70 | Cat has a small chance (5%) of triggering a brief "happy zoomie" sprint |

#### 4.1.6 The Boss Key (Emergency Hide)

An immediate hotkey that forces the application to become completely invisible for screen sharing or professional contexts.

| Property | Specification |
|---|---|
| **Default Hotkey** | `Ctrl + Shift + H` (H for Hide). Note: `Ctrl+Shift+Esc` is reserved by Windows Task Manager and cannot be registered |
| **Alternative Trigger** | Double-click the system tray icon |
| **Behavior** | Hides the overlay window AND the system tray icon. No visible trace remains |
| **Restore** | Press the Boss Key hotkey again to restore. The cat reappears at its last position |
| **State Preservation** | FSM state and position are frozen on hide, resumed on restore |

#### 4.1.7 System Tray Icon

A persistent system tray icon provides a discoverable control surface for users who don't memorize hotkeys.

| Menu Item | Action |
|---|---|
| **Show / Hide Mochi** | Toggle cat visibility (same as Boss Key) |
| **Open Toolbox** | Opens the inventory toolbox at cursor position |
| **Stats** | Shows current Hunger / Boredom / Affection values in a tooltip or submenu |
| **About** | App version and credits |
| **Quit** | Saves state and exits cleanly |

#### 4.1.8 First-Run Onboarding

On the very first launch (no `pet_state.json` exists), a small translucent tooltip appears **above** the cat (with a small arrow pointing down) for 8 seconds. The tooltip's bottom edge must be at least 60px above the screen bottom to clear any taskbar.

```
🐱 Meet Mochi!
Ctrl+Shift+P → Open Toolbox
Ctrl+Shift+H → Boss Key (hide everything)
Alt+Click → Pick up Mochi
```

The tooltip fades out automatically and never appears again.

#### 4.1.10 Single-Instance Enforcement

Only one instance of Mochi may run at a time. If the user launches the application while a hidden (Boss Key) instance is already running:

- The second instance detects the existing process via a named mutex (Windows) or Unix domain socket (macOS/Linux).
- The second instance sends a "show" signal to the existing instance, which restores visibility.
- The second instance then exits immediately.

This prevents hotkey registration conflicts, state file corruption, and user confusion when the tray icon is hidden.

#### 4.1.9 Auto-Hide in Fullscreen Applications

When a fullscreen application is detected (game, video player, presentation, video call), the cat automatically hides with no user intervention. The cat reappears when the user returns to a windowed desktop.

- Detection method: Poll for fullscreen windows via PyWinCtl at the same interval as the window geometry poll.
- The Boss Key override takes precedence — if the user manually hid the cat, auto-show does not restore it.

### 4.2 Post-MVP Roadmap (Priority Order)

| Priority | Feature | Description |
|---|---|---|
| P1 | **Multi-Monitor Support** | Expand the coordinate grid across all active displays. Cat can walk between monitors via screen edges |
| P2 | **Configurable Hotkeys** | Allow users to remap all hotkeys via a settings panel |
| P3 | **Multiple Cat Skins** | Color variants and alternate sprite sheets selectable from tray menu |
| P4 | **Desktop Zoomies** | High-chaos subroutine: unpredictable screen-wide sprinting triggered randomly when all metrics > 80 |
| P5 | **Text-Cursor Swatting** | Cat detects active text cursor blinking and swats at it with paw animation |
| P6 | **Sound Effects** | Optional purring, meowing, and ambient sounds. Default OFF. Toggle in tray menu |
| P7 | **Seasonal Behaviors** | Holiday-themed idle animations (Santa hat in December, pumpkin in October, etc.) |

---

## 5. User Experience (UX) Flow

### 5.1 First Launch
1. User runs the application executable (or `python -m mochi`).
2. The transparent overlay canvas initializes fullscreen.
3. The cat spawns sitting on the OS taskbar (screen bottom).
4. The onboarding tooltip appears for 8 seconds showing hotkey bindings.
5. The system tray icon appears in the notification area.

### 5.2 Subsequent Launches
1. Application loads `pet_state.json`, calculates offline metric decay.
2. Cat spawns at its **last saved position**. If that surface no longer exists (window closed), the cat spawns in Fall state from that position and lands on the nearest surface below.
3. No onboarding tooltip.

### 5.3 Passive Engagement
1. The user works normally. The cat independently explores the screen.
2. The cat walks along window top edges, climbs screen bezels, and occasionally sleeps.
3. If the user moves or closes a window the cat is standing on, the cat falls to the next surface.

### 5.4 Active Intervention (Toolbox)
1. User presses `Ctrl + Shift + P`.
2. Click-through is temporarily disabled on the overlay.
3. The toolbox appears at cursor position with inventory items.
4. User clicks an item (e.g., Food Dish).
5. The item appears on the cat's **current surface**, at the nearest X position to the cursor. If the cat is falling, the item is placed on the screen bottom.
6. The cat's FSM enters a **best-effort approach** mode: it walks toward the item's X coordinate on its current surface. If the cat falls off an edge during approach, it may land on the item's surface (or closer to it). If the cat hasn't reached the item within 15 seconds, the approach is cancelled and the cat resumes normal FSM behavior. The metric is updated when the cat reaches the item.
7. The toolbox dismisses and click-through is re-enabled.

### 5.5 Drag Interaction
1. User holds `Alt` and clicks on the cat sprite.
2. Click-through mode is disabled; the cat enters the Grabbed state.
3. The cat follows the cursor with a dangling limbs animation.
4. On mouse release, the cat enters Fall state from the release position.
5. Affection increases by +5.

### 5.6 Containment (Cardboard Box)
1. User deploys a Cardboard Box from the toolbox.
2. A box sprite appears on the nearest surface.
3. The cat's FSM prioritizes walking into the box.
4. Once inside, the cat enters a non-disruptive idle loop (eyes peeking from box).
5. The box auto-removes after 60 seconds, or the user can dismiss it via the toolbox.

### 5.7 Emergency Hide (Boss Key)
1. User presses `Ctrl + Shift + H` (or double-clicks tray icon).
2. The cat, any deployed items, and the tray icon instantly disappear.
3. No visual artifacts remain on screen.
4. Pressing the hotkey again restores everything to its prior state.

---

## 6. Non-Functional Requirements

### 6.1 Performance Budget

| Metric | Target |
|---|---|
| **Idle CPU** | < 1% single core |
| **Active CPU** (walking/climbing) | < 3% single core |
| **RAM** | < 80 MB resident set |
| **Startup to visible** | < 2 seconds |
| **GPU** | No GPU acceleration required. Software rendering only |

### 6.2 Reliability

- The application must not crash if PyWinCtl returns invalid window data.
- The application must gracefully handle permission denial on macOS (show a one-time dialog with a button to open System Settings > Privacy > Accessibility).
- If a global hotkey fails to register (already claimed by another app), the application must log a warning and show a tray notification — not crash.
- `pet_state.json` corruption must not prevent startup — fall back to default values.

### 6.3 Security & Privacy

- No network access. The application is fully offline.
- No telemetry, analytics, or crash reporting.
- All data is stored locally in the application directory.
- **No global keyboard hook.** Hotkeys use platform-native registration APIs (`RegisterHotKey`, `RegisterEventHotKey`, `XGrabKey`) that intercept only the specific hotkey combinations — not all keystrokes. This avoids antivirus false positives on Windows and reduces macOS permission requirements.

---

## 7. Constraints & Assumptions

| Constraint | Detail |
|---|---|
| Single monitor only (MVP) | Multi-monitor is deferred |
| No Wayland support (MVP) | Linux support is X11 only |
| No admin/root privileges required | The app runs in user-space |
| Sprite sheet is pre-authored | No runtime sprite generation |
| Desktop must have visible windows | The cat falls to the screen bottom if no windows are open |
| Fullscreen-exclusive apps are not platforms | The cat hides, not walks on them |

---

## 8. MVP Definition of Done

- [ ] Cat walks on top edges of visible application windows
- [ ] Cat falls with gravity acceleration when supporting window is moved/closed/minimized
- [ ] Cat climbs screen edges and window side borders
- [ ] Cat transitions between all 7 FSM states without visual glitches or stuck states
- [ ] Idle state has subtle breathing/tail micro-animation (not a static sprite)
- [ ] Toolbox appears at cursor on `Ctrl+Shift+P` with all 4 inventory items functional
- [ ] Metrics persist to `pet_state.json` and decay correctly across app restarts
- [ ] Boss Key hides and restores the app with no residual artifacts
- [ ] Click-through works — user can interact with windows beneath the cat
- [ ] Alt+click drag interaction works to reposition the cat
- [ ] System tray icon is present with Show/Hide, Stats, and Quit options
- [ ] First-run onboarding tooltip displays once
- [ ] Auto-hide in fullscreen applications
- [ ] Works on Windows 10+ and macOS 12+
- [ ] Linux X11 support (stretch goal, not blocking)

---

## 9. Glossary

| Term | Definition |
|---|---|
| **FSM** | Finite State Machine — the behavioral engine that determines the cat's current action |
| **Surface** | Any horizontal boundary the cat can walk on: window top edges or the screen bottom |
| **Vertical Surface** | Any vertical boundary the cat can climb: screen left/right bezels or window side borders |
| **Controlled Chaos** | The behavior model where the cat acts autonomously with bounded randomness — it explores unpredictably but never blocks input, obscures content, or requires user intervention |
| **Boss Key** | An emergency hide hotkey borrowed from early PC gaming — instantly hides the application |
| **Click-Through** | The overlay window passes all mouse/keyboard events to the applications underneath |
| **Ground** | The effective bottom boundary — the screen bottom edge (above the OS taskbar) |