import time

import pytest

from app.sandbox.watchdog import CHECK_INTERVAL, TICK_FUNC_NAME, Watchdog, WatchdogTimeout, compile_with_watchdog


def test_watchdog_does_not_raise_before_deadline_or_cancellation():
    wd = Watchdog(timeout=5.0)
    for _ in range(CHECK_INTERVAL * 3):
        wd.tick()  # should not raise


def test_watchdog_raises_once_deadline_elapses():
    wd = Watchdog(timeout=0.01)
    time.sleep(0.05)
    with pytest.raises(WatchdogTimeout):
        for _ in range(CHECK_INTERVAL):
            wd.tick()


def test_watchdog_raises_immediately_once_cancelled():
    wd = Watchdog(timeout=5.0)
    wd.cancel()
    with pytest.raises(WatchdogTimeout):
        wd.tick()


def test_compile_with_watchdog_injects_tick_into_for_loop():
    calls = []
    compiled = compile_with_watchdog("for i in range(3):\n    pass\n")
    exec(compiled, {TICK_FUNC_NAME: lambda: calls.append(1), "__builtins__": {"range": range}})
    assert len(calls) == 3


def test_compile_with_watchdog_injects_tick_into_while_loop():
    calls = []
    compiled = compile_with_watchdog("i = 0\nwhile i < 3:\n    i += 1\n")
    exec(compiled, {TICK_FUNC_NAME: lambda: calls.append(1), "__builtins__": {}})
    assert len(calls) == 3


def test_compile_with_watchdog_injects_tick_into_nested_loops():
    calls = []
    compiled = compile_with_watchdog("for i in range(2):\n    for j in range(2):\n        pass\n")
    exec(compiled, {TICK_FUNC_NAME: lambda: calls.append(1), "__builtins__": {"range": range}})
    assert len(calls) == 2 + 4  # 2 outer ticks, 4 inner ticks


def test_compile_with_watchdog_preserves_line_numbers_for_errors():
    source = "x = 1\nfor i in range(1):\n    raise ValueError('boom')\n"
    compiled = compile_with_watchdog(source)

    try:
        exec(
            compiled,
            {TICK_FUNC_NAME: lambda: None, "__builtins__": {"range": range, "ValueError": ValueError}},
        )
        pytest.fail("expected ValueError")
    except ValueError as e:
        tb = e.__traceback__
        while tb.tb_next is not None:
            tb = tb.tb_next
        assert tb.tb_lineno == 3


def test_watchdog_tick_is_cheap_for_a_large_fast_loop():
    calls = []
    compiled = compile_with_watchdog("total = 0\nfor i in range(200000):\n    total += i\n")
    start = time.time()
    exec(compiled, {TICK_FUNC_NAME: lambda: calls.append(1), "__builtins__": {"range": range}})
    elapsed = time.time() - start

    assert len(calls) == 200000
    assert elapsed < 2.0
