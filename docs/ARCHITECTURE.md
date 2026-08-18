# Architecture

A reference for architects/engineers evaluating or extending this codebase:
system context, component structure, domain model (class diagrams), key
runtime flows (sequence diagrams), the persistence model, and the design
decisions behind them. For a plain-language feature tour see the
[README](../README.md); for a narrative walkthrough of each subsystem see
[DEVELOPMENT.md](DEVELOPMENT.md). This document is the structural/visual
counterpart to that narrative.

## 1. System context

Fully offline, single-user (one child profile per install), no backend.

```mermaid
flowchart TB
    child["Child / Parent"]
    subgraph device["Device (Windows desktop or Android tablet)"]
        ctk["CustomTkinter app\n(main.py) — shipping Windows build"]
        flet["Flet app\n(main_flet.py) — in-progress\nWindows + Android re-platform"]
        core["Shared core\napp/engine, app/progress, app/config"]
        sandbox["Code execution sandbox\n(subprocess or in-process)"]
        fsdata[("settings.json +\nprogress.sqlite3\n(local disk)")]
        content[("content/*.yaml\n(lessons, quiz — read-only)")]
    end

    child -->|uses| ctk
    child -->|uses| flet
    ctk --> core
    flet --> core
    ctk --> sandbox
    flet --> sandbox
    core --> fsdata
    core --> content
    sandbox -.->|no network, no filesystem\naccess beyond stdin/stdout| sandbox
```

No accounts, no cloud sync, no telemetry, no network calls anywhere in the
runtime path — the sandbox process is deliberately denied network access
as part of its safety model, and the app itself never makes an outbound
request.

## 2. Two UI codebases, one shared core

The single most important structural fact about this repo: **there are two
complete, parallel UI implementations of the same product**, chosen per
screen at import time by filename convention, not by a runtime feature
flag.

```mermaid
flowchart LR
    subgraph ui_ctk["app/ui/*.py (CustomTkinter)"]
        direction TB
        aw["app_window.py\nApp(ctk.CTk)"]
        ls["lesson_screen.py"]
        db["dashboard.py"]
        ss["settings_screen.py"]
        th["theme.py"]
        aw --> ls & db & ss
    end

    subgraph ui_flet["app/ui/*_flet.py (Flet)"]
        direction TB
        awf["app_window_flet.py\nmain(page)"]
        lsf["lesson_screen_flet.py"]
        dbf["dashboard_flet.py"]
        ssf["settings_screen_flet.py"]
        thf["theme_flet.py"]
        asf["app_state_flet.py\nAppState"]
        awf --> lsf & dbf & ssf
        awf --> asf
    end

    subgraph shared["Shared core (imported by both, UI-agnostic)"]
        engine["app/engine\nLessonEngine, QuizEngine,\nvalidator, categories, badges,\ncourse_status"]
        progress["app/progress\nProgressStore (SQLite)"]
        config["app/config\nSettings, load/save,\nplatform data dir"]
        sandbox["app/sandbox\ntwo execution engines"]
        games["app/games\nSnake / graphical lessons"]
        audio["app/audio\nsound-choice logic\n(playback stays UI-specific)"]
    end

    ui_ctk --> shared
    ui_flet --> shared
```

Neither UI imports from the other. `theme.py`/`theme_flet.py` are a
**deliberate duplicate** — same `ThemePreset`/`CategoryMeta`/`BadgeMeta`
shape and the same preset *keys*, independently-chosen concrete values per
platform (a CTk-only Windows font vs. Flet's bundled cross-platform font,
for instance). Once Flet reaches parity, the CTk tree and `runner.py` /
`worker.py` / `graphical_runner.py` are meant to be deleted — this is a
migration-in-progress, not a permanent fork.

## 3. Domain model — class diagram

The engine layer is pure, dependency-light Python: dataclasses plus
stateless(ish) loader/query classes. Nothing here imports `customtkinter`
or `flet`.

