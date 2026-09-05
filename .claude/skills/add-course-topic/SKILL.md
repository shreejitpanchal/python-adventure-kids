---
name: add-course-topic
description: "Use when adding a new topic, chapter, or standalone course to the Learning Hub's course system (content/lessons/*.yaml with a category in a registered CourseSpec), or extending content/quiz/quiz_questions.yaml. Encodes the repeatable schema, curriculum-order rules, and the three places tag vocabulary must stay in sync, so a fresh clone doesn't have to rediscover these the hard way."
---

# Adding a topic to a Learning Hub course

There are two standalone courses today — "🎓 Python Learning" and "🤖 AI &
Machine Learning" — sharing one engine and one set of UI screens via
`app/engine/courses.py`'s `CourseSpec` (`id`/`title`/`categories`/`badge_id`)
and `ALL_COURSES` registry, rather than each course duplicating
`course_status.py`'s functions or the 6 course-UI screen files (3 CTk + 3
Flet). Every course is grouped by `Lesson.category` (a "chapter") and
`Lesson.topic` (a sub-group within a chapter). Every topic is exactly 3
items: a concept lesson ("What is X?"), a coding exercise ("Your Sample
Program with X"), and a quiz. This is data, not code — no UI changes are
needed to add content to an *existing* course.

## 1. Decide where it goes

- **New topic in an existing chapter** (e.g. another Data Structures topic):
  just add 3 more lessons with a new `topic` value in that `category`.
- **New chapter in an existing course**: needs `app/engine/categories.py`
  updates too — see step 5.
- **A brand-new, third standalone course**: add a new `CourseSpec` to
  `app/engine/courses.py`'s `ALL_COURSES` (its own `categories` list and
  `badge_id`) — `compute_course_status()`/`maybe_award_course_badge()` and
  every course-UI screen file already take a `course`/`categories` param, so
  they work for a third course with zero further engine/screen changes. You
  still need: a new Hub card (`learning_hub.py`/`_flet.py`), new
  `show_course_map`/`show_course_chapter`/`show_course_quiz` call sites or
  route-dispatch branches (mirror the existing `/course...` vs
  `/ai-course...` prefixes in `app_window_flet.py`), and a new
  `app/engine/badges.py` entry.

Chapters and topics are **never locked relative to each other** — only the
3 items *within one topic* gate in order. Don't try to make topics or
chapters depend on each other. **Never let two courses share a category** —
`find_course_for_category()` assumes each category belongs to at most one
course; `tests/test_ai_course_status.py::test_ai_and_python_courses_are_independent_categories`
guards this.

## 2. Level numbering (curriculum order)

`LessonEngine._load()` sorts ALL lessons globally by `level` (int), but a
course's own **chapter order comes from its `CourseSpec.categories` list
order**, not from `level` — `compute_course_status()` iterates that list
directly. `level` only needs to avoid colliding with any other lesson's
`level` app-wide; it does not need to be contiguous with an existing
course's range. The Python Learning course occupies roughly 0-995; the AI &
Machine Learning course starts fresh at 2001 — grep `^level:` across
`content/lessons/` to confirm your chosen range is free before picking
numbers, rather than assuming.

Within the *Python Learning* course specifically, `course_capstone` must
stay the highest `level` range, since `LessonEngine.categories()` (used
elsewhere for global ordering) still sorts by first-appearance-by-level —
inserting a new chapter there means renumbering Capstone up, not just
picking free numbers.

## 3. The lesson YAML schema

Copy an existing file (e.g. `content/lessons/course_variables_numbers_01_what_is_a_number.yaml`
for the Python course, or `content/lessons/ai_tools_whatismcp_01_what_is_mcp.yaml`
for the AI course) as your template. Required fields: `id`, `title`,
`level`, `objective`, `explanation`, `example_code`, `starter_code`,
`challenge`, `expected_output`, `hints`, `reward_stars`, `badge: null`,
`category`, `category_level`, `topic`, `concept_tags`. Quiz items (3rd item
of every topic) additionally set `is_quiz: true` and leave
`example_code`/`starter_code`/`expected_output` empty, `hints: []`.

Filename/`id` convention: match your **category's actual name**, not a
reflexive `course_` prefix — e.g. `course_variables_numbers_01_...yaml` /
`id: course_variables_numbers_1` for the `course_variables` category, but
`ai_tools_whatismcp_01_...yaml` / `id: ai_tools_whatismcp_1` for the
`ai_tools` category (which has no `course_` prefix). Pattern:
`<category>_<topic_slug>_<01|02|03>_<short_desc>.yaml`, id
`<category>_<topic_slug>_<1|2|3>` (trailing digit matches `category_level`'s
position within the topic).

`starter_code` is normally identical to `example_code` — the challenge asks
the child to edit one specific value, and `expected_output` reflects the
*edited* result, not the unedited starter.

**Two gotchas specific to what code you put in `example_code`:**
- **No `input()` in course lessons.** `tests/test_course_lessons.py`'s
  `LESSON_SOLUTIONS` harness runs `run_code(lesson.starter_code)` with **no
  stdin fed at all** — an `input()` call raises `EOFError` there and fails
  the test immediately. Course lessons must be deterministic (edit a
  variable, rerun) — reserve `input_prompt`/`expected_output_pattern` for
  the flat, non-course `games` category (see `lesson_15_rock_paper_scissors.yaml`),
  which isn't tested this way.
