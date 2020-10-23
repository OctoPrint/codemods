# 👷‍♀️ OctoPrint codemods

Helpful codemods based on [LibCST](https://github.com/Instagram/LibCST/) created for use in OctoPrint development.

Provided as-is for documentationational purposes.

## Setup

    pip3 install .

## Usage

See

    codemod_* --help

## pre-commit

This repository can be used with [pre-commit](https://pre-commit.com/).

``` yaml
  - repo: https://github.com/OctoPrint/codemods
    rev: main
    hooks:
      - id: codemod_dict_to_literal
      - id: codemod_set_to_literal
      - id: codemod_not_in
```

## License

MIT
