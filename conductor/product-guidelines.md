# Product Guidelines

## Brand Voice & Personality

### Tone
- **Playful but Polished:** Mochi is a cute companion, not a toy. The tone should feel warm, whimsical, and slightly mischievous — like a real cat's personality.
- **Minimal Text:** Most interaction is visual/animated. When text is used (tooltips, tray menu), keep it concise and friendly.
- **No Anthropomorphism:** Mochi acts like a cat, not a human. Avoid human-like speech, emotions, or overly complex behaviors.

### Visual Identity
- **Soft, Warm Color Palette:** Pastel oranges, creams, gentle grays, and warm accent colors.
- **Rounded Aesthetics:** Rounded corners on all UI elements (toolbox, tooltips, tray menu).
- **Subtle Transparency:** UI overlays use semi-transparency (70-85% opacity) to feel light and non-intrusive.
- **Consistent Sprite Scale:** All sprites rendered at 2× scaling for crisp display on modern HiDPI screens.

## UX Principles

### 1. Zero Disruption
- Mochi must NEVER block click targets, obscure text, or interrupt user workflow.
- The overlay window is click-through by default — users can interact with everything underneath.
- All animations are subtle and non-flashy. No abrupt movements, screen flashes, or attention-grabbing effects.

### 2. Predictable Autonomy
- The cat's behavior follows clear, deterministic rules governed by the FSM.
- Users should be able to infer why the cat is doing what it's doing based on context.
- No random behavior that appears broken or confusing — every transition has a visible cause.

### 3. Discoverable Interaction
- Hotkeys are shown via the onboarding tooltip on first launch.
- The system tray icon provides a discoverable fallback for all actions.
- Toolbox items have visual cooldown indicators so users understand when they can interact again.

### 4. Graceful Degradation
- If a platform feature is unavailable (e.g., hotkey registration fails, permission denied), Mochi logs a warning and continues with reduced functionality.
- No crashes, no blocking error dialogs (except critical failures like missing sprite sheet).
- Missing assets fall back to placeholder visuals rather than crashing.

## Interaction Design Guidelines

### Hotkey Design
- All hotkeys use `Ctrl+Shift+<key>` combinations to avoid conflicts with common application shortcuts.
- Hotkeys must use platform-native registration APIs — no global keyboard hooks.
- Failed hotkey registration shows a non-blocking tray notification, not a crash.

### Animation Principles
- **Ease In/Out:** State transitions should feel natural. Avoid instant state switches.
- **Adaptive Frame Rate:** Higher frame rate during active movement, reduced during idle/sleep for CPU efficiency.
- **Loop Safety:** All looping animations must have seamless frame wrapping (no visual jumps).
- **Sprite Padding:** Each sprite cell includes 24px padding around the 32×32 cat frame to accommodate animation overshoot (tail, ears, limbs).

### Feedback Patterns
- **Immediate:** User actions (item deployment, drag) get instant visual feedback.
- **Subtle:** Passive cat behaviors (walking, climbing) have smooth, gradual transitions.
- **Deliberate:** Cooldown timers prevent spam and give each interaction weight.

## Accessibility Guidelines
- All interactive elements should be usable with keyboard-only input where feasible.
- Color is not the sole indicator of state (cooldown indicators use dimming + countdown text).
- Tooltip text uses a clear, readable font at minimum 11pt equivalent on screen.

## Performance Guidelines
- **Idle CPU < 1%** — Animation timer should adapt to lowest possible rate during idle/sleep.
- **Active CPU < 3%** — Even during walking/climbing, keep computation minimal.
- **RAM < 80 MB** — No heavy asset caching. Sprite frames are lightweight QPixmaps.
- **No GPU** — Software rendering only. No OpenGL/DirectX dependencies.
- **Write debouncing** — State file writes batched, max once per 5 seconds.

## Quality Standards (Definition of Done)
- All state transitions must work without visual glitches or stuck states.
- Click-through must work correctly in all modes (default, toolbox, drag).
- Hotkeys must not leak to or conflict with other applications.
- The application must not crash under any error condition (permission denied, corrupt state, missing assets).
- Test coverage > 80% for core logic modules (FSM, physics, pet_state).
- Zero lint errors (`ruff check`), zero type errors (`mypy strict`).
