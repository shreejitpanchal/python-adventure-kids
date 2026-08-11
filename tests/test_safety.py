import pytest

from app.sandbox.safety import SafetyViolation, check_code_safety


def test_allows_ordinary_code():
    check_code_safety('print("Hello!")')
    check_code_safety("x = 1 + 2\nprint(x)")


def test_blocks_import_statement():
    with pytest.raises(SafetyViolation):
        check_code_safety("import os")


def test_blocks_import_from():
    with pytest.raises(SafetyViolation):
        check_code_safety("from os import system")


def test_allows_the_random_module():
    check_code_safety("import random\nrandom.randint(1, 10)")
    check_code_safety("from random import choice")


def test_still_blocks_other_modules_from_import():
    with pytest.raises(SafetyViolation):
        check_code_safety("from sys import exit")
    with pytest.raises(SafetyViolation):
        check_code_safety("import subprocess")


def test_blocks_eval_and_exec():
    with pytest.raises(SafetyViolation):
        check_code_safety("eval('1+1')")
    with pytest.raises(SafetyViolation):
        check_code_safety("exec('print(1)')")


def test_blocks_open():
    with pytest.raises(SafetyViolation):
        check_code_safety("open('secrets.txt')")


def test_blocks_dunder_attribute_access():
    with pytest.raises(SafetyViolation):
        check_code_safety("().__class__.__bases__")


def test_lets_syntax_errors_through_for_the_real_interpreter():
    # Should not raise SafetyViolation -- the real run will surface a friendly SyntaxError instead.
    check_code_safety("print('unterminated")


def test_while_loop_allowed_by_default():
    # Subprocess-sandboxed lessons have an OS timeout, so while loops are fine there.
    check_code_safety("while False:\n    pass")


def test_while_loop_blocked_when_disallowed():
    with pytest.raises(SafetyViolation):
        check_code_safety("while True:\n    pass", disallow_while=True)
