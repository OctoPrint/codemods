from typing import Union

import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to convert 'for x in generator: yield x' to 'yield from generator'.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class YieldFromGenerator(CodeMod):
    DESCRIPTION: str = "Converts 'for x in generator: yield x' to 'yield from generator'."

    def leave_For(
        self, original_node: cst.For, updated_node: cst.For
    ) -> Union[cst.For, cst.SimpleStatementLine]:
        if m.matches(
            updated_node.body,
            m.IndentedBlock(body=[m.SimpleStatementLine(body=[m.Expr(value=m.Yield())])]),
        ):
            self.count += 1
            updated_node = cst.SimpleStatementLine(
                body=[cst.Expr(value=cst.Yield(value=cst.From(item=updated_node.iter)))]
            )
        return updated_node


def main():
    runner(YieldFromGenerator)


if __name__ == "__main__":
    main()
