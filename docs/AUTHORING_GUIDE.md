# Content authoring guide

Everything a child sees — lessons, quiz questions, and the Python Journey
course map itself — is plain YAML data under `content/`, loaded by
`app/engine/`. Adding or changing content never requires touching app
code. This guide covers the two things specific to Python Journey: the
`learning_path.yaml` module format, and the lesson-content fields that
support it (`learning_path_module`, `lesson_type`, `concept_tags`,
`prerequisite_lesson_ids`). For everything else about the base lesson
schema (`category`, `category_level`, `main_path`, `expected_output`,
`graphical`, etc.), see the "How it works" section of the main README.

## Adding a 9th module (or a new lesson to an existing one)

`content/learning_path.yaml` is a flat list under `modules:`:

```yaml
modules:
  - id: python-starter
    title: "Python Starter"
    order: 1
    icon: "🚀"
    description: "Learn how Python talks, counts, and follows instructions."
    required_lesson_ids: [lesson_01, lesson_02, lesson_03, lesson_450]
    checkpoint_lesson_id: lesson_451
    badge_id: module_python_starter
```

- `order` controls both display order and lock/unlock sequencing —
  module *N* is locked until module *N-1* is fully complete (see
  `app/engine/learning_path.py`'s `LearningPathEngine.module_status()`).
  Module 1 (lowest `order`) is always unlocked.
- `required_lesson_ids` is an ordered list — a lesson unlocks once every
  *earlier* id in this same list is completed
  (`LearningPathEngine.is_lesson_unlocked()`), the same "earlier levels
  unlock later ones" idea `LessonEngine.is_unlocked()` already uses for
  the category browser, just keyed by list position instead of an
  integer `category_level`.
- `checkpoint_lesson_id` (optional) is the module's capstone — appended
  to the end of the unlock sequence, shown with a 🏆 trophy marker on the
  course map instead of a plain step number.
- `badge_id` is awarded automatically the moment every required lesson
  plus the checkpoint are completed — see "Module badges" below. Pick an
  id following the `module_<slug>` convention and add a matching entry to
  `BADGE_META` in `app/engine/badges.py` (title/icon/description — purely
  presentational; a badge without an entry there still works, just falls
  back to a generic "Mystery Badge" look).

**Reuse existing content first.** A module's `required_lesson_ids`/
`checkpoint_lesson_id` can point at *any* existing lesson id, regardless
of its `category`/`main_path`/`graphical` fields — referencing a lesson
here never changes those fields or its place in the guided "Today's
Mission" chain or category browser. The shipped 8 modules deliberately
reuse existing content wherever a good fit already exists: 5 of the 8
checkpoints are the last ("capstone") level of an existing 20-level bonus
practice track (e.g. `lesson_358` for Decisions), and Problem Solving's
required lessons are existing Code Crackers debugging exercises. Only
write new lesson YAML when nothing already teaches the concept a module
needs.

Whichever lessons you reference, add a validation test asserting they
exist — see `tests/test_learning_path.py`'s
`test_every_module_lesson_id_exists_in_the_real_lesson_content`, which
catches a typo'd id immediately instead of it surfacing as a confusing
runtime error deep in a UI screen.

## Lesson YAML additions for Python Journey

Four optional fields on top of the base `Lesson` schema
(`app/engine/lesson.py`) — all default to "not part of Journey", so
nothing about existing lessons changes by not setting them:

```yaml
learning_path_module: python-starter   # which module this lesson belongs to, if any
lesson_type: project                   # learn | practice | challenge | project
concept_tags: [print, strings, numbers, comments]
prerequisite_lesson_ids: []            # documentation only, not enforced -- see below
```

### `lesson_type`

Purely descriptive (shown in the Journey UI), doesn't change validation
behavior. One template per type, from the two lessons written for this
feature:

**`learn`** — a single new concept, "press RUN to see it work" style
(`starter_code` already satisfies the challenge, matching most main-path
lessons):

```yaml
# content/lessons/lesson_450_comments.yaml (trimmed)
id: lesson_450
lesson_type: learn
concept_tags: [comments]
example_code: |
  # This is a comment -- Python skips right over it.
  print("Comments help you leave notes in your code!")
starter_code: |
  # This is a comment -- Python skips right over it.
  print("Comments help you leave notes in your code!")
expected_output: "Comments help you leave notes in your code!"
```

**`project`** — a module's checkpoint: combines several of the module's
concepts into one small program, and *requires editing* (`starter_code`
deliberately does NOT satisfy the challenge unedited — the child has to
apply what they learned, not just press RUN):

```yaml
# content/lessons/lesson_451_intro_card.yaml (trimmed)
id: lesson_451
lesson_type: project
concept_tags: [print, strings, numbers, comments]
starter_code: |
  print("Favorite number:", favorite_number)  # favorite_number = 7
challenge: |
  🎯 Challenge: Change favorite_number to 42, and change the last line...
expected_output: |
  Favorite number: 42
  ...
```

`practice` and `challenge` aren't used by the 3 lessons written for this
feature (every module besides the first two reuses existing bonus-track
content, which predates `lesson_type` and defaults to `"learn"`) — use
`practice` for a straightforward drill (matches the existing 20-level
bonus tracks' style) and `challenge` for something harder than a `learn`
lesson but not a full multi-concept `project`.

### `concept_tags` and the fixed vocabulary

Powers "Practice Quest" (a suggestion to try 1-3 related lessons after a
child fails the same lesson 3 times in a row —
`app/progress/store.py`'s `get_recent_failure_count()` +
`app/engine/lesson_engine.py`'s `recommend_practice()`) and the quiz
results screen's "practice these next" (same matching, from the union of
tags across every question missed that session —
`recommend_practice_for_tags()`). Both only work between lessons/questions
that share at least one tag, so **use the same fixed vocabulary
everywhere** rather than inventing new tags per lesson:

```
print, strings, numbers, comments, expressions, variables, naming, input,
type-conversion, f-strings, comparison, booleans, conditionals, loops,
for-loops, while-loops, functions, parameters, return-values, lists,
indexing, slicing, dictionaries, iteration, debugging, errors, algorithms,
random, classes
```

Most lessons want 1-3 tags. It's fine to leave `concept_tags` empty on a
lesson that isn't meant to feed adaptive practice (the vast majority of
bonus content) — `recommend_practice()` simply returns nothing for an
untagged lesson, it's never an error. Quiz questions
(`content/quiz/quiz_questions.yaml`) use the identical field and
vocabulary — add `concept_tags: [tag1, tag2]` to a question the same way.

### `prerequisite_lesson_ids`

Present on the schema for future use, but **not enforced by the engine**
in this version — a module's own `required_lesson_ids` list order already
provides real, engine-checked sequencing (see `is_lesson_unlocked()`
above), and that's the only unlock mechanism Python Journey actually
uses today. Document real prerequisites here for future authors/tooling,
but don't rely on it to gate access to a lesson.

## Module badges (how the awarding actually happens)

There's no polling or background job — the check runs at two points,
both already wired up, no new code needed when you add a module:

1. **On lesson completion** — `_on_lesson_success()` in both
   `app/ui/lesson_screen_flet.py` and `app/ui/lesson_screen.py` (CTk)
   calls a shared `_award_module_badges()` helper right after
   `complete_lesson()`, which checks whether *this* completion just
   satisfied any module and awards its badge (plus the capstone
   `python_journey_complete` badge if it was the very last module).
2. **On opening the Journey map** — `build_journey_map_view()`
   (`app/ui/journey_map_flet.py`) runs the same
   `LearningPathEngine.newly_earned_module_badges()` check on every load.
   This is what makes migration free: a child who completed a module's
   lessons the old way, before Python Journey existed, gets the badge
   retroactively the first time they open the map — no migration script,
   since module completion is always computed live from
   `completed_lesson_ids`, never stored as its own flag.

## Testing new content

Follow the same real-execution rigor as every other content track in
this app — no lesson ships on "it looks right":

- Run the *solved* version of any new `starter_code`/`example_code`
  through the real sandbox (`app.sandbox.inprocess_runner.run_code` for
  Flet-only graphical content, `app.sandbox.runner.run_code` for
  everything else) and assert the real stdout matches `expected_output`
  via `app.engine.validator.validate_output()` — don't hand-write
  expected output from memory, Python's exact formatting (float division,
  list `repr()`, f-string spacing, …) is easy to get subtly wrong.
- If `starter_code` is meant to require editing (most `challenge`/
  `project` lessons), also assert the *unedited* starter does **not**
  satisfy the challenge — this catches an accidentally-already-solved
  lesson.
- Add the new module/lessons to `tests/test_learning_path.py`-style
  coverage: lock/unlock transitions, and the existence check described
  above under "Adding a 9th module".
