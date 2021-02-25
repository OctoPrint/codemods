import io
import os
import subprocess
import sys

import pytest

codemods = [
    # "dict_to_literal",
    "set_to_literal",
    "not_in",
    "remove_future_imports",
    # "remove_builtins_imports",
    # "detect_past_builtins_imports",
    "py3_class_inheritance",
    "oserror_merge",
    "yield_from_generator",
    "dict_comprehension_to_literal",
    "string_encoding",
    "py3_super",
]


def _get_files(codemod):
    input_file = os.path.join(os.path.dirname(__file__), "fixtures", codemod + ".py")
    expected_file = os.path.join(os.path.dirname(__file__), "expected", codemod + ".py")
    return input_file, expected_file


def _run_test(codemod, input_file, expected_file):
    with subprocess.Popen(
        r"{} -m octoprint_codemods.{} --test {} {}".format(
            sys.executable, codemod, input_file, expected_file
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as p:

        p.stdout = io.TextIOWrapper(p.stdout, encoding="utf-8", errors="replace")
        p.stderr = io.TextIOWrapper(p.stderr, encoding="utf-8", errors="replace")

        output, errors = p.communicate()
        returncode = p.returncode

    return returncode, output, errors


@pytest.mark.parametrize(
    "codemod", [pytest.param(codemod, id=codemod) for codemod in codemods]
)
def test_codemods(codemod):
    input_file, expected_file = _get_files(codemod)
    if not os.path.exists(input_file) or not os.path.exists(expected_file):
        pytest.fail("Input file or expected file missing for {}".format(codemod))

    returncode, output, errors = _run_test(codemod, input_file, expected_file)
    if returncode != 0:
        print(errors + output)
        pytest.fail("Returncode not 0, test failed")
