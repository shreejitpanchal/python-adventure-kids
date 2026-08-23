---
description: Run the full test suite and a quick CTk launch sanity check.
---

Run these two checks, in order, and report the results:

1. Full pytest suite:
   ```
   .venv\Scripts\python.exe -m pytest tests\ -q
   ```
   This repo has no linter/formatter configured — don't invent one. If
   anything fails, investigate and fix the root cause rather than skipping
   or loosening the failing test.

2. Quick launch sanity check for the shipping CustomTkinter app (should open
   without raising; a few seconds is enough to confirm, then stop it):
   ```
   timeout 8 .venv\Scripts\python.exe main.py
   ```

If UI files were touched in `app/ui/*_flet.py`, also mention that
`flet run main_flet.py` should be manually clicked through — it isn't
covered by an automated launch check the way the CTk app is.
