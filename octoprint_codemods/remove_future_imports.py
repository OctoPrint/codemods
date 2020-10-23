from typing import Union

import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to check for 'from __future__ import ...'.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class CheckFutureImports(CodeMod):
    DESCRIPTION: str = "Removes 'from __future__ import ...'"

    @classmethod
    def add_parser_args(cls, parser):
        parser.add_argument(
            "--allow",
            type=str,
            default=[],
            action="append",
            help="Future imports to allow, add multiple as required",
        )

    def leave_ImportFrom(
        self, node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> Union[cst.ImportFrom, cst.RemovalSentinel]:
        if m.matches(updated_node.module, m.Name("__future__")):
            names = list(
                filter(
                    lambda x: not isinstance(x, cst.ImportAlias)
                    or cst.ensure_type(x.name, cst.Name).value in self.args.allow,
                    updated_node.names,
                )
            )
            self.count += 1
            if names:
                return updated_node.with_changes(names=names)
            else:
                return cst.RemovalSentinel.REMOVE
        return updated_node


def main():
    runner(CheckFutureImports)


if __name__ == "__main__":
    main()
