from typing import Union, cast

import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to change 'not foo in bar' to 'foo not in bar' constructs.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class NotIn(CodeMod):
    DESCRIPTION: str = "Converts 'not foo in bar' to 'foo not in bar' constructs."

    def leave_UnaryOperation(
        self, node: cst.UnaryOperation, updated_node: cst.UnaryOperation
    ) -> Union[cst.UnaryOperation, cst.Comparison]:
        if m.matches(
            updated_node,
            m.UnaryOperation(
                operator=m.Not(),
                expression=m.Comparison(
                    comparisons=[m.ComparisonTarget(operator=m.In())]
                ),
            ),
        ):
            expression = cast(cst.Comparison, updated_node.expression)
            new_node = cst.Comparison(
                left=expression.left,
                comparisons=[
                    cst.ComparisonTarget(
                        operator=cst.NotIn(),
                        comparator=expression.comparisons[0].comparator,
                    )
                ],
            )
            self.count += 1
            return new_node
        return updated_node


def main():
    runner(NotIn)


if __name__ == "__main__":
    main()
