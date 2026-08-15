"""SQLite-backed progress, gamification, and activity tracking for the single child profile."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    level INTEGER NOT NULL DEFAULT 1,
    total_stars INTEGER NOT NULL DEFAULT 0,
    current_lesson_id TEXT,
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_played_date TEXT
);

CREATE TABLE IF NOT EXISTS lesson_completions (
    lesson_id TEXT PRIMARY KEY,
    stars_earned INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS badges (
    badge_id TEXT PRIMARY KEY,
    earned_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id TEXT,
    event_type TEXT NOT NULL,
    detail TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    completed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS player_xp (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    total_xp INTEGER NOT NULL DEFAULT 0
);
"""

# XP cost to clear level N is N * 100 (level 1->2 costs 100, 2->3 costs 200, ...).
_XP_PER_LEVEL_STEP = 100


def _level_from_xp(total_xp: int) -> tuple[int, int, int]:
    """(level, xp_into_level, xp_needed_for_level) for a cumulative XP total.

    Computed fresh from the single stored total_xp counter rather than
    storing level/remaining-xp as separate mutable fields, so there's one
    source of truth and the leveling curve can change later without
    migrating old stored state.
    """
    level = 1
    remaining = total_xp
    xp_needed = level * _XP_PER_LEVEL_STEP
    while remaining >= xp_needed:
        remaining -= xp_needed
        level += 1
        xp_needed = level * _XP_PER_LEVEL_STEP
    return level, remaining, xp_needed


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ProfileSummary:
    level: int
    total_stars: int
    current_lesson_id: Optional[str]
    streak_days: int
    lessons_completed: int
    badges_earned: int


@dataclass
class PlayerLevel:
    level: int
    xp_into_level: int
    xp_needed_for_level: int
    total_xp: int


@dataclass
class WeeklySummary:
    lessons_completed: int
    stars_earned: int
    quiz_attempts: int
    badges_earned: int
    active_days: int
    """Distinct calendar dates (UTC) with at least one logged activity
    event in the window -- not the same as streak_days, which tracks
    *consecutive* days going back from today regardless of window size."""