```mermaid
classDiagram
    class Lesson {
        +str id
        +str title
        +int level
        +str objective
        +str explanation
        +str example_code
        +str starter_code
        +str challenge
        +str expected_output
        +list~str~ hints
        +int reward_stars
        +str badge
        +str next_lesson_id
        +str input_prompt
        +str expected_output_pattern
        +bool graphical
        +str category
        +int category_level
        +bool main_path
        +list~str~ ast_contains
        +bool requires_goal_reached
        +list~str~ concept_tags
        +bool is_quiz
    }

    class LessonEngine {
        -dict~str,Lesson~ _lessons
        -list~str~ _order
        +get(lesson_id) Lesson
        +has(lesson_id) bool
        +first() Lesson
        +all_in_order() list~Lesson~
        +main_path_lessons() list~Lesson~
        +next_after(lesson_id) Lesson
        +resolve_current(completed_ids, stored_current_id) Lesson
        +categories() list~str~
        +lessons_in_category(category) list~Lesson~
        +is_unlocked(lesson, completed_ids) bool
        +next_unlocked_in_category(category, completed_ids) Lesson
        +recommend_practice(lesson_id, completed_ids, limit) list~Lesson~
        +recommend_practice_for_tags(tags, completed_ids, limit) list~Lesson~
        +category_completion(completed_ids) dict
    }
    LessonEngine "1" o-- "many" Lesson : loads from content/lessons/*.yaml

    class QuizQuestion {
        +str id
        +str question
        +list~str~ options
        +int correct
        +str explanation
        +list~str~ concept_tags
    }
    class QuizEngine {
        -list~QuizQuestion~ _questions
        +start_session() list~QuizQuestion~
        +start_session_for_tags(tags, count) list~QuizQuestion~
        +__len__() int
    }
    QuizEngine "1" o-- "many" QuizQuestion : loads from content/quiz/*.yaml

    class ChapterStatus {
        +str category
        +list~Lesson~ items
        +int completed_count
        +int total_count
    }
    class CourseStatus {
        +list~ChapterStatus~ chapters
        +int items_done
        +int items_total
        +int stars_earned
    }
    CourseStatus "1" o-- "many" ChapterStatus
    note for CourseStatus "Built by course_status.py's compute_course_status() function, the same shape as hub_status.py's compute_hub_status()."

    class Settings {
        +str child_name
        +bool sound_enabled
        +bool animations_enabled
        +bool reduced_motion
        +str theme
        +str font_family
        +str font_size
        +str parent_pin_salt
        +str parent_pin_hash
        +bool setup_complete
        +has_parent_pin() bool
        +set_parent_pin(pin)
        +verify_parent_pin(pin) bool
    }

    class ProgressStore {
        -sqlite3.Connection _conn
        +get_summary() ProfileSummary
        +complete_lesson(lesson_id, stars)
        +get_completed_lesson_ids() list~str~
        +award_badge(badge_id) bool
        +get_badge_ids() list~str~
        +record_quiz_attempt(score, total)
        +get_best_quiz_score() tuple
        +add_xp(amount) PlayerLevel
        +get_player_level() PlayerLevel
        +log_event(lesson_id, event_type, detail)
        +get_recent_failure_count(lesson_id) int
        +get_weekly_summary() WeeklySummary
        +reset_progress()
    }
    class ProfileSummary {
        +int level
        +int total_stars
        +str current_lesson_id
        +int streak_days
        +int lessons_completed
        +int badges_earned
    }
    class PlayerLevel {
        +int level
        +int xp_into_level
        +int xp_needed_for_level
        +int total_xp
    }
    class WeeklySummary {
        +int lessons_completed
        +int stars_earned
        +int quiz_attempts
        +int badges_earned
        +int active_days
    }
    ProgressStore ..> ProfileSummary : returns
    ProgressStore ..> PlayerLevel : returns
    ProgressStore ..> WeeklySummary : returns

    class ThemePreset {
        +str key
        +str title
        +bool is_dark
        +str bg
        +str card
        +str text
        +str primary
        +int min_level
    }
    class CategoryMeta {
        +str title
        +str icon
        +str color
    }
    class BadgeMeta {
        +str title
        +str icon
        +str description
    }

    class AppStateFlet {
        +Settings settings
        +ProgressStore progress
        +LessonEngine lesson_engine
        +QuizEngine quiz_engine
        +theme ThemePreset
        +font_family str
        +font_scale float
        +apply_theme(key)
        +apply_font(family_key, size_key)
        +save_settings()
    }
    AppStateFlet --> Settings
    AppStateFlet --> ProgressStore
    AppStateFlet --> LessonEngine
    AppStateFlet --> QuizEngine
    AppStateFlet ..> ThemePreset : resolves via theme_flet.get_preset()
```

