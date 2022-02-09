import importlib
import os

import pytest

codemods = [
    "not_in",
    # "remove_builtins_imports",
    # "detect_past_builtins_imports",
    "remove_float_conversion",
]


def _get_files(codemod):
    input_file = os.path.join(os.path.dirname(__file__), "input", codemod + ".py")
    expected_file = os.path.join(os.path.dirname(__file__), "expected", codemod + ".py")
    return input_file, expected_file


def _run_test(codemod, input_file, expected_file, monkeypatch):
    monkeypatch.setattr(
        "sys.argv", ["codemod_" + codemod, "--test", input_file, expected_file]
    )
    module = importlib.import_module("octoprint_codemods." + codemod)
    getattr(module, "main")()


def _run_batch(input_file, expected_file, monkeypatch):
    argv = ["codemod_batch"]
    for codemod in codemods:
        argv += ["--check", codemod]
    argv += ["--test", input_file, expected_file]
    monkeypatch.setattr("sys.argv", argv)
    module = importlib.import_module("octoprint_codemods.batch")
    getattr(module, "main")()


@pytest.mark.parametrize(
    "codemod", [pytest.param(codemod, id=codemod) for codemod in codemods]
)
def test_codemods(codemod, monkeypatch):
    input_file, expected_file = _get_files(codemod)
    if not os.path.exists(input_file) or not os.path.exists(expected_file):
        pytest.fail("Input file or expected file missing for {}".format(codemod))

    with pytest.raises(SystemExit) as exc:
        _run_test(codemod, input_file, expected_file, monkeypatch)
    assert exc.value.code == 0


def test_batch(monkeypatch):
    codemod = "batch"

    input_file, expected_file = _get_files(codemod)
    if not os.path.exists(input_file) or not os.path.exists(expected_file):
        pytest.fail("Input file or expected file missing for batch")

    with pytest.raises(SystemExit) as exc:
        _run_batch(
            input_file,
            expected_file,
            monkeypatch,
        )
    assert exc.value.code == 0
