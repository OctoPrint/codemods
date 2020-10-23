from typing import Union

import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to check for 'from builtins import ...' imports
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class CheckBuiltinsImports(CodeMod):
    DESCRIPTION: str = "Removes 'from builtins import ...' and 'import builtins'"

    def leave_Import(
        self, node: cst.Import, updated_node: cst.Import
    ) -> Union[cst.Import, cst.RemovalSentinel]:
        if m.matches(
            updated_node,
            m.Import(
                names=[
                    m.ZeroOrMore(),
                    m.ImportAlias(name=m.Name("builtins")),
                    m.ZeroOrMore(),
                ]
            ),
        ):
            self.count += 1
            return cst.RemovalSentinel.REMOVE
        return updated_node

    def leave_ImportFrom(
        self, node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> Union[cst.ImportFrom, cst.RemovalSentinel]:
        if m.matches(updated_node.module, m.Name("builtins")):
            self.count += 1
            return cst.RemovalSentinel.REMOVE
        return updated_node


def main():
    runner(CheckBuiltinsImports)


if __name__ == "__main__":
    main()