`App` (the CTk equivalent of `AppStateFlet`, in `app/ui/app_window.py`) is
structurally the same composition — `Settings` + `ProgressStore` +
`LessonEngine` + `QuizEngine` as instance attributes on the `ctk.CTk`
subclass itself — just without a `@property`-based theme/font resolver
(CTk's `theme.py` uses module-level globals reassigned by
`apply_theme()`/`apply_font()` instead, since CTk screens are destroyed
and rebuilt on navigation rather than holding a long-lived state object).

## 4. Sandbox architecture

Two independent execution engines exist side by side, both applying the
same static safety check first.

```mermaid
flowchart TB
    code["Child's submitted code (str)"]
    safety["app/sandbox/safety.py\ncheck_code_safety()\nAST walk: blocks eval/exec/open/\ndunder access, disallowed imports\n(only random is allowlisted)"]
    code --> safety
    safety -->|SafetyViolation| blocked["Blocked message shown,\nnothing executes"]
    safety -->|passes| branch{"Which UI /\nlesson type?"}

    branch -->|CTk, or Flet\nnot-yet-migrated| subprocess["app/sandbox/runner.py\n+ worker.py\n\nSeparate python -I process,\nrestricted builtins,\n5s hard timeout,\nno filesystem/network"]
    branch -->|Flet, Android-safe --\nno subprocess spawn allowed| inproc["app/sandbox/inprocess_runner.py\n+ watchdog.py\n\nRuns in-process; a cooperative\nAST-injected loop-body check\nstands in for the OS timeout"]
    branch -->|graphical: true --\nSnake project| graphical["app/games/graphical_runner.py\n\nRuns in the MAIN process against\na live game window; while-loops\nbanned outright, no timeout\nfallback exists here"]

    subprocess --> result["ExecutionResult\n(stdout, stderr, success, blocked)"]
    inproc --> result
    graphical --> result
    result --> validator["app/engine/validator.py\nvalidate_output() /\nvalidate_ast_contains()"]
    validator --> outcome{"Correct?"}
    outcome -->|yes| reward["ProgressStore.complete_lesson()\n+ award_badge() + reward UI"]
    outcome -->|no| friendly["app/sandbox/errors.py\ntranslates to a kid-friendly\nmessage + optional raw traceback"]
```

The in-process engine and the graphical runner are on a deliberate
convergence path: once the Flet lesson screen is the only one left,
`runner.py`, `worker.py`, and `graphical_runner.py` get deleted and
everything routes through one engine.

## 5. Sequence diagrams

### 5.1 App startup and initial routing

```mermaid
sequenceDiagram
    participant User
    participant Entry as main.py / main_flet.py
    participant App as App / AppState
    participant Cfg as app/config/settings.py
    participant Engine as LessonEngine / QuizEngine
    participant Store as ProgressStore

    User->>Entry: launch
    Entry->>App: construct
    App->>Cfg: load_settings()
    Cfg-->>App: Settings (defaults if no settings.json yet)
    App->>Store: open progress.sqlite3 (creates schema if missing)
    App->>Engine: load content/lessons/*.yaml, content/quiz/*.yaml
    alt settings.setup_complete is False
        App->>User: show Setup Wizard (child's name only)
    else already set up
        App->>Engine: resolve_current(completed_ids, stored_current_id)
        App->>User: show Dashboard (Today's Mission card + stats)
    end
```

### 5.2 Running code and completing a lesson

