---
name: add-course-topic
description: "Use when adding a new topic, chapter, or lesson to the 'Python Learning' course (content/lessons/course_*.yaml), or extending content/quiz/quiz_questions.yaml. Encodes the repeatable schema, curriculum-order rules, and the three places tag vocabulary must stay in sync, so a fresh clone doesn't have to rediscover these the hard way."
---

# Adding a topic to the Python Learning course

The course lives entirely in `content/lessons/course_*.yaml`, grouped by
`Lesson.category` (a "chapter") and `Lesson.topic` (a sub-group within a
chapter). Every topic is exactly 3 items: a concept lesson ("What is X?"),
a coding exercise ("Your Sample Program with X"), and a quiz. This is data,
not code — no UI changes are needed to add content.

## 1. Decide where it goes

- **New topic in an existing chapter** (e.g. another Data Structures topic):
  just add 3 more lessons with a new `topic` value in that `category`.
- **New chapter**: needs `app/engine/categories.py` updates too — see step 5.

Chapters and topics are **never locked relative to each other** — only the
3 items *within one topic* gate in order. Don't try to make topics or
chapters depend on each other.

## 2. Level numbering (curriculum order)

`LessonEngine._load()` sorts ALL lessons globally by `level` (int), and
`categories()` derives chapter order from first appearance in that sorted
sequence. `course_capstone` must always have the highest `level` range in
the course, since it's meant to be the final chapter.

- Adding to an existing chapter/topic at the end: just continue past the
  current max `level` used by that chapter.
- Inserting a new chapter before Capstone: renumber Capstone's 3 lessons to
  free up a `level` range above your new chapter and below wherever Capstone
  needs to end up (grep `^level: 9` across `content/lessons/` to see current
  usage before picking numbers — don't guess).

## 3. The lesson YAML schema

Copy an existing file (e.g. `content/lessons/course_variables_numbers_01_what_is_a_number.yaml`)
as your template. Required fields: `id`, `title`, `level`, `objective`,
`explanation`, `example_code`, `starter_code`, `challenge`, `expected_output`,
`hints`, `reward_stars`, `badge: null`, `category`, `category_level`,
`topic`, `concept_tags`. Quiz items (3rd item of every topic) additionally
set `is_quiz: true` and leave `example_code`/`starter_code`/`expected_output`
empty, `hints: []`.

Filename convention: `course_<chapter>_<topic_slug>_<01|02|03>_<short_desc>.yaml`.
`id` convention: `course_<chapter>_<topic_slug>_<1|2|3>` (matches the
trailing digit to `category_level`'s position within the topic).

`starter_code` is normally identical to `example_code` — the challenge asks
the child to edit one specific value, and `expected_output` reflects the
*edited* result, not the unedited starter.

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
- `COURSE_CATEGORIES` — insert the new category slug in curriculum order.

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
  non-quiz lesson, containing the *challenge-solved* code (not the starter).
  A test asserts every course code lesson has an entry here, that unedited
  starter code does NOT satisfy the challenge, and that the solution DOES
  produce `expected_output` exactly.
- `tests/test_course_status.py` — if you added a new chapter, add a
  `test_<chapter>_chapter_shows_0_of_N` test mirroring the existing ones.

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
