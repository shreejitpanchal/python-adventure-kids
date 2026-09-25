"""The shared restricted runtime environment (app/sandbox/allowed_builtins.py):
the one place both engines get their builtins and module views from."""
import types

import pytest

from app.sandbox.allowed_builtins import (
    ALLOWED_BUILTIN_NAMES, build_safe_builtins, make_module_view, make_restricted_import,
)
from app.sandbox.safety import ALLOWED_MODULES


def test_view_hides_private_and_submodule_attributes_but_keeps_public_api():
    import json
    import random

    random_view = make_module_view(random)
    assert not hasattr(random_view, "_os"), "random._os is the real os module"
    assert callable(random_view.randint)
    assert callable(random_view.choice)

    json_view = make_module_view(json)
    assert not hasattr(json_view, "decoder"), "json.decoder -> re -> enum -> sys"
    assert json_view.dumps({"a": 1}) == '{"a": 1}'
    assert json_view.loads("[1, 2]") == [1, 2]


def test_no_allowlisted_module_view_exposes_a_private_name_or_a_module_object():
    restricted_import = make_restricted_import()
    for module_name in ALLOWED_MODULES:
        view = restricted_import(module_name)
        assert isinstance(view, types.SimpleNamespace)
        for attr, value in vars(view).items():
            assert not attr.startswith("_"), f"{module_name}.{attr}"
            assert not isinstance(value, types.ModuleType), f"{module_name}.{attr} is a module"


@pytest.mark.parametrize("name", ["os", "sys", "subprocess", "json.decoder", "random.foo"])
def test_restricted_import_rejects_disallowed_and_dotted_names(name):
    with pytest.raises(ImportError):
        make_restricted_import()(name)


def test_restricted_import_rejects_relative_imports():
    with pytest.raises(ImportError):
        make_restricted_import()("random", level=1)


def test_overrides_replace_one_attribute_of_a_view():
    marker = object()
    view = make_restricted_import({"time": {"sleep": marker}})("time")
    assert view.sleep is marker
    assert callable(view.monotonic), "other attributes are untouched"


def test_views_are_cached_within_a_run_but_isolated_between_runs():
    run_a = make_restricted_import()
    run_b = make_restricted_import()
    assert run_a("random") is run_a("random")
    run_a("random").randint = None
    assert callable(run_b("random").randint), "one run's mutation must not leak into the next"


def test_build_safe_builtins_is_exactly_the_allowlist_plus_restricted_import():
    safe = build_safe_builtins()
    assert set(safe) == set(ALLOWED_BUILTIN_NAMES) | {"__import__"}
    for dangerous in ("open", "getattr", "eval", "exec", "__build_class__"):
        assert dangerous not in safe


def test_from_import_forms_work_against_a_view():
    namespace = {"__builtins__": build_safe_builtins()}
    exec(
        "from collections import Counter\n"
        "from random import *\n"
        "counts = Counter('aab')\n"
        "n = randint(3, 3)\n",
        namespace,
    )
    assert namespace["counts"]["a"] == 2
    assert namespace["n"] == 3


def test_from_import_of_a_hidden_name_is_an_import_error():
    namespace = {"__builtins__": build_safe_builtins()}
    with pytest.raises(ImportError):
        exec("from json import decoder", namespace)
