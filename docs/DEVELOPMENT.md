# Development guide

Technical documentation for anyone digging into the code — architecture,
project layout, and implementation notes. For what the app actually does
and how to run it, see the main [README](../README.md).

## Status

A Windows-to-Android re-platform onto [Flet](https://flet.dev) (one Python
codebase targeting both — `main_flet.py`, `app/ui/*_flet.py`) is being built
out feature-by-feature alongside the CustomTkinter app (`main.py`, the
shipping Windows build). The Flet build has its own setup wizard, dashboard,
category browser, quiz, settings screen, PIN-gated parent area, and full
lesson flow (including the Snake project's graphical lessons), built
against the same content and progress data. It isn't the shipping build
yet — `run.bat`/`run.sh` launch the CustomTkinter app; run the Flet build
with `flet run main_flet.py` (see "Running it" below).

## Running it

**Easiest way (no terminal needed):** double-click `run.bat` (Windows) or
run `./run.sh` (git-bash/macOS/Linux). First run sets up a virtual
environment and installs dependencies automatically (takes a minute);
every run after that just launches the app straight away, with no console
window left open.

Manually, if you prefer:

```powershell
.venv\Scripts\python.exe main.py
```

**The in-progress Flet re-platform** (see "Status" above) runs separately
and shares the same progress data:

```powershell
.venv\Scripts\python.exe -m flet run main_flet.py
```

## Running the tests

```powershell
.venv\Scripts\python.exe -m pytest tests\ -v
```

## Project layout

```
app/
  ui/        # screens: setup wizard, dashboard, lesson screen, code editor,
             # category browser, quiz, settings/theme picker, shared theme +
             # assets -- plain filenames are the CustomTkinter app; *_flet.py
             # is the parallel in-progress Flet re-platform (see "Status")
  audio/     # chime-sound selection logic shared by both UIs (playback
             # itself is UI-specific -- winsound for CTk, flet-audio for Flet)
  config/    # settings persistence + platform-appropriate data directory
  progress/  # SQLite-backed progress, stars, badges, streaks, activity log, quiz attempts
  parent/    # PIN-gated parent area (summary + recent activity)
  engine/    # lesson model + YAML-based lesson engine + category logic +
             # output validator + quiz model/engine + badge display metadata
  sandbox/   # AST safety check + two execution engines (see "Code execution
             # sandbox" below for why there are currently two)
  games/     # GameCanvas/GameWindow + in-process graphical runner (Snake,
             # Creative Arts, Arcade Lab, and Robot Adventure's execution model)
content/
  lessons/   # lesson content (YAML), kept separate from app code
  quiz/      # the quiz question bank (YAML), same content-not-code principle
  sounds/    # generated chime .wav files (scripts/generate_sounds.py) --
             # CTk reads these directly; assets/sounds/ is a copy Flet's
             # asset pipeline serves from (see app/ui/components/sound_player_flet.py)
  images/    # app icon (main-icon.png / .ico)
docs/
  app-screenshots/    # images used in the README
tests/       # pytest suite (1350+ tests)
app-data/    # gitignored, legacy dev-only location — see "Data storage" below
main.py      # CustomTkinter entry point
main_flet.py # Flet entry point (see "Status")
```

## How it works

### Today's Mission

`LessonEngine.main_path_lessons()` computes the guided "Today's Mission"
sequence live from lesson content rather than a hand-authored chain: the
"basics" intro lesson (Meet Python) once, then `category_level` 1 of
every category in `TODAYS_MISSION_CATEGORIES` (Numbers through Lists, in
that order), then level 2 of all of them, then level 3, and so on for as
many levels as those categories actually have. A category only advances
to its next level once every category has finished the current one — the
mission is a round-robin across topics, not one topic finished at a time.
Games, Snake, Code Crackers, and every other bonus category stay
reachable only through the category browser, never auto-assigned here.

`LessonEngine.resolve_current()` decides which lesson a child actually
lands on: trusts the stored "current lesson" pointer only if it's still
valid and not already completed, otherwise falls back to the first
incomplete lesson in `main_path_lessons()`, or the last one if everything
is done. `next_after()` does a positional lookup in that same computed
sequence to find what comes after a given lesson. Both keep working
correctly even as lessons are added, removed, or reordered in
content/lessons/ — nothing about the sequence is stored.

### Category browser

Every lesson belongs to a `category` (e.g. `"addition"`) and a
`category_level` (its position within that category, 1-based) — set in
its YAML, grouped by `LessonEngine.categories()` /
`lessons_in_category()`. From the dashboard's "🗺️ Categories" button, a
child picks a topic and sees each level in it as completed (⭐ + replay),
ready to play, or locked. `LessonEngine.is_unlocked()` unlocks a level
once every earlier level in the same category is complete — no separate
progress-tracking schema needed, it's derived entirely from
`completed_lesson_ids`.

This is a second, orthogonal way to reach lessons alongside the guided
"Today's Mission" flow above — the same lessons (Numbers through Lists)
are reachable either way, so progress made through one shows up in the
other automatically.

### Adaptive practice

- **Practice Quest** — a lesson gets an optional `concept_tags` list
  (e.g. `[loops, for-loops]`); after 3 failed attempts in a row on the
  same lesson (`ProgressStore.get_recent_failure_count()`), a dismissible
  suggestion offers 1-3 lessons sharing a tag
  (`LessonEngine.recommend_practice()`). It never blocks retrying, hints,
  or continuing — purely additive.
- **Quiz recommendations** — quiz questions carry the same `concept_tags`
  field; the results screen suggests practice lessons from the union of
  tags across every question missed that session
  (`recommend_practice_for_tags()`), tracked only in memory for the
  session, never persisted.

### Quiz

A standalone 300-question multiple-choice quiz covering the whole
curriculum (`content/quiz/quiz_questions.yaml`), reachable from both the
dashboard's "❓ Quick Quiz" card and a "❓ Quiz" tile in the category
browser. It's not a lesson category — multiple-choice doesn't fit the
`Lesson` model at all (no code editor, no sandboxed run, no output to
validate), so it gets its own small data model (`app/engine/quiz.py`)
and engine (`app/engine/quiz_engine.py`) instead of borrowing the lesson
one.

`QuizEngine.start_session()` returns a freshly shuffled copy of every
question each time it's called — both the question order and each
question's own answer-option order are re-randomized, so the correct
answer isn't always in the same position and no two playthroughs look
the same. Picking an option gives instant right/wrong feedback plus a
short explanation, then a results screen shows the score and offers
"Play Again" (which reshuffles) or back to the menu. `ProgressStore`
tracks the best score across attempts (`quiz_attempts` table), shown as
a "🏆 Best: X/Y" badge on both quiz entry points once played.

### Code Crackers

Two debugging-focused categories, structurally just more lessons
(`category: code_crackers` / `category: advanced_code_crackers`), no
special engine support needed: `starter_code` is deliberately broken,
`example_code` is the fix, and the child's job is to make their edited
code match `expected_output`. The "Advanced Code Crackers" lessons target
experienced developers (closures/late binding, mutable defaults, aliasing
vs. copying, floating-point precision, etc.) rather than beginner syntax
errors, and lean on Python's only-`random`-importable sandbox — see "Code
execution sandbox" below — for what's actually expressible: no `class`
statement will run in the sandbox today (`__build_class__` isn't in the
restricted builtins set), so class-attribute-sharing-style lessons use an
equivalent dict/factory-function example instead and explain the real
`class`-based version in prose.

### Code execution sandbox

Child code runs through two layers before anything executes:
1. **Static AST check** (`app/sandbox/safety.py`) — rejects imports and
   dangerous builtins (`eval`, `exec`, `open`, dunder access, …) before any
   process is spawned.
2. **Isolated subprocess** (`app/sandbox/runner.py` + `worker.py`) — runs in
   a separate `python -I` process with a restricted builtins set, a hard
   timeout (default 5s, kills runaway loops), and no filesystem/network
   access granted. The UI can cancel a run mid-flight via `RunHandle`.

Errors are translated into friendly, kid-appropriate messages
(`app/sandbox/errors.py`) with an optional "I'm curious" toggle to reveal
the raw traceback.

**Currently in transition**: an Android port is underway (see Status above
— the shipping app today is still Windows-only CustomTkinter). Android
doesn't allow a sandboxed app to spawn a sibling OS process, so
`app/sandbox/inprocess_runner.py` + `app/sandbox/watchdog.py` implement a
second engine that runs child code in-process instead, using a cooperative
watchdog (an AST transform injects a cheap check at the top of every loop
body) in place of the OS-level process kill. It also folds in what
`app/games/graphical_runner.py` does for Snake, so eventually there's one
engine instead of two. The old subprocess engine stays live and in use
until the Flet rewrite of the lesson screen actually switches over to the
new one — at that point `runner.py`, `worker.py`, and
`graphical_runner.py` get deleted.

### Lessons that take input

A lesson can set `input_prompt` in its YAML to show a labeled answer box
in the lesson screen instead of a terminal-style prompt. Whatever the
child types is piped to the sandboxed process's stdin, and
`expected_output` can contain `{input}` as a placeholder so any answer is
accepted as long as the child's program echoes it back correctly (see
Lesson 9, "Ask a Question"). Code that never receives input closes stdin
immediately, so an unexpected `input()` call fails fast with a friendly
message instead of hanging until the timeout.

