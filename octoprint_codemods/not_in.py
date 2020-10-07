from typing import Union

import libcst as cst

from .util import CodeMod, runner

"""
libcst based transformer to change 'not foo in bar' to 'foo not in bar' constructs.

Tool call heavily based on https://github.com/seatgeek/tornado-async-transformer

Whitespace for alignment is not properly used in all cases yet, patches welcome.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class NotIn(CodeMod):
    DESCRIPTION: str = "Converts 'not foo in bar' to 'foo not in bar' constructs."

    def leave_UnaryOperation(
        self, node: cst.UnaryOperation, updated_node: cst.UnaryOperation
    ) -> Union[cst.UnaryOperation, cst.Comparison]:
        if (
            isinstance(updated_node.operator, cst.Not)
            and isinstance(updated_node.expression, cst.Comparison)
            and len(updated_node.expression.comparisons) == 1
            and isinstance(updated_node.expression.comparisons[0], cst.ComparisonTarget)
            and isinstance(updated_node.expression.comparisons[0].operator, cst.In)
        ):
            new_node = cst.Comparison(
                left=updated_node.expression.left,
                comparisons=[
                    cst.ComparisonTarget(
                        operator=cst.NotIn(),
                        comparator=updated_node.expression.comparisons[0].comparator,
                    )
                ],
            )
            self.count += 1
            return new_node
        return node


def main():
    runner(NotIn)


if __name__ == "__main__":
    main()
