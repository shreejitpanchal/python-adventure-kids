from app.sandbox.runner import RunHandle, run_code


def test_successful_run_captures_stdout():
    result = run_code('print("Hello!")')
    assert result.success is True
    assert result.stdout.strip() == "Hello!"
    assert result.blocked is False
    assert result.timed_out is False


def test_syntax_error_is_reported_not_blocked():
    result = run_code('print("Hello!"')
    assert result.success is False
    assert result.blocked is False
    assert "SyntaxError" in result.stderr


def test_runtime_error_is_reported():
    result = run_code("print(1 / 0)")
    assert result.success is False
    assert "ZeroDivisionError" in result.stderr


def test_blocked_import_never_executes():
    result = run_code("import os\nprint('should not run')")
    assert result.blocked is True
    assert result.stdout == ""


def test_blocked_dangerous_call_never_executes():
    result = run_code("eval('1+1')")
    assert result.blocked is True


def test_infinite_loop_times_out():
    result = run_code("while True:\n    pass", timeout=1.5)
    assert result.timed_out is True
    assert result.success is False


def test_cancel_stops_a_running_process():
    handle = RunHandle()
    handle.cancel()
    # Cancelling before the process even starts should still result in it being killed immediately.
    result = run_code("while True:\n    pass", timeout=5, handle=handle)
    assert result.timed_out is True


def test_input_reads_from_provided_stdin():
    result = run_code('name = input("Name? ")\nprint("Hi " + name)', stdin_text="Sam\n")
    assert result.success is True
    assert result.stdout == "Name? Hi Sam\n"


def test_input_without_stdin_fails_fast_with_eof_instead_of_hanging():
    import time

    start = time.time()
    result = run_code("print(input())", timeout=5)
    elapsed = time.time() - start

    assert result.success is False
    assert result.timed_out is False
    assert "EOFError" in result.stderr
    assert elapsed < 4, "should fail immediately on EOF, not wait out the timeout"


def test_random_module_is_usable_end_to_end():
    result = run_code("import random\nn = random.randint(1, 10)\nprint(1 <= n <= 10)")
    assert result.success is True
    assert result.stdout.strip() == "True"


def test_disallowed_module_is_blocked_even_though_random_is_allowed():
    result = run_code("import subprocess")
    assert result.blocked is True


# -- the subprocess engine shares app/sandbox/allowed_builtins.py's environment --

def test_private_module_attribute_escape_is_blocked_in_the_subprocess_engine_too():
    result = run_code("import random\nprint(random._os.getcwd())")
    assert result.blocked is True


def test_worker_serves_module_views_so_submodules_are_hidden_at_runtime():
    result = run_code("import json\nprint(json.dumps([1]))\nprint(json.decoder)")
    assert result.success is False
    assert result.stdout.strip() == "[1]"
    assert "AttributeError" in result.stderr


def test_course_stdlib_modules_work_end_to_end_in_the_subprocess_engine():
    result = run_code(
        "import itertools, datetime\n"
        "from collections import Counter\n"
        "from functools import reduce\n"
        "print(list(itertools.chain([1], [2])), datetime.date(2026, 1, 1), "
        "Counter('aab')['a'], reduce(lambda a, b: a + b, [1, 2, 3]))\n"
    )
    assert result.success is True, result.stderr
    assert result.stdout.strip() == "[1, 2] 2026-01-01 2 6"
