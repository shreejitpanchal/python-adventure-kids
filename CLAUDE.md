# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

"Python Adventure" — an offline, GUI-based Python-learning app for kids. **Two UI codebases currently coexist in `app/ui/`:**

- **CustomTkinter (CTk)** — plain filenames (`app_window.py`, `lesson_screen.py`, `category_map.py`, `category_levels.py`, `dashboard.py`, `settings_screen.py`, `setup_wizard.py`, `theme.py`). This is the shipping Windows app, entry point `main.py`.
- **Flet** — `*_flet.py` counterparts (`app_window_flet.py`, `lesson_screen_flet.py`, etc.). This is an in-progress re-platform onto one Python codebase targeting **both Windows and Android**, entry point `main_flet.py` (`flet run main_flet.py`). It is being built out feature-by-feature alongside the CTk app, not yet a full replacement.

Know which one you're editing — `app/ui/theme.py` vs `app/ui/theme_flet.py` etc. are separate, parallel implementations, not shared code. Non-UI layers (`app/engine`, `app/progress`, `app/config`) are shared by both.

## Commands

Run all from the repo root, using the project venv at `.venv\Scripts\python.exe` (created by `run.bat`/`run.sh` on first launch; on Windows the venv layout is `.venv\Scripts\`, not `.venv\bin\`).

```powershell
# Run the shipping CustomTkinter app
.venv\Scripts\python.exe main.py

# Run the in-progress Flet re-platform
.venv\Scripts\python.exe -m flet run main_flet.py

# Full test suite
.venv\Scripts\python.exe -m pytest tests\ -v

# A single test file / test
.venv\Scripts\python.exe -m pytest tests\test_lesson_engine.py -v
.venv\Scripts\python.exe -m pytest tests\test_lesson_engine.py::test_name -v
```

There is no linter or formatter configured in this repo (no ruff/flake8/black/mypy config) — don't invent commands for one.

## Architecture

### Content is data, not code

Lessons live as YAML files under `content/lessons/` (one file per lesson), loaded by `LessonEngine._load()` (`app/engine/lesson_engine.py`) into `Lesson` dataclass instances (`app/engine/lesson.py`). **Adding or changing a lesson never requires touching app code** — add a YAML file. Key `Lesson` fields beyond the obvious: `category`/`category_level` (bonus/category-browser placement — see below), `main_path` (guided-curriculum vs. bonus level), `next_lesson_id` (chains the guided sequence), `expected_output` / `expected_output_pattern` (exact-match vs. regex, for lessons with randomized output), `input_prompt` (stdin-fed answer box), `graphical` (opts into the Snake-style live-window execution path).

### Two parallel ways to reach a lesson

1. **"Today's Mission"** — a single guided sequence computed live by `LessonEngine.main_path_lessons()`: the `basics` intro once, then level 1 of every category in `TODAYS_MISSION_CATEGORIES`, then level 2 of each, and so on (round-robin, derived from `category`/`category_level` — nothing about order is stored, and categories outside that list never leak in). `Lesson.next_lesson_id` and `Lesson.main_path` are legacy fields still present in YAML but no longer read. `LessonEngine.resolve_current()` decides where a returning child lands: trusts the stored "current lesson" pointer only if still valid and incomplete, else falls back to the first incomplete lesson in that sequence.
2. **Category browser** — every lesson has a `category` + 1-based `category_level`; `LessonEngine.categories()`/`lessons_in_category()` group and order them, `is_unlocked()` derives lock state purely from `completed_lesson_ids` (no separate unlock-tracking schema — a level unlocks once every earlier `category_level` in the same category is complete). Category display metadata (title/icon/color) is separate, in `app/engine/categories.py`'s `CATEGORY_META` — a category with no entry there falls back to `DEFAULT_META`, but the category itself still works; the real set of categories is derived entirely from what's present in lesson YAML.

### Code execution sandbox — two engines by design, converging to one

1. **Subprocess engine** (`app/sandbox/runner.py` + `worker.py`, used by the CTk app for ordinary lessons): static AST safety check → isolated `python -I` subprocess with a hard timeout (default 5s) that kills runaway loops. Cancelable mid-run via `RunHandle`.
2. **In-process engine** (`app/sandbox/inprocess_runner.py` + `watchdog.py`, used by the Flet app for everything and by the CTk app for graphical lessons): exists because **Android can't spawn a sibling OS process** from a sandboxed app. Same AST safety check, but the runaway-loop guard is cooperative — an AST transform injects a cheap watchdog tick at the top of every loop body and inside every comprehension, and `time.sleep` is served by a watchdog-aware replacement, since there's no OS-level process to kill. A run that still can't be interrupted can't hold the engine hostage either: the next run waits at most its own timeout for the run lock, then reports the sandbox as busy.

Both engines share the same two layers — extend these, never hand-roll a restricted import or builtins dict inside an engine:
- `app/sandbox/safety.py` — the AST rules: `BLOCKED_NAMES`; `ALLOWED_MODULES` (the **only** place the module allowlist lives); dunder identifiers anywhere they could be bound (so nothing can shadow the watchdog's `__pyadv_tick__`); frame/generator/traceback introspection attributes (`gi_frame`, `f_back`, …); and leading-underscore attributes (`random._os` is the real `os` module), except namedtuple's `_replace`-style API.
- `app/sandbox/allowed_builtins.py` — the runtime environment: `build_safe_builtins()` returns the restricted builtins plus a restricted `__import__` that hands back a *view* of each allowlisted module containing only its public, non-module attributes (so `json.decoder` doesn't exist to walk through to `sys`). Views are per run, so one run mutating `random.randint` can't affect the next.

`app/sandbox/errors.py` translates raw exceptions into kid-friendly messages, with an "I'm curious" toggle to reveal the real traceback. Once the Flet lesson screen fully replaces the CTk one, `runner.py` and `worker.py` are meant to be deleted in favor of the in-process engine. `app/games/graphical_runner.py` is already only a compatibility wrapper over it (kept for `tests/test_graphical_runner.py`) and can be deleted together with that test.

**Graphical lessons** (`graphical: true` in the YAML — Snake, Creative Arts, Arcade Lab, Robot Adventure) are not a separate engine: both UIs call the in-process `run_code(code, game=..., disallow_while=True)`, injecting a restricted drawing surface as `game` (CTk: `app/games/game_canvas.py` drawing into a `CTkToplevel` owned by `app/games/game_window.py`; Flet: `app/games/game_canvas_flet.py` drawing into an inline canvas). The surface exposes `set_title`, `draw_rect`, `move_shape`, `on_key`, `after`, etc. — not a general Tkinter/Flet passthrough. `disallow_while=True` bans `while` loops outright because top-level code must hand control back to the UI loop; lessons animate with `game.after(ms, callback)` self-scheduling instead. Validation is "ran without raising" (plus `ast_contains` / `requires_goal_reached` when set) rather than output-matching.

### Output validation

`validate_output()` (`app/engine/validator.py`) compares sandboxed stdout against `Lesson.expected_output` (supports a `{input}` placeholder templated from what the child typed, for input-taking lessons) or, for lessons with genuinely randomized output, `expected_output_pattern` (a regex covering every valid outcome).

### Data storage

Fully offline, no network/cloud/accounts. `settings.json` + `progress.sqlite3` (progress, stars, badges, activity log — `app/progress/store.py`) live in an OS-appropriate app-data directory resolved by `resolve_platform_data_dir()` (`app/config/platform_paths.py`), kept separate from `app/config/settings.py` specifically so it can also target Android's sandboxed storage without touching Windows logic. On first run, `get_data_dir()` migrates forward any data found in this repo's legacy dev-convenience `app-data/` folder (gitignored) so relocating storage never resets a child's progress.

### Directory layout

```
app/
  ui/        # CTk screens (plain names) + Flet screens (*_flet.py) — see "Two UI codebases" above
  ui/components/  # Flet-only shared widgets: adventure_kit (game-world look: sky headers, chunky cards, power bars),
                  # motion (bounded implicit animations), codey_avatar (mascot), streak_flame, treasure_chest,
                  # celebration (confetti/level-up), map_path (Adventure Map road/nodes), game_button, macro_toolbar, sound_player
  engine/    # Lesson dataclass, YAML loader, category logic, output validator
  sandbox/   # AST safety + shared restricted environment (allowed_builtins) + subprocess engine (runner/worker) + in-process engine (inprocess_runner/watchdog)
  games/     # restricted drawing surfaces injected into graphical lessons as `game`: game_canvas + game_window (CTk), game_canvas_flet (Flet); graphical_runner is a to-be-deleted wrapper
  progress/  # SQLite-backed progress/stars/badges/streaks/daily chest/activity log
  config/    # settings persistence + platform-appropriate data directory resolution
  parent/    # parent area (CTk only currently; Flet equivalent is app/ui/parent_dashboard_flet.py) --
             # not currently PIN-gated: Settings.set_parent_pin()/verify_parent_pin() exist but no screen calls them
content/
  lessons/   # one YAML file per lesson — the actual curriculum content
  images/    # app icon
tests/       # pytest suite, one file per module roughly mirroring app/
main.py       # CTk entry point
main_flet.py  # Flet entry point
build/        # gitignored — flet build output (Windows/Android packaging), not source
```