```mermaid
sequenceDiagram
    participant Child
    participant Screen as LessonScreen
    participant Safety as sandbox/safety.py
    participant Sandbox as runner.py / inprocess_runner.py
    participant Validator as engine/validator.py
    participant Store as ProgressStore
    participant Engine as LessonEngine

    Child->>Screen: click RUN
    Screen->>Safety: check_code_safety(code)
    alt violation found
        Safety-->>Screen: SafetyViolation
        Screen-->>Child: blocked message
    else safe
        Screen->>Sandbox: run_code(code, stdin=...)
        Sandbox-->>Screen: ExecutionResult(stdout, stderr, success)
        alt not result.success
            Screen->>Screen: errors.translate_error(stderr)
            Screen-->>Child: friendly error + "I'm curious" toggle
        else ran cleanly
            Screen->>Validator: validate_output(stdout, expected_output)
            alt output correct
                Screen->>Store: complete_lesson(id, stars)
                Screen->>Store: award_badge(id) if lesson.badge
                Screen->>Engine: next_after(lesson.id)
                Engine-->>Screen: next Lesson in Today's Mission (or none)
                Screen->>Store: set_current_lesson(next.id)
                Screen-->>Child: inline reward card:\n"Onward" + "Next Lesson" buttons
            else output wrong
                Screen->>Store: log_event(id, "attempt_wrong_output")
                Screen->>Engine: get_recent_failure_count(id) >= 3?
                opt threshold crossed
                    Screen->>Engine: recommend_practice(id, completed_ids)
                    Screen-->>Child: dismissible "Practice Quest" suggestion
                end
            end
        end
    end
```

### 5.3 Settings change (theme or font) and live repaint

```mermaid
sequenceDiagram
    participant User
    participant Screen as SettingsScreen
    participant State as AppState / theme.py globals
    participant Cfg as app/config/settings.py

    User->>Screen: tap a theme / font-size / font-style option
    Screen->>State: apply_theme(key) or apply_font(family_key, size_key)
    State->>State: mutate Settings in memory
    State->>Cfg: save_settings() (JSON write to disk)
    Note over Screen,State: Neither UI has live-reactive widgets --<br/>colors/fonts are read fresh only when a screen is (re)built.
    Screen->>Screen: rebuild the current screen<br/>CTk destroys+recreates the frame, Flet does page.views.clear()+append()
    Screen-->>User: new theme/font visible immediately
```

### 5.4 Parent Area — first visit sets a PIN, later visits verify it

```mermaid
sequenceDiagram
    participant Parent
    participant Area as Parent Area
    participant Cfg as Settings

    Parent->>Area: open Parent Area
    Area->>Cfg: has_parent_pin()?
    alt no PIN set yet -- first-ever visit
        Area-->>Parent: "Set a Parent PIN" (enter, then confirm)
        Parent->>Area: enter PIN twice (matching)
        Area->>Cfg: set_parent_pin(pin) (salted SHA-256)
        Area->>Cfg: save_settings()
        Area-->>Parent: Parent Area summary unlocked
    else PIN already set
        Area-->>Parent: "Enter the 4-digit PIN"
        Parent->>Area: enter PIN
        Area->>Cfg: verify_parent_pin(pin)
        alt correct
            Area-->>Parent: Parent Area summary unlocked
        else incorrect
            Area-->>Parent: "Incorrect PIN", stays locked
        end
    end
    opt Parent renames child or resets progress
        Parent->>Area: edit name / confirm reset
        Area->>Cfg: settings.child_name = new_name, then save_settings()
        Area->>Area: ProgressStore.reset_progress() (on confirmed reset)
    end
```

## 6. "Today's Mission" — computed, not stored

A frequently-asked design question, worth a dedicated diagram: nothing
about lesson *order* is stored anywhere in the database. It's recomputed
from lesson content every time.

```mermaid
flowchart LR
    basics["basics\n(Meet Python)\nonce"] --> L1

    subgraph L1["Level 1 — every category in turn"]
        direction LR
        n1["numbers"] --> a1["addition"] --> s1["subtraction"] --> m1["multiplication"] --> d1["division"] --> v1["variables"] --> st1["strings"] --> i1["input"] --> c1["conditionals"] --> lo1["loops"] --> f1["functions"] --> li1["lists"]
    end
    L1 --> L2["Level 2 — same 12 categories,\nsame order"]
    L2 --> L3["Level 3 ... up to however many\nlevels each category has (20)"]

    note1["A category only advances to its\nnext level once ALL 12 categories\nhave finished the current level --\nround-robin, not one-topic-at-a-time."]
```

