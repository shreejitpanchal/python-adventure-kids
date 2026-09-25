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


# -- modules added for the Python Learning course's Standard Library
# Deep Dive / Advanced Programming Concepts chapters -----------------------
@pytest.mark.parametrize("module", ["time", "collections", "itertools", "datetime", "json", "functools"])
def test_allows_the_stdlib_modules_added_for_the_course(module):
    check_code_safety(f"import {module}")


@pytest.mark.parametrize("module", ["threading", "asyncio", "logging"])
def test_still_blocks_concurrency_and_logging_modules(module):
    """Deliberately excluded even though they're common stdlib modules --
    real threads/event loops don't compose safely with this sandbox's
    hard-kill-after-5s timeout model. The course's concurrency lessons
    teach the concepts without importing these for real."""
    with pytest.raises(SafetyViolation):
        check_code_safety(f"import {module}")


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


# -- escape routes closed by the architecture review --------------------------
# private module attributes, frame/generator introspection, and dunder
# identifiers that could shadow the in-process watchdog's injected tick.

@pytest.mark.parametrize("source", [
    "import random\nrandom._os.system('calc')",
    "import collections\nprint(collections._sys.modules)",
    "from random import _os",
    "x = [1]\nx._private",
])
def test_blocks_leading_underscore_attributes_and_import_names(source):
    with pytest.raises(SafetyViolation):
        check_code_safety(source)


def test_allows_namedtuples_underscore_spelled_public_api():
    check_code_safety(
        "from collections import namedtuple\n"
        "Point = namedtuple('Point', 'x y')\n"
        "p = Point(1, 2)\n"
        "print(p._replace(x=3), p._asdict(), Point._fields, Point._make([4, 5]))\n"
    )


@pytest.mark.parametrize("source", [
    "def g():\n    yield 1\ngen = g()\nfor _ in gen:\n    print(gen.gi_frame.f_back)",
    "def g():\n    yield 1\nprint(g().gi_code)",
    "try:\n    1 / 0\nexcept ZeroDivisionError as e:\n    print(e.__traceback__.tb_frame)",
    "async def c():\n    pass\nprint(c().cr_frame)",
])
def test_blocks_frame_generator_and_traceback_introspection(source):
    with pytest.raises(SafetyViolation):
        check_code_safety(source)


@pytest.mark.parametrize("source", [
    "__pyadv_tick__ = lambda: None",
    "def __pyadv_tick__():\n    pass",
    "def f(__pyadv_tick__):\n    pass",
    "f = lambda __pyadv_tick__: 1",
    "import random as __pyadv_tick__",
    "from random import randint as __pyadv_tick__",
    "global __pyadv_tick__",
    "def f():\n    nonlocal __pyadv_tick__",
    "for __pyadv_tick__ in range(3):\n    pass",
    "try:\n    pass\nexcept Exception as __pyadv_tick__:\n    pass",
    "class __pyadv_tick__:\n    pass",
    "match 1:\n    case __pyadv_tick__:\n        pass",
    "print(__builtins__)",
])
def test_blocks_dunder_identifiers_everywhere_one_could_be_bound(source):
    with pytest.raises(SafetyViolation):
        check_code_safety(source)


def test_allows_dunder_method_names_directly_inside_a_class_body():
    check_code_safety(
        "class Dog:\n"
        "    def __init__(self, name):\n"
        "        self.name = name\n"
        "    def __str__(self):\n"
        "        return self.name\n"
    )


def test_blocks_a_dunder_def_nested_inside_a_method():
    # Inside a method, a local def named like the watchdog tick would
    # shadow the injected global call for that method's loops.
    with pytest.raises(SafetyViolation):
        check_code_safety(
            "class A:\n"
            "    def run(self):\n"
            "        def __pyadv_tick__():\n"
            "            pass\n"
        )


def test_still_allows_ordinary_course_style_stdlib_usage():
    check_code_safety(
        "import json, itertools, datetime\n"
        "from functools import reduce\n"
        "from collections import Counter\n"
        "print(json.dumps({'a': 1}))\n"
        "print(list(itertools.chain([1], [2])))\n"
        "print(datetime.date(2026, 1, 1))\n"
        "print(reduce(lambda a, b: a + b, [1, 2, 3]))\n"
        "print(Counter('aab'))\n"
    )
