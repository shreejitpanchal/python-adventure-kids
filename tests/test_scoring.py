from app.engine.scoring import (
    COMBO_THRESHOLD, COMBO_XP_MULTIPLIER, combo_label, combo_multiplier, improvement_hint, stars_for_attempt,
)


def test_full_stars_for_a_clean_pass_and_one_failure_is_free():
    assert stars_for_attempt(3, hints_used=0, failed_attempts=0) == 3
    assert stars_for_attempt(3, hints_used=0, failed_attempts=1) == 3


def test_any_hint_costs_a_star():
    assert stars_for_attempt(3, hints_used=1, failed_attempts=0) == 2
    assert stars_for_attempt(3, hints_used=4, failed_attempts=0) == 2


def test_two_or_more_failed_attempts_cost_a_star():
    assert stars_for_attempt(3, hints_used=0, failed_attempts=2) == 2
    assert stars_for_attempt(3, hints_used=0, failed_attempts=9) == 2


def test_both_penalties_stack_but_never_below_one_star():
    assert stars_for_attempt(3, hints_used=1, failed_attempts=2) == 1
    assert stars_for_attempt(2, hints_used=1, failed_attempts=2) == 1
    assert stars_for_attempt(1, hints_used=3, failed_attempts=5) == 1


def test_improvement_hint_names_what_to_fix():
    assert improvement_hint(3, 3, hints_used=0, failed_attempts=0) is None
    assert "without hints" in improvement_hint(2, 3, hints_used=1, failed_attempts=0)
    assert "fewer tries" in improvement_hint(2, 3, hints_used=0, failed_attempts=2)
    both = improvement_hint(1, 3, hints_used=1, failed_attempts=2)
    assert "no hints" in both and "first try" in both
    assert "⭐⭐⭐" in both


def test_combo_multiplier_kicks_in_at_the_threshold():
    for combo in range(COMBO_THRESHOLD):
        assert combo_multiplier(combo) == 1
    assert combo_multiplier(COMBO_THRESHOLD) == COMBO_XP_MULTIPLIER
    assert combo_multiplier(10) == COMBO_XP_MULTIPLIER


def test_combo_label_is_hidden_for_a_single_lesson_then_counts_up():
    assert combo_label(0) is None and combo_label(1) is None
    assert combo_label(2) == "Combo x2 — one more for 2× XP"
    assert combo_label(3) == "Combo x3 — 2× XP!"
