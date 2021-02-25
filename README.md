# 👷‍♀️ OctoPrint codemods

Helpful codemods based on [LibCST](https://github.com/Instagram/LibCST/) created for use in OctoPrint development.

Provided as-is for documentationational purposes.

## Setup

    pip3 install .

## Usage

See

    codemod_* --help

E.g.

```
$ codemod_not_in --help
usage: codemod_not_in [-h] [--before] [--after] [--dryrun] [--ignore IGNORE]
                      [--verbose] [--test]
                      bases [bases ...]

Converts 'not foo in bar' to 'foo not in bar' constructs.

positional arguments:
  bases            Files and directories (recursive) including python files to
                   be modified.

optional arguments:
  -h, --help       show this help message and exit
  --before         Write the CST of the original file to file.cst.before
  --after          Write the CST of the transformed file to file.cst.after
  --dryrun         Only perform a dry run without writing back the transformed
                   file
  --ignore IGNORE  Paths to ignore, add multiple as required
  --verbose        Generate output for all processed files, not juse for those
                   with replacements
  --test           Run in test mode: first path is input file, second path is
                   file with expected output.
```

To run in test mode, use `--test` and supply two files, input and expected output, e.g.:

```
$ codemod_not_in --test tests/input/not_in.py tests/expected/not_in.py
tests/input/not_in.py:4:0:
  not foo in bar
✨ Test successful, contents identical
```

## pre-commit

This repository can be used with [pre-commit](https://pre-commit.com/).

```yaml
- repo: https://github.com/OctoPrint/codemods
  rev: main
  hooks:
      - id: codemod_dict_to_literal
      - id: codemod_set_to_literal
      - id: codemod_not_in
```

Additional arguments can also be specified:

```yaml
- repo: https://github.com/OctoPrint/codemods
  rev: main
  hooks:
      - id: codemod_dict_to_literal
        args: ["--ignore", "lib/vendor"]
      - id: remove_future_imports
        args: ["--allow", "division", "--allow", "unicode_literals"]
```

## What codemods are available?

### `dict_comprehension_to_literal`

Converts `dict((x.a, x.b) for x in y)` to `{x.a: x.b for x in y}`.

### `dict_to_literal`

Converts `dict(**args)` to literal `{...}` constructs.

### `not_in`

Converts `not foo in bar` to `foo not in bar` constructs.

### `oserror_merge`

Converts `EnvironmentError` and friends to `OSError`.

Use with Python 3 source only.

### `py3_class_inheritance`

Converts `class Foo(object):` to `class Foo:`.

Use with Python 3 source only.

### `py3_super`

Converts `super(cls, self).member` to `super().member`.

Use with Python 3 source only.

### `remove_builtins_imports`

Removes `from builtins import ...` and `import builtins`.

Use with Python 3 source only.

### `remove_float_conversion`

Removes unnecessary float conversions and `.0`s in division and multiplication.

Use with Python 3 source only, unless `from __future__ import division` is used.

### `remove_future_imports`

Removes `from __future__ import ...`.

Allowed imports can be specified with `--allow`.

Use with Python 3 source only.

### `set_to_literal`

Converts `set(*args)` to literal `{...}` constructs.

### `string_encoding`

Converts `r"abc".encode("utf-8")` to `rb"abc"` and `"abc".encode("utf-8")` to `"abc".encode()`.

Use with Python 3 source only, unless `from __future__ import unicode_literals` is used.

### `yield_from_generator`

Converts `for x in generator: yield x` to `yield from generator`.

Use with Python 3 source only.

## What code checks are available?

### `detect_past_builtins_imports`

Detects `from past... import ...` & `import past...`.

Use with Python 3 source only.

## Development

Checkout out the source. Install source and requirements, in editable mode:

```
pip install -e . -r requirements.txt
```

All existing tests can be run with `pytest`.

Individual tests can be run with `codemod_{codemod} --test tests/input/{codemod}.py tests/expected/{codemod}.py` (replacing `{codemod}` with the codemod to test).

When adding new codemods or checks, add implementation to `octoprint_codemods` (be sure to inherit from `octoprint_codemods.Codemod` or `octoprint_codemods.Codecheck` and implement `main` using `octoprint_codemods.runner`, see existing code).

`--before` and `--after` can be used to generated dumps of the CST before and after transformation. `--dryrun` helps to keep input unmodified during development.

## License

MIT