### Games with randomness

Lessons 14–15 introduce `random`, which is now allowlisted through both
safety layers (`app/sandbox/safety.py`'s `ALLOWED_MODULES` and
`worker.py`'s restricted `__import__` — everything else stays blocked).
Because the outcome is genuinely random, these lessons validate with
`expected_output_pattern` (a regex covering every valid outcome) instead
of an exact string, via `validate_output()`'s `expected_output_pattern`
parameter.

### Graphical lessons (the Snake project)

Snake needs a live, continuously-updating window — something the
subprocess-sandboxed model (built for one-shot "run code, capture
stdout" exercises) can't provide. Tkinter widgets must also be created
and touched from the main thread, so this is a deliberate second
execution path with different tradeoffs, not a bug:

- **`app/games/game_canvas.py`** — the only surface a graphical lesson's
  code can touch: `set_title`, `set_background`, `draw_rect`,
  `move_shape`, `set_shape_position`, `delete_shape`, `clear`, `after`
  (schedule a callback without blocking), `on_key` (Up/Down/Left/Right/
  space only). Not a general Tkinter passthrough.
- **`app/games/game_window.py`** — owns the real `CTkToplevel` + `Canvas`
  a lesson draws into; one live window per lesson screen, recreated on
  each RUN.
- **`app/games/graphical_runner.py`** — runs the lesson's code **in the
  main process**, not a subprocess. It still applies the same AST safety
  check and restricted builtins as defense in depth, **plus a `while`-loop
  ban** (`check_code_safety(..., disallow_while=True)`), since there's no
  OS-level timeout here to recover from a runaway loop. Lessons use
  `game.after(ms, callback)` — a self-scheduling function — for animation
  instead, which returns control to Tkinter's own event loop immediately
  and never blocks.
- Validation for graphical lessons is "ran without raising" — the visual
  result in the game window *is* the feedback, matching the visual-first
  philosophy used throughout the app.

A lesson opts into this path with `graphical: true` in its YAML.

## Data storage

Everything lives locally and offline — no cloud, no accounts, no network
access at all. `settings.json` (child name, parent PIN salted + hashed,
selected theme, other preferences) and `progress.sqlite3` (level, stars,
badges, completed lessons, activity log) live in `%APPDATA%\PythonAdventure\`
on Windows.

The actual OS-appropriate location is resolved by
`resolve_platform_data_dir()` (`app/config/platform_paths.py`), kept
separate from `app/config/settings.py` so it can also target Android's
app-sandboxed storage directory without touching anything else. On first
run, `get_data_dir()` (`app/config/settings.py`) copies forward any data
left in this repo's old dev-convenience `app-data/` location — so moving
where data lives never resets a child's progress.