class ProgressStore:
    """Owns the SQLite connection for the child's progress data."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.executescript(SCHEMA)
            self._conn.execute(
                "INSERT OR IGNORE INTO profile (id, level, total_stars) VALUES (1, 1, 0)"
            )
            self._conn.execute(
                "INSERT OR IGNORE INTO player_xp (id, total_xp) VALUES (1, 0)"
            )

    def close(self) -> None:
        self._conn.close()

    # -- Profile -----------------------------------------------------
    def get_summary(self) -> ProfileSummary:
        with closing(self._conn.cursor()) as cur:
            cur.execute(
                "SELECT level, total_stars, current_lesson_id, streak_days FROM profile WHERE id = 1"
            )
            level, total_stars, current_lesson_id, streak_days = cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM lesson_completions")
            lessons_completed = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM badges")
            badges_earned = cur.fetchone()[0]
        return ProfileSummary(
            level=level,
            total_stars=total_stars,
            current_lesson_id=current_lesson_id,
            streak_days=streak_days,
            lessons_completed=lessons_completed,
            badges_earned=badges_earned,
        )

    def set_current_lesson(self, lesson_id: str) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE profile SET current_lesson_id = ? WHERE id = 1", (lesson_id,)
            )

    def set_level(self, level: int) -> None:
        with self._conn:
            self._conn.execute("UPDATE profile SET level = ? WHERE id = 1", (level,))

    def record_play_today(self) -> None:
        today = datetime.now(timezone.utc).date().isoformat()
        with closing(self._conn.cursor()) as cur:
            cur.execute("SELECT last_played_date, streak_days FROM profile WHERE id = 1")
            last_played, streak = cur.fetchone()
        if last_played == today:
            return
        if last_played is not None:
            gap_days = (
                datetime.fromisoformat(today) - datetime.fromisoformat(last_played)
            ).days
            streak = streak + 1 if gap_days == 1 else 1
        else:
            streak = 1
        with self._conn:
            self._conn.execute(
                "UPDATE profile SET last_played_date = ?, streak_days = ? WHERE id = 1",
                (today, streak),
            )

    # -- Lessons -------------------------------------------------------
    def complete_lesson(self, lesson_id: str, stars_earned: int) -> None:
        # XP is only awarded the first time a lesson is completed -- otherwise
        # replaying an already-completed lesson would let XP be farmed
        # infinitely, unlike stars (which are already capped via MAX() below).
        first_time = not self.is_lesson_completed(lesson_id)
        with self._conn:
            self._conn.execute(
                """INSERT INTO lesson_completions (lesson_id, stars_earned, completed_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(lesson_id) DO UPDATE SET
                     stars_earned = MAX(stars_earned, excluded.stars_earned),
                     completed_at = excluded.completed_at""",
                (lesson_id, stars_earned, _now()),
            )
            self._conn.execute(
                "UPDATE profile SET total_stars = (SELECT COALESCE(SUM(stars_earned), 0) FROM lesson_completions) WHERE id = 1"
            )
        self.log_event(lesson_id, "lesson_completed", f"stars={stars_earned}")
        if first_time:
            self.add_xp(stars_earned * 10)

    def is_lesson_completed(self, lesson_id: str) -> bool:
        with closing(self._conn.cursor()) as cur:
            cur.execute(
                "SELECT 1 FROM lesson_completions WHERE lesson_id = ?", (lesson_id,)
            )
            return cur.fetchone() is not None

    def get_completed_lesson_ids(self) -> list[str]:
        with closing(self._conn.cursor()) as cur:
            cur.execute("SELECT lesson_id FROM lesson_completions")
            return [row[0] for row in cur.fetchall()]

    def get_stars_by_lesson(self) -> dict[str, int]:
        with closing(self._conn.cursor()) as cur:
            cur.execute("SELECT lesson_id, stars_earned FROM lesson_completions")
            return {lesson_id: stars for lesson_id, stars in cur.fetchall()}

    # -- Badges ----------------------------------------------------------
    def award_badge(self, badge_id: str) -> bool:
        """Returns True if newly awarded, False if already had it."""
        with self._conn:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO badges (badge_id, earned_at) VALUES (?, ?)",
                (badge_id, _now()),
            )
            newly_awarded = cur.rowcount > 0
        if newly_awarded:
            self.log_event(None, "badge_earned", badge_id)
        return newly_awarded

    def get_badge_ids(self) -> list[str]:
        with closing(self._conn.cursor()) as cur:
            cur.execute("SELECT badge_id FROM badges ORDER BY earned_at")
            return [row[0] for row in cur.fetchall()]

    def get_badges_with_dates(self) -> list[tuple[str, str]]:
        """(badge_id, earned_at ISO timestamp) pairs, oldest first -- for the
        Trophy Room, which shows when each badge was earned."""
        with closing(self._conn.cursor()) as cur:
            cur.execute("SELECT badge_id, earned_at FROM badges ORDER BY earned_at")
            return [(row[0], row[1]) for row in cur.fetchall()]

    # -- Quiz --------------------------------------------------------------
    def record_quiz_attempt(self, score: int, total: int) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO quiz_attempts (score, total, completed_at) VALUES (?, ?, ?)",
                (score, total, _now()),
            )
        self.log_event(None, "quiz_completed", f"score={score}/{total}")
        # Every attempt is a freshly randomized session, so unlike lessons
        # there's no first-time-only gate -- XP per correct answer is safe
        # from farming since it still requires answering correctly each time.
        self.add_xp(score * 5)

    def get_best_quiz_score(self) -> Optional[tuple[int, int]]:
        """(score, total) of the highest-scoring attempt, or None if never played."""
        with closing(self._conn.cursor()) as cur:
            cur.execute(
                "SELECT score, total FROM quiz_attempts ORDER BY (score * 1.0 / total) DESC, score DESC LIMIT 1"
            )
            row = cur.fetchone()
            return (row[0], row[1]) if row else None

    def get_quiz_attempt_count(self) -> int:
        with closing(self._conn.cursor()) as cur:
            cur.execute("SELECT COUNT(*) FROM quiz_attempts")
            return cur.fetchone()[0]

    # -- XP / leveling -------------------------------------------------------
    def add_xp(self, amount: int) -> PlayerLevel:
        """Awards XP (amount may be 0, e.g. a lesson worth 0 stars) and
        returns the resulting level/progress."""
        if amount:
            with self._conn:
                self._conn.execute(
                    "UPDATE player_xp SET total_xp = total_xp + ? WHERE id = 1", (amount,)
                )
        return self.get_player_level()

    def get_player_level(self) -> PlayerLevel:
        with closing(self._conn.cursor()) as cur:
            cur.execute("SELECT total_xp FROM player_xp WHERE id = 1")
            (total_xp,) = cur.fetchone()
        level, xp_into_level, xp_needed = _level_from_xp(total_xp)
        return PlayerLevel(
            level=level, xp_into_level=xp_into_level, xp_needed_for_level=xp_needed, total_xp=total_xp,
        )

    # -- Activity log (feeds the parent dashboard) ------------------------
    def log_event(self, lesson_id: Optional[str], event_type: str, detail: str = "") -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO activity_log (lesson_id, event_type, detail, timestamp) VALUES (?, ?, ?, ?)",
                (lesson_id, event_type, detail, _now()),
            )

    def get_recent_activity(self, limit: int = 50) -> list[sqlite3.Row]:
        conn = self._conn
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cur:
            cur.execute(
                "SELECT * FROM activity_log ORDER BY id DESC LIMIT ?", (limit,)
            )
            rows = cur.fetchall()
        conn.row_factory = None
        return rows

    def get_activity_since(self, cutoff_iso: str) -> list[sqlite3.Row]:
        """Activity log rows at or after cutoff_iso (an ISO-8601 timestamp
        string, same format _now() produces -- lexically comparable since
        both are UTC), newest first."""
        conn = self._conn
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cur:
            cur.execute(
                "SELECT * FROM activity_log WHERE timestamp >= ? ORDER BY id DESC", (cutoff_iso,)
            )
            rows = cur.fetchall()
        conn.row_factory = None
        return rows

    def get_weekly_summary(self) -> WeeklySummary:
        """Activity in the last 7 days, for the parent dashboard's "This
        Week" card. detail's "stars=N" shape (see complete_lesson()) is
        parsed here rather than given its own column -- it's the same
        free-text detail field every other event_type already uses."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        rows = self.get_activity_since(cutoff)

        lessons_completed = 0
        stars_earned = 0
        quiz_attempts = 0
        badges_earned = 0
        active_dates: set[str] = set()

        for row in rows:
            event_type = row["event_type"]
            active_dates.add(row["timestamp"][:10])
            if event_type == "lesson_completed":
                lessons_completed += 1
                detail = row["detail"] or ""
                if detail.startswith("stars="):
                    try:
                        stars_earned += int(detail.split("=", 1)[1])
                    except ValueError:
                        pass
            elif event_type == "quiz_completed":
                quiz_attempts += 1
            elif event_type == "badge_earned":
                badges_earned += 1

        return WeeklySummary(
            lessons_completed=lessons_completed,
            stars_earned=stars_earned,
            quiz_attempts=quiz_attempts,
            badges_earned=badges_earned,
            active_days=len(active_dates),
        )

    # -- Parent controls ---------------------------------------------------
    def reset_progress(self) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM lesson_completions")
            self._conn.execute("DELETE FROM badges")
            self._conn.execute("DELETE FROM activity_log")
            self._conn.execute("DELETE FROM quiz_attempts")
            self._conn.execute(
                "UPDATE profile SET level = 1, total_stars = 0, current_lesson_id = NULL, streak_days = 0, last_played_date = NULL WHERE id = 1"
            )
            self._conn.execute("UPDATE player_xp SET total_xp = 0 WHERE id = 1")