`LessonEngine.main_path_lessons()` walks `category`/`category_level`
fields on lesson content to build this sequence fresh on every call;
`resolve_current()` just finds the first ID in that sequence not present
in `completed_lesson_ids`. Games, Snake, Code Crackers, the Python
Learning course's `course_*` categories, and every other bonus category
are simply never included in this walk — they're reached exclusively
through the category browser (or, for the course, its own chapter
screens), which uses the same content but a different, independent
traversal (`lessons_in_category()` sorted by `category_level`,
unlock-gated by `is_unlocked()`).

## 7. Persistence model

Two separate files per install, both resolved by
`app/config/platform_paths.py`'s `resolve_platform_data_dir()` (Windows:
`%APPDATA%\PythonAdventure\`; Android: the app's sandboxed storage dir).

```mermaid
erDiagram
    profile {
        int id PK "always 1 (single profile)"
        int level
        int total_stars
        text current_lesson_id
        int streak_days
        text last_played_date
    }
    lesson_completions {
        text lesson_id PK
        int stars_earned
        text completed_at
    }
    badges {
        text badge_id PK
        text earned_at
    }
    activity_log {
        int id PK
        text lesson_id
        text event_type
        text detail
        text timestamp
    }
    quiz_attempts {
        int id PK
        int score
        int total
        text completed_at
    }
    player_xp {
        int id PK "always 1"
        int total_xp
    }
```

`settings.json` (separate file, not SQLite — small, human-editable key/value
config) holds `child_name`, `sound_enabled`, `theme`, `font_family`,
`font_size`, `parent_pin_salt`/`parent_pin_hash` (PIN is salted SHA-256,
never stored in plaintext), and `setup_complete`. `load_settings()` filters
incoming JSON keys against `Settings.__dataclass_fields__` before
construction, so an old file missing new fields (or a newer file with
fields this version doesn't know about) never crashes — a new field just
takes its dataclass default.

## 8. Cross-cutting design decisions

- **Content is data, not code.** Every lesson and quiz question is a YAML
  file under `content/`. Adding, editing, or removing one never requires
  an app-code change — `LessonEngine`/`QuizEngine` just re-glob the
  directory on next load.
- **Derived state over stored state.** Category unlock status, module/
  mission progress, category mastery percentages, and badge eligibility
  are all *computed live* from `completed_lesson_ids` + `get_badge_ids()`
  on every read, never cached in their own schema. This is what makes
  content changes (adding a lesson, reordering a category) retroactively
  correct for existing save files with zero migration code.
- **Semantic settings keys, per-UI concrete mapping.** `theme`,
  `font_family`, and `font_size` in `Settings` are abstract keys (e.g.
  `"classic"`), not literal color hexes or font names. Each UI's own
  `theme.py`/`theme_flet.py` maps the same key to whatever's actually
  appropriate on that platform (a Windows-only system font vs. a bundled
  cross-platform one) via a `dict.get(key, DEFAULT)` — so the one shared
  `settings.json` is meaningful (and safely falls back) no matter which
  UI last wrote it.
- **Two sandbox engines by necessity, not by design preference.** Android
  forbids spawning a sibling OS process from a sandboxed app, so the
  subprocess-based engine (real OS-level timeout, strongest isolation)
  can't be the only implementation. The in-process engine exists purely
  to make Android possible and is intended to fully replace the subprocess
  one once the Flet UI is complete (see Section 4).
- **A course chapter is just a category; a quiz item is just a Lesson.**
  The Python Learning course (Section 6 note above) deliberately reuses
  the existing category/`is_unlocked()`/`complete_lesson()` machinery
  instead of a parallel "chapter" content model, and models its quiz
  item as a `Lesson` with an `is_quiz` flag rather than a new content
  type — so quiz completion gets unlock tracking, star rewards, and XP
  for free, and the course needed zero new `ProgressStore` schema.
- **Dual-UI parity by convention, not abstraction.** Rather than building
  a shared widget/view abstraction over both CTk and Flet (which would
  constrain both to their lowest common capability), each UI is a
  complete, independent implementation against the same core. This costs
  duplicate UI code but keeps each UI free to use its platform's real
  capabilities (e.g. Flet's animated overlays, CTk's native Windows
  dialogs) without a leaky shared abstraction in between.