- **No emoji inside `print()`/f-string output.** The sandboxed child
  subprocess's stdout is cp1252 on Windows — printing e.g. `"🤖 ..."` raises
  `UnicodeEncodeError` and fails the lesson. Emoji are fine in `title`/
  `explanation`/`hints` (rendered directly by the UI, never executed), just
  never inside a string a lesson actually `print()`s.

## 4. Concept tags — three places must stay in sync

If you introduce a **new** tag (not already in the vocabulary), it must be
added in all three of these, or tests fail:

1. `app/engine/lesson.py` — the `concept_tags` field's docstring (the fixed
   vocabulary list).
2. `tests/test_concept_tags.py` — the `VOCABULARY` set.
3. `tests/test_quiz_tags.py` — the (separate, must-match) `VOCABULARY` set.

This has bitten past work more than once — the two test files' `VOCABULARY`
sets look like duplicates and are easy to update in only one place.

Every topic's quiz filters `content/quiz/quiz_questions.yaml` by the quiz
lesson's `concept_tags` (`QuizEngine.start_session_for_tags`, count=8, falls
back to the *full* bank if the filtered pool is empty — silently masking a
missing tag rather than erroring). **Before finalizing**, make sure each new
tag actually has ≥8 real questions:

```
.venv\Scripts\python.exe -m pytest tests/test_course_quiz_content.py -q
```

If you need new questions, generate them with a small Python script that
builds a `list[dict]` and appends via `yaml.dump(..., allow_unicode=True,
sort_keys=False, default_flow_style=False)` — never hand-type YAML with
embedded quotes directly into `quiz_questions.yaml`; unescaped inner quotes
have broken parsing before. New ids continue sequentially from the current
max `qNNN`.

## 5. New chapter only: `app/engine/categories.py`

- `CATEGORY_META[<category>]` — display title/icon/color.
- `TOPIC_ICONS[<topic name>]` — one entry per new topic (cosmetic, optional
  but expected).
- Insert the new category slug in curriculum order into the right course's
  list — `COURSE_CATEGORIES` for Python Learning, `AI_COURSE_CATEGORIES`
  for AI & Machine Learning (both consumed via `app/engine/courses.py`'s
  `PYTHON_COURSE`/`AI_ML_COURSE`, so no other file needs the raw list name).

Also update the course chapter-count/lesson-count mentions in `README.md`,
`docs/DEVELOPMENT.md`, and the Learning Hub card subtitle text in
`app/ui/learning_hub.py` and `app/ui/learning_hub_flet.py`.

## 6. Sandbox module allowlist (only if a lesson needs a new stdlib import)

The sandbox only allows explicitly listed modules —
`app/sandbox/safety.py`'s `ALLOWED_MODULES` (AST-level check) **and**
`app/sandbox/worker.py`'s `ALLOWED_MODULES` (subprocess-level restricted
`__import__`) must both be updated, kept identical. Only add
pure-computation or clock-reading modules with no filesystem/network/
process access. `threading`/`asyncio`/`logging` are deliberately excluded —
real concurrency doesn't compose safely with the sandbox's hard-kill-after-
5s-timeout model; teach those concepts with simulated plain-loop/dict/`zip()`
examples instead (see `course_concurrency`'s lessons for the pattern).

## 7. Test fixtures that need new entries

- `tests/test_course_lessons.py`'s `LESSON_SOLUTIONS` dict — one entry per
  non-quiz lesson (any course), containing the *challenge-solved* code (not
  the starter). `test_every_course_code_lesson_has_a_solution_fixture`
  iterates `app.engine.courses.ALL_COURSES` generically, so adding a new
  course's categories to its `CourseSpec` is picked up automatically — you
  only need to add the new lesson ids' solutions here, not touch the test.
- `tests/test_course_quiz_content.py` — same story: its fixture iterates
  `ALL_COURSES` already, no changes needed for a new topic/chapter in an
  existing course.
- New chapter in an existing course: add a `test_<chapter>_chapter_shows_0_of_N`
  test to `tests/test_course_status.py` (Python course) or
  `tests/test_ai_course_status.py` (AI course), mirroring the existing ones.
- Brand-new third course: add a new sibling file mirroring
  `tests/test_ai_course_status.py` in full (it's a compact, complete
  template — status/badge tests against your new `CourseSpec`), plus sibling
  Flet screen tests mirroring `tests/test_ai_course_map_flet.py`/
  `test_ai_course_chapter_flet.py`/`test_ai_course_quiz_screen_flet.py`.

## 8. Verify before finalizing

Validate every new solution against the **real** sandbox before writing it
into YAML (catches off-by-one/output-format mistakes early, cheaper than a
second editing pass):

```python
from app.sandbox.runner import run_code
result = run_code(your_challenge_solved_code)
print(result.stdout)  # compare against your intended expected_output
```

Then:

```
.venv\Scripts\python.exe -m pytest tests\ -q
.venv\Scripts\python.exe main.py     # quick launch sanity check (Ctrl+C after it opens)
```

Full suite takes ~5 minutes. `/verify` runs both of these for you.
