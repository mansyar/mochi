# Mochi — Agent Guide

## Quick commands (all use `uv run`)

| Task | Command |
|---|---|
| Install | `uv sync --extra dev` |
| Lint | `uv run ruff check src/` |
| Lint + fix | `uv run ruff check --fix src/` |
| Format check | `uv run ruff format --check src/` |
| Format | `uv run ruff format src/` |
| Typecheck | `uv run mypy src/mochi/` |
| Test all | `uv run pytest` |
| Test single file | `uv run pytest tests/test_config.py` |
| Test parallel | `uv run pytest -n auto` |
| Run app | `uv run python -m mochi` |
| Full pre-commit | `uv run ruff check src/ && uv run ruff format --check src/ && uv run mypy src/mochi/ && uv run pytest` |

## Tooling quirks

- **Package manager is `uv`** (not pip). Never use `pip install`. The lockfile `uv.lock` is committed.
- **Line length**: 100 (Ruff default is 88). Configured in `pyproject.toml`.
- **Known first-party**: `mochi` — Ruff's isort groups it correctly.
- **mypy strict mode**: on. Exceptions for `pywinctl` and `pymonctl` (missing stubs).
- **File limit**: max 500 lines per `.py` file (enforced by pre-commit hook).
- **pytest config**: `qt_api = "pyside6"`, coverage auto-enabled (`--cov=src/mochi`), target 80%+.
- **Pre-push**: coverage threshold check via `uv run pytest --cov-fail-under=80`.

## Testing notes

- **Canvas/widget tests** require `qtbot` fixture from `pytest-qt`. Always call `qtbot.addWidget(w)`.
- **1 skipped test**: `test_green_pixel_at_bottom_center` — needs visible display, skip unconditionally.
- **Logger tests**: call `teardown_method()` to clear root handlers between tests. Use `tmp_path` for log files.
- **Platform tests**: mock `sys.platform` and `ctypes.windll` — never call real win32 APIs.

## Dev conventions

- **TDD**: Red (failing test) → Green (passing) → Refactor, per `conductor/workflow.md`.
- **Conductor methodology**: each feature is a "Track" with spec + plan tracked in `conductor/`. Completed tracks archived to `conductor/archive/`.
- **No global keyboard hooks**: use platform-native APIs only (`RegisterHotKey` / `RegisterEventHotKey` / `XGrabKey`). No `pynput`.
- **No GPU**: software rendering only. No OpenGL/DirectX.
- **No network**: fully offline app, no telemetry.
- **Click-through**: on by default. Toggled via `set_click_through()` in `platform.py` (Win32: `WS_EX_TRANSPARENT` via ctypes).
- **Sprite scale**: 2× on HiDPI screens. Cell size 64×64 px with 24px padding.

## Codebase Search (SocratiCode)

This project is indexed with SocratiCode. Always use its MCP tools to explore the codebase
before reading any files directly.

### Workflow

1. **Start most explorations with `codebase_search`.**
   Hybrid semantic + keyword search (vector + BM25, RRF-fused) runs in a single call.
   - Use broad, conceptual queries for orientation: "how is authentication handled",
     "database connection setup", "error handling patterns".
   - Use precise queries for symbol lookups: exact function names, constants, type names.
   - Prefer search results to infer which files to read — do not speculatively open files.
   - **When to use grep instead**: If you already know the exact identifier, error string,
     or regex pattern, grep/ripgrep is faster and more precise — no semantic gap to bridge.
     Use `codebase_search` when you're exploring, asking conceptual questions, or don't
     know which files to look in.

2. **Follow the graph before following imports.**
   Use `codebase_graph_query` to see what a file imports and what depends on it before
   diving into its contents. This prevents unnecessary reading of transitive dependencies.
   - **Before modifying or deleting a file**, check its dependents with `codebase_graph_query`
     to understand the blast radius.
   - **When planning a refactor**, use the graph to identify all affected files before
     making changes.

3. **Use Impact Analysis BEFORE refactoring, renaming, or deleting code.**
   The symbol-level call graph (`codebase_impact`, `codebase_flow`, `codebase_symbol`,
   `codebase_symbols`) goes one step deeper than the file graph: it knows which
   functions and methods call which.
   - `codebase_impact` answers "what breaks if I change X?" (blast radius — every file
     that transitively calls into the target).
   - `codebase_flow` answers "what does this code do?" by tracing forward from an entry
     point. Call with no `entrypoint` to discover candidate entry points (auto-detected
     via orphans, conventional names like `main()`, framework routes, tests).
   - `codebase_symbol` gives a 360° view of one function: definition, callers, callees.
   - `codebase_symbols` lists symbols in a file or searches by name.
   - Always prefer these over reading multiple files when the question is about
     dependencies between functions, not concepts.

4. **Read files only after narrowing down via search.**
   Once search results clearly point to 1–3 files, read only the relevant sections.
   Never read a file just to find out if it's relevant — search first.

5. **Use `codebase_graph_circular` when debugging unexpected behaviour.**
   Circular dependencies cause subtle runtime issues; check for them proactively.
   Also run `codebase_graph_circular` when you notice import-related errors or unexpected
   initialisation order.

6. **Check `codebase_status` if search returns no results.**
   The project may not be indexed yet. Run `codebase_index` if needed, then wait for
   `codebase_status` to confirm completion before searching.

7. **Leverage context artifacts for non-code knowledge.**
   Projects can define a `.socraticodecontextartifacts.json` config to expose database
   schemas, API specs, infrastructure configs, architecture docs, and other project
   knowledge that lives outside source code. These artifacts are auto-indexed alongside
   code during `codebase_index` and `codebase_update`.
   - Run `codebase_context` early to see what artifacts are available.
   - Use `codebase_context_search` to find specific schemas, endpoints, or configs
     before asking about database structure or API contracts.
   - If `codebase_status` shows artifacts are stale, run `codebase_context_index` to
     refresh them.

### When to use each tool

| Goal | Tool |
|------|------|
| Understand what a codebase does / where a feature lives | `codebase_search` (broad query) |
| Find a specific function, constant, or type | `codebase_search` (exact name) or grep if you know already the exact string |
| Find exact error messages, log strings, or regex patterns | grep / ripgrep |
| See what a file imports or what depends on it | `codebase_graph_query` |
| Check blast radius before modifying or deleting a file | `codebase_impact` (symbol-level) or `codebase_graph_query` (file-level) |
| **What breaks if I change function X?** | `codebase_impact target=X` |
| **What does this entry point actually do?** | `codebase_flow entrypoint=X` |
| **List entry points in this codebase** | `codebase_flow` (no args) |
| **Who calls this function and what does it call?** | `codebase_symbol name=X` |
| **What functions/classes exist in this file?** | `codebase_symbols file=path` |
| **Search for symbols by name across the project** | `codebase_symbols query=X` |
| Spot architectural problems | `codebase_graph_circular`, `codebase_graph_stats` |
| Visualise module structure | `codebase_graph_visualize` |
| Verify index is up to date | `codebase_status` |
| Discover what project knowledge (schemas, specs, configs) is available | `codebase_context` |
| Find database tables, API endpoints, infra configs | `codebase_context_search` |