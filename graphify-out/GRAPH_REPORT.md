# Graph Report - KidsLearningApp  (2026-08-15)

## Corpus Check
- 222 files · ~55,685 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1256 nodes · 2136 edges · 85 communities (74 shown, 11 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 225 edges (avg confidence: 0.68)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 82
- Community 83

## God Nodes (most connected - your core abstractions)
1. `LessonEngine` - 56 edges
2. `run_code()` - 41 edges
3. `AppState` - 41 edges
4. `validate_output()` - 39 edges
5. `run_code()` - 35 edges
6. `LessonScreen` - 33 edges
7. `_LessonController` - 33 edges
8. `ProgressStore` - 29 edges
9. `_ParentController` - 28 edges
10. `GameCanvas` - 25 edges

## Surprising Connections (you probably didn't know these)
- `"Today's Mission" panel (guided single-lesson prompt with progress bar and Continue button)` --conceptually_related_to--> `LessonEngine.resolve_current()`  [AMBIGUOUS]
  docs/app-screenshots/welcome-screen.png → CLAUDE.md
- `Offline Data Storage` --references--> `resolve_platform_data_dir()`  [EXTRACTED]
  CLAUDE.md → app/config/platform_paths.py
- `get_data_dir()` --references--> `app-data/ Legacy Dev-Convenience Folder`  [EXTRACTED]
  app/config/settings.py → CLAUDE.md
- `Offline Data Storage` --references--> `get_data_dir()`  [EXTRACTED]
  CLAUDE.md → app/config/settings.py
- `LessonEngine._load()` --references--> `Lesson`  [EXTRACTED]
  CLAUDE.md → app/engine/lesson.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Badge-awarding lessons within the basics progression** — content_lessons_lesson_01_meet_python_lesson, content_lessons_lesson_06_division_lesson, content_lessons_lesson_09_input_lesson [EXTRACTED 1.00]
- **Today's Mission guided sequence (lessons 1-10)** — content_lessons_lesson_01_meet_python_lesson, content_lessons_lesson_02_numbers_lesson, content_lessons_lesson_03_addition_lesson, content_lessons_lesson_04_subtraction_lesson, content_lessons_lesson_05_multiplication_lesson, content_lessons_lesson_06_division_lesson, content_lessons_lesson_07_variables_lesson, content_lessons_lesson_08_strings_lesson, content_lessons_lesson_09_input_lesson, content_lessons_lesson_10_if_else_lesson [EXTRACTED 1.00]
- **Lesson 64 explicitly combines round, max/min, and abs learned in prior number lessons** — content_lessons_lesson_64_numbers_level20, content_lessons_lesson_56_numbers_level12_max_function, content_lessons_lesson_61_numbers_level17_abs_decimal [EXTRACTED 1.00]
- **Sandbox Engines Sharing the AST Safety Check** — claude_subprocess_engine, claude_inprocess_engine, app_sandbox_safety, app_games_graphical_runner [EXTRACTED 1.00]
- **Shared Non-UI Layers Across CTk and Flet** — claude_ctk_ui_codebase, claude_flet_ui_codebase, app_engine_lesson_engine, app_progress_store, app_config_settings [EXTRACTED 1.00]
- **Snake Project: incremental build across lessons 16-18** — content_lessons_lesson_16_snake_window_lesson, content_lessons_lesson_17_snake_draw_lesson, content_lessons_lesson_18_snake_move_lesson [EXTRACTED 1.00]
- **Comparing the result of a computed expression (>, ==) across numbers and addition lessons** — content_lessons_lesson_63_numbers_level19_expression_comparison, content_lessons_lesson_70_addition_level9_addition_comparison, content_lessons_lesson_76_addition_level15_addition_equality_check [INFERRED 0.75]
- **Comparison operators cluster across variables and numbers categories** — content_lessons_lesson_39_variables_level12, content_lessons_lesson_53_numbers_level9, content_lessons_lesson_54_numbers_level10, content_lessons_lesson_55_numbers_level11 [INFERRED 0.75]
- **Parenthesized-arithmetic-then-power pattern across operations** — content_lessons_lesson_79_addition_level18, content_lessons_lesson_79_addition_level18_power_of_sum, content_lessons_lesson_96_subtraction_level18, content_lessons_lesson_96_subtraction_level18_power_of_difference [INFERRED 0.75]
- **Chained addition of multiple numbers, escalating in count and size** — content_lessons_lesson_67_addition_level6_chained_addition, content_lessons_lesson_71_addition_level10_chained_addition_five, content_lessons_lesson_75_addition_level14_chained_addition_large [INFERRED 0.80]
- **Floor division (//) and modulo (%) shared operator pattern** — content_lessons_lesson_122_division_level10_floor_division, content_lessons_lesson_123_division_level11_modulo, content_lessons_lesson_124_division_level12, content_lessons_lesson_131_division_level19 [INFERRED 0.80]
- **Mini-games introducing randomness and graphical execution (lessons 14-16)** — content_lessons_lesson_14_guess_the_number_lesson, content_lessons_lesson_15_rock_paper_scissors_lesson, content_lessons_lesson_16_snake_window_lesson [INFERRED 0.80]
- **Addition levels 17-20 progression (chunk tail)** — content_lessons_lesson_78_addition_level17, content_lessons_lesson_79_addition_level18, content_lessons_lesson_80_addition_level19, content_lessons_lesson_81_addition_level20 [INFERRED 0.85]
- **Division category_level 4-19 progression** — content_lessons_lesson_116_division_level4, content_lessons_lesson_117_division_level5, content_lessons_lesson_118_division_level6, content_lessons_lesson_119_division_level7, content_lessons_lesson_120_division_level8, content_lessons_lesson_121_division_level9, content_lessons_lesson_122_division_level10, content_lessons_lesson_123_division_level11, content_lessons_lesson_124_division_level12, content_lessons_lesson_125_division_level13, content_lessons_lesson_126_division_level14, content_lessons_lesson_127_division_level15, content_lessons_lesson_128_division_level16, content_lessons_lesson_129_division_level17, content_lessons_lesson_130_division_level18, content_lessons_lesson_131_division_level19 [INFERRED 0.85]
- **Main-Path Lesson Badge System** — readme_badge_math_master, readme_badge_python_explorer, readme_badge_loop_wizard, readme_badge_game_creator, readme_main_path_lessons_1_13 [INFERRED 0.85]
- **Multiplication category_level 17-20 progression** — content_lessons_lesson_112_multiplication_level17, content_lessons_lesson_113_multiplication_level18, content_lessons_lesson_114_multiplication_level19, content_lessons_lesson_115_multiplication_level20 [INFERRED 0.85]
- **Numbers level 4-11 progression arc** — content_lessons_lesson_48_numbers_level4, content_lessons_lesson_49_numbers_level5, content_lessons_lesson_50_numbers_level6, content_lessons_lesson_51_numbers_level7, content_lessons_lesson_52_numbers_level8, content_lessons_lesson_53_numbers_level9, content_lessons_lesson_54_numbers_level10, content_lessons_lesson_55_numbers_level11 [INFERRED 0.85]
- **Variables level 7-20 progression arc** — content_lessons_lesson_34_variables_level7, content_lessons_lesson_35_variables_level8, content_lessons_lesson_36_variables_level9, content_lessons_lesson_37_variables_level10, content_lessons_lesson_38_variables_level11, content_lessons_lesson_39_variables_level12, content_lessons_lesson_40_variables_level13, content_lessons_lesson_41_variables_level14, content_lessons_lesson_42_variables_level15, content_lessons_lesson_43_variables_level16, content_lessons_lesson_44_variables_level17, content_lessons_lesson_45_variables_level18, content_lessons_lesson_46_variables_level19, content_lessons_lesson_47_variables_level20 [INFERRED 0.85]
- **Variables bonus progression arc (levels 2-6)** — content_lessons_lesson_29_variables_level2_lesson, content_lessons_lesson_30_variables_level3_lesson, content_lessons_lesson_31_variables_level4_lesson, content_lessons_lesson_32_variables_level5_lesson, content_lessons_lesson_33_variables_level6_lesson [INFERRED 0.85]
- **Multiplication category_level progression (levels 1, 5-16)** — content_lessons_lesson_05_multiplication_lesson, content_lessons_lesson_100_multiplication_level5_lesson, content_lessons_lesson_101_multiplication_level6_lesson, content_lessons_lesson_102_multiplication_level7_lesson, content_lessons_lesson_103_multiplication_level8_lesson, content_lessons_lesson_104_multiplication_level9_lesson, content_lessons_lesson_105_multiplication_level10_lesson, content_lessons_lesson_106_multiplication_level11_lesson, content_lessons_lesson_107_multiplication_level12_lesson, content_lessons_lesson_108_multiplication_level13_lesson, content_lessons_lesson_109_multiplication_level14_lesson, content_lessons_lesson_110_multiplication_level15_lesson, content_lessons_lesson_111_multiplication_level16_lesson [INFERRED 0.90]
- **Subtraction levels 4-20 full bonus progression** — content_lessons_lesson_82_subtraction_level4, content_lessons_lesson_83_subtraction_level5, content_lessons_lesson_84_subtraction_level6, content_lessons_lesson_85_subtraction_level7, content_lessons_lesson_86_subtraction_level8, content_lessons_lesson_87_subtraction_level9, content_lessons_lesson_88_subtraction_level10, content_lessons_lesson_89_subtraction_level11, content_lessons_lesson_90_subtraction_level12, content_lessons_lesson_91_subtraction_level13, content_lessons_lesson_92_subtraction_level14, content_lessons_lesson_93_subtraction_level15, content_lessons_lesson_94_subtraction_level16, content_lessons_lesson_95_subtraction_level17, content_lessons_lesson_96_subtraction_level18, content_lessons_lesson_97_subtraction_level19, content_lessons_lesson_98_subtraction_level20 [INFERRED 0.90]

## Communities (85 total, 11 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (57): Any, The restricted builtin set shared by the subprocess worker and the in-process…, _build_globals(), ExecutionResult, _make_input(), Executes a child's Python code safely, in-process. Replaces the subprocess-…, Mirrors how a real stdin pipe behaves: a trailing newline marks the end of the…, Lets the UI cancel a run that's in progress (e.g. an infinite loop). Python… (+49 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (20): extract_error_line_number(), _last_exception_type(), Translates raw Python tracebacks into kid-friendly messages. Raw text stays…, translate_error(), apply_highlighting(), CodeEditor, configure_highlight_tags(), make_read_only_code_block() (+12 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (13): _LessonController, Control, ExecutionResult, RunHandle, View, KeyboardEvent, controller(), FakePage (+5 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (43): open_parent_area(), _open_parent_window(), _open_pin_prompt(), PIN-gated parent area: progress summary and basic controls. Full detail…, _find_enclosing_scrollable_canvas(), install_fast_mousewheel_scrolling(), _on_wheel(), Reliable, fast mouse-wheel scrolling for CTkScrollableFrame, installed ONCE for… (+35 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (32): GameCanvas, Canvas, The Flet port of the safe drawing surface injected into graphical lessons as…, Runs callback once, ms milliseconds from now -- call it again inside callback…, Runs callback whenever the given key is pressed. key is one of: Up, Down, Left,…, Called by the on-screen D-pad / physical keyboard handler in…, Stops any still-scheduled after() callbacks -- called when the child navigates…, Draws a filled rectangle and returns an id you can move or delete later. (+24 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (47): Lesson 112: Multiplication Level 17, Multiplication (chained decimal multiplication), Lesson 113: Multiplication Level 18, Exponentiation with operator precedence (** after *), Multiplication (combined with exponent), Lesson 114: Multiplication Level 19, Multiplication (chained five-number product), Lesson 115: Multiplication Level 20 (+39 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (46): addition category (bonus progression), numbers category (bonus progression), Lesson 56: Numbers Level 12 - max(), max() function, Lesson 57: Numbers Level 13 - min(), min() function, Lesson 58: Numbers Level 14 - Exponentiation, Exponentiation (**) (+38 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (46): Lesson 34: Variables Level 7 - minus-equals shortcut, -= augmented subtraction operator, Variables (category), Lesson 35: Variables Level 8 - times-equals shortcut, *= augmented multiplication operator, Lesson 36: Variables Level 9 - storing text in a variable, Storing text (string) in a variable, Lesson 37: Variables Level 10 - printing two variables together (+38 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (22): CategoryMapFrame, Category browser: pick a topic (Numbers, Addition, ...) to see its levels., contrasting_text_color(), darken(), _hex_to_rgb(), lighten(), Small color-math helpers for category color-coding (Scratch-style solid,…, Picks white or near-black text depending on which reads better on this… (+14 more)

### Community 9 - "Community 9"
Cohesion: 0.06
Nodes (41): Lesson 13: Lists, list indexing (0-based), lists, if/else conditionals, games (category), Lesson 14: Guess the Number, random numbers (random.randint), variables (+33 more)

### Community 10 - "Community 10"
Cohesion: 0.10
Nodes (23): LessonEngine, LessonEngine._load(), Path, A level is unlocked once every earlier level in its category is complete., The first not-yet-completed, unlocked lesson in a category, for a "Play" button…, The next lesson in the guided main-path chain, or None at the end. Follows…, The lesson a child should land on next for "Today's Mission". Trusts a stored…, Category slugs in curriculum order (by each category's first appearance). (+15 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (18): _ParentController, Control, View, FakePage, fixture, Exercises _ParentController's real PIN-gate, summary, activity, and reset logic…, state(), test_activity_log_shows_friendly_labels_with_icons() (+10 more)

### Community 12 - "Community 12"
Cohesion: 0.07
Nodes (9): _now(), ProfileSummary, ProgressStore, Path, Returns True if newly awarded, False if already had it., Owns the SQLite connection for the child's progress data., Row, fixture (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (21): check_code_safety(), While, Raises SafetyViolation if the code uses something the sandbox blocks. Syntax…, SafetyViolation, _SafetyVisitor, Attribute, Exception, Import (+13 more)

### Community 14 - "Community 14"
Cohesion: 0.16
Nodes (18): Exercise validation: checks behavior/output, not exact code formatting., Compares output, optionally substituting what the child typed into a template.…, validate_output(), Output Validation, test_lesson_09_content_is_input_shaped(), test_lesson_09_fails_validation_against_a_different_typed_name(), test_lesson_09_starter_code_passes_for_any_typed_name(), End-to-end simulation of what the lesson screen does on a successful run,… (+10 more)

### Community 15 - "Community 15"
Cohesion: 0.10
Nodes (18): LessonEngine.is_unlocked(), LessonEngine.resolve_current(), Category Browser, Python Adventure (App), Today's Mission (Guided Sequence), Two Parallel Ways to Reach a Lesson, Completed Missions sidebar (color-coded lesson cards with star ratings), Midnight Dark theme styling (dark purple background, bright accent colors) (+10 more)

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (8): GameCanvas, Canvas, Draws a filled rectangle and returns an id you can move or delete later., Moves a shape by dx, dy pixels from where it currently is., Moves a shape to an exact x, y position, keeping its size., Runs callback once, ms milliseconds from now -- call it again inside callback…, Runs callback whenever the given key is pressed. key is one of: Up, Down, Left,…, Toplevel

### Community 17 - "Community 17"
Cohesion: 0.18
Nodes (15): Lets the UI cancel a run that's in progress (e.g. an infinite loop)., run_code(), RunHandle, Popen, test_blocked_dangerous_call_never_executes(), test_blocked_import_never_executes(), test_cancel_stops_a_running_process(), test_disallowed_module_is_blocked_even_though_random_is_allowed() (+7 more)

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (9): _hash_pin(), Settings, test_default_settings_are_not_setup_complete(), test_first_time_user_defaults_to_midnight_dark_theme(), test_load_settings_corrupt_file_returns_defaults(), test_load_settings_missing_file_returns_defaults(), test_parent_pin_round_trip(), test_parent_pin_salted_differently_each_time() (+1 more)

### Community 19 - "Community 19"
Cohesion: 0.11
Nodes (4): engine(), fixture, Tests for category grouping, unlocking, and the main-path/bonus-level split., test_get_category_meta_falls_back_for_unknown_category()

### Community 20 - "Community 20"
Cohesion: 0.21
Nodes (13): Shared app state for the Flet UI: settings, progress store, lesson engine, and…, build_settings_view(), _build_theme_card(), _build_theme_option(), Control, Page, ThemePreset, View (+5 more)

### Community 21 - "Community 21"
Cohesion: 0.25
Nodes (13): get_data_dir(), get_db_path(), get_repo_root(), get_settings_path(), is_first_run(), load_settings(), _migrate_from_repo_local_dir(), Path (+5 more)

### Community 22 - "Community 22"
Cohesion: 0.18
Nodes (11): CATEGORY_META, CategoryMeta, DEFAULT_META, get_category_meta(), Display metadata (title, icon, color) for lesson categories, used by the…, build_category_levels_view(), Page, View (+3 more)

### Community 23 - "Community 23"
Cohesion: 0.17
Nodes (8): AppState, ThemePreset, build_lesson_view(), Page, build_parent_view(), Page, PIN-gated parent area: progress summary and basic controls. Ported from…, app/parent — PIN-Gated Parent Area (CTk)

### Community 24 - "Community 24"
Cohesion: 0.16
Nodes (11): The Lesson data model. Lessons are content, not code — see…, ExecutionResult, Executes a child's Python code safely: static check, then an isolated…, The Explain -> Demonstrate -> Try It -> Run -> Result -> Challenge -> Reward…, lesson_01_meet_python.yaml - Meet Python introductory lesson content, learn-python-1.png (Lesson explanation screenshot), Screenshot: 'Meet Python' lesson explanation screen, Midnight Dark theme visual style (purple-on-dark UI) (+3 more)

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (12): main(), Page, Root Flet application: route-based navigation between full-screen views. The…, build_category_map_view(), Page, View, build/ Directory (Flet Packaging Output), Flet UI Codebase (Re-platform) (+4 more)

### Community 27 - "Community 27"
Cohesion: 0.18
Nodes (11): Loads lesson content from YAML files, kept separate from application code.…, tests/ Pytest Suite, pytest>=8.0.0 dependency, pyyaml>=6.0 dependency, engine(), fixture, parametrize, Content checks for the bonus practice levels (numbers/addition/subtraction/… (+3 more)

### Community 28 - "Community 28"
Cohesion: 0.22
Nodes (11): ALLOWED_MODULES, Static (AST-based) safety check, run before any child code is executed. This is…, build_safe_globals(), main(), Runs in its own subprocess with a restricted builtin set. Never imported by the…, _restricted_import(), In-Process Sandbox Engine, Two Sandbox Engines, Converging to One (+3 more)

### Community 29 - "Community 29"
Cohesion: 0.19
Nodes (11): apply_window_icon(), ensure_windows_app_id(), load_icon_image(), make_ctk_icon(), Shared image assets -- the app icon (window/taskbar + in-UI)., A CTkImage for embedding the app icon inside a widget (e.g. CTkLabel)., Registers a distinct AppUserModelID so Windows' taskbar treats this as its own…, Sets both the title-bar icon (iconphoto, works everywhere) and the native .ico… (+3 more)

### Community 30 - "Community 30"
Cohesion: 0.27
Nodes (11): run_graphical_code(), GameCanvas, game_canvas(), fixture, test_blocked_import_never_executes(), test_drawing_and_moving_via_the_game_object(), test_random_module_is_usable_in_graphical_lessons(), test_runtime_error_is_captured_not_raised() (+3 more)

### Community 31 - "Community 31"
Cohesion: 0.21
Nodes (9): SQLite-backed progress, gamification, and activity tracking for the single…, Root application window: owns navigation between full-screen frames., run_app(), CustomTkinter (CTk) UI Codebase, Offline Data Storage, Entry point for Python Adventure., customtkinter>=5.2.2 dependency, run.bat launcher script (+1 more)

### Community 32 - "Community 32"
Cohesion: 0.23
Nodes (7): build_setup_wizard_view(), Control, Page, ThemePreset, View, _SetupWizard, Column

### Community 33 - "Community 33"
Cohesion: 0.17
Nodes (12): basics (category), first_program badge, Lesson 1: Meet Python, print() function, Lesson 2: Numbers, numbers (category/concept), addition (category/concept), Lesson 3: Addition (+4 more)

### Community 35 - "Community 35"
Cohesion: 0.20
Nodes (10): engine(), game_canvas(), fixture, parametrize, Content + behavior checks for the first Snake project steps (16-18): each…, test_lesson_is_marked_graphical(), test_starter_code_runs_cleanly_against_a_real_canvas(), test_step_16_sets_title_and_background() (+2 more)

### Community 36 - "Community 36"
Cohesion: 0.27
Nodes (9): Path, Resolves the real, writable directory this app's data lives in. Windows and…, Returns the OS-appropriate writable data directory, creating it if it doesn't…, resolve_platform_data_dir(), test_falls_back_to_home_dir_if_appdata_unset_on_windows(), test_flet_app_storage_data_wins_even_on_windows(), test_uses_appdata_pythonadventure_on_windows(), test_uses_flet_app_storage_data_env_var_when_set() (+1 more)

### Community 37 - "Community 37"
Cohesion: 0.18
Nodes (11): Lesson 91: Subtraction Level 13, int() string-to-number conversion before subtracting, Subtraction (category), Lesson 92: Subtraction Level 14, Chained subtraction (five numbers from a big total), Subtraction (category), Lesson 93: Subtraction Level 15, Equality (==) check of a subtraction result (+3 more)

### Community 38 - "Community 38"
Cohesion: 0.24
Nodes (7): The safe drawing surface injected into graphical lessons as `game`. This is NOT…, Owns the live CTkToplevel + Canvas that a graphical lesson's code draws into., GraphicalExecutionResult, Runs a graphical lesson's code in-process against a live GameCanvas. Unlike…, _restricted_import(), Third Execution Path for Graphical (Snake) Lessons, Lessons 16-18 (Snake Project Steps 1-3)

### Community 39 - "Community 39"
Cohesion: 0.42
Nodes (9): build_dashboard_view(), _build_header(), _build_mission_card(), _build_missions_sidebar(), Control, Page, View, Main screen: greets the child, shows level/progress, starts today's lesson, and… (+1 more)

### Community 40 - "Community 40"
Cohesion: 0.22
Nodes (10): comparison operators (>), division (category), Lesson 132: Division Level 20, rounding (round()), division (category), division operator (/), Lesson 27: Division Level 2, division (category) (+2 more)

### Community 41 - "Community 41"
Cohesion: 0.20
Nodes (10): Lesson 95: Subtraction Level 17, Chained decimal subtraction (three numbers), Subtraction (category), Lesson 96: Subtraction Level 18, Subtraction (category), Lesson 97: Subtraction Level 19, Chained subtraction (five numbers from a big total), Subtraction (category) (+2 more)

### Community 42 - "Community 42"
Cohesion: 0.27
Nodes (9): engine(), fixture, parametrize, Content checks for the extended bonus practice levels added across…, test_bonus_level_is_marked_correctly(), test_category_has_a_full_1_to_20_level_progression(), test_every_new_lesson_has_a_unique_level_and_id(), test_intended_solution_satisfies_the_challenge() (+1 more)

### Community 43 - "Community 43"
Cohesion: 0.22
Nodes (6): engine(), fixture, parametrize, Content + behavior checks for lessons 7-13 (variables through lists). Same…, test_intended_solution_satisfies_the_challenge(), test_unedited_starter_code_does_not_satisfy_the_challenge()

### Community 44 - "Community 44"
Cohesion: 0.20
Nodes (7): engine(), fixture, Behavior checks for the randomized mini-games (14-15): the starter code is…, Sanity check on the game logic itself, independent of the sandbox: rock/rock is…, test_guess_the_number_always_produces_a_valid_outcome(), test_rock_paper_scissors_always_produces_a_valid_outcome(), test_rock_paper_scissors_never_produces_a_losing_outcome_for_valid_play()

### Community 45 - "Community 45"
Cohesion: 0.28
Nodes (7): make_code_editor(), make_read_only_code_block(), Control, A child-friendly code editor -- Phase 5 MVP. A plain monospace multiline…, A non-editable, monospace code block for showing examples., The Explain -> Demonstrate -> Try It -> Run -> Result -> Reward lesson flow.…, TextField

### Community 47 - "Community 47"
Cohesion: 0.25
Nodes (6): engine(), fixture, parametrize, Content + behavior checks for the arithmetic lessons (2-6): each challenge must…, test_intended_solution_satisfies_the_challenge(), test_unedited_starter_code_does_not_satisfy_the_challenge()

### Community 48 - "Community 48"
Cohesion: 0.25
Nodes (8): Lesson 80: Addition Level 19, Addition (category), Six-number chained addition, Lesson 81: Addition Level 20, Addition (category), Combined round() and comparison capstone, Chained subtraction (four numbers), Combined round() and comparison capstone

### Community 49 - "Community 49"
Cohesion: 0.29
Nodes (7): division (category/concept, float .0 results), Lesson 6: Division, math_master badge, Lesson 7: Variables, variables (category/concept), Lesson 8: Strings, strings (category/concept)

### Community 50 - "Community 50"
Cohesion: 0.29
Nodes (7): Lesson 78: Addition Level 17, Addition (category), Chained decimal addition, Lesson 79: Addition Level 18, Addition (category), Power of a sum ((a+b)**n), Power of a difference ((a-b)**n)

### Community 52 - "Community 52"
Cohesion: 0.33
Nodes (6): input() (category/concept), Lesson 9: Ask a Question, python_explorer badge, string concatenation with +, conditionals (if/else), Lesson 10: Decisions

### Community 53 - "Community 53"
Cohesion: 0.47
Nodes (6): Lesson 100: Multiplication Level 5, multiplication (category), multiplying by a negative number, chaining multiple * operators, Lesson 101: Multiplication Level 6, multiplication (category)

### Community 54 - "Community 54"
Cohesion: 0.47
Nodes (6): Lesson 102: Multiplication Level 7, multiplication (category), round() function, abs() function, Lesson 103: Multiplication Level 8, multiplication (category)

### Community 55 - "Community 55"
Cohesion: 0.47
Nodes (6): comparison operator (>), Lesson 104: Multiplication Level 9, multiplication (category), Lesson 105: Multiplication Level 10, multiplication (category), multiplying by zero

### Community 56 - "Community 56"
Cohesion: 0.47
Nodes (6): multiplying two decimals, Lesson 106: Multiplication Level 11, multiplication (category), Lesson 107: Multiplication Level 12, max() function, multiplication (category)

### Community 57 - "Community 57"
Cohesion: 0.47
Nodes (6): int() type conversion, Lesson 108: Multiplication Level 13, multiplication (category), chaining five * operators, Lesson 109: Multiplication Level 14, multiplication (category)

### Community 58 - "Community 58"
Cohesion: 0.47
Nodes (6): equality operator (==), Lesson 110: Multiplication Level 15, multiplication (category), Lesson 111: Multiplication Level 16, multiplication (category), negative times negative = positive

### Community 59 - "Community 59"
Cohesion: 0.33
Nodes (6): Lesson 19: Numbers Level 2, numbers (category), printing numbers, Lesson 20: Numbers Level 3, numbers (category), printing numbers

### Community 60 - "Community 60"
Cohesion: 0.33
Nodes (6): addition (category), addition operator (+), Lesson 21: Addition Level 2, addition (category), chained addition (a + b + c), Lesson 22: Addition Level 3

### Community 61 - "Community 61"
Cohesion: 0.33
Nodes (6): Lesson 23: Subtraction Level 2, subtraction (category), subtraction operator (-), chained subtraction (a - b - c), Lesson 24: Subtraction Level 3, subtraction (category)

### Community 62 - "Community 62"
Cohesion: 0.33
Nodes (6): Lesson 25: Multiplication Level 2, multiplication (category), multiplication operator (*), chained multiplication (a * b * c), Lesson 26: Multiplication Level 3, multiplication (category)

### Community 63 - "Community 63"
Cohesion: 0.33
Nodes (6): Lesson 82: Subtraction Level 4, Decimal subtraction, Subtraction (category), Lesson 99: Multiplication Level 4, Decimal-by-whole-number multiplication, Multiplication (category)

### Community 64 - "Community 64"
Cohesion: 0.33
Nodes (6): Lesson 83: Subtraction Level 5, Subtracting a negative number (flips to addition), Subtraction (category), Lesson 84: Subtraction Level 6, Subtraction (category), Subtracting a negative from a negative (double negative)

### Community 65 - "Community 65"
Cohesion: 0.33
Nodes (6): Lesson 85: Subtraction Level 7, round() applied to a subtraction result, Subtraction (category), Lesson 86: Subtraction Level 8, abs() applied to a subtraction result, Subtraction (category)

### Community 66 - "Community 66"
Cohesion: 0.33
Nodes (6): Lesson 87: Subtraction Level 9, Greater-than comparison of a subtraction result, Subtraction (category), Lesson 88: Subtraction Level 10, Repeated subtraction of the same number, Subtraction (category)

### Community 67 - "Community 67"
Cohesion: 0.33
Nodes (6): Lesson 89: Subtraction Level 11, Decimal subtraction with differing decimal places, Subtraction (category), Lesson 90: Subtraction Level 12, min() applied to two subtraction results, Subtraction (category)

### Community 69 - "Community 69"
Cohesion: 0.50
Nodes (5): Lesson 11: Loops, Loop Wizard Badge, Loops (for i in range()), Lesson 12: Functions, Functions (def and call)

## Ambiguous Edges - Review These
- `LessonEngine.resolve_current()` → `"Today's Mission" panel (guided single-lesson prompt with progress bar and Continue button)`  [AMBIGUOUS]
  docs/app-screenshots/welcome-screen.png · relation: conceptually_related_to

## Knowledge Gaps
- **142 isolated node(s):** `python-adventure`, `run.sh script`, `Output Validation`, `build/ Directory (Flet Packaging Output)`, `app-data/ Legacy Dev-Convenience Folder` (+137 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `LessonEngine.resolve_current()` and `"Today's Mission" panel (guided single-lesson prompt with progress bar and Continue button)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `AppState` connect `Community 23` to `Community 32`, `Community 2`, `Community 39`, `Community 10`, `Community 11`, `Community 12`, `Community 45`, `Community 18`, `Community 20`, `Community 21`, `Community 22`, `Community 26`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `LessonEngine` connect `Community 10` to `Community 35`, `Community 42`, `Community 43`, `Community 44`, `Community 14`, `Community 47`, `Community 19`, `Community 20`, `Community 21`, `Community 23`, `Community 25`, `Community 27`, `Community 31`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `ProgressStore` connect `Community 12` to `Community 14`, `Community 20`, `Community 21`, `Community 23`, `Community 25`, `Community 31`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `LessonEngine` (e.g. with `Lesson` and `AppState`) actually correct?**
  _`LessonEngine` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `AppState` (e.g. with `Settings` and `LessonEngine`) actually correct?**
  _`AppState` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `run_code()` (e.g. with `SafetyViolation` and `Watchdog`) actually correct?**
  _`run_code()` has 4 INFERRED edges - model-reasoned connections that need verification._