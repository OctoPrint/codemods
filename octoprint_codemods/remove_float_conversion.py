from typing import Union

import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to remove unnecessary float conversions.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class RemoveFloatConversion(CodeMod):
    DESCRIPTION: str = "Removes unnecessary float conversions"

    TARGET_OPERATOR = m.OneOf(
        m.Divide(), m.Multiply(), m.DivideAssign(), m.MultiplyAssign()
    )
    FLOAT_ARGUMENT = m.Float()
    FLOAT_CALL = m.Call(func=m.Name("float"), args=[m.Arg()])
    TARGET_ARGUMENT = m.OneOf(FLOAT_ARGUMENT, FLOAT_CALL)

    def _replace_float_arg(self, arg: cst.Float) -> Union[cst.Float, cst.Integer]:
        floatval = float(arg.value)
        if floatval == int(floatval):
            return cst.Integer(str(int(floatval)))
        return arg

    def _replace_float_call(self, arg: cst.Call) -> cst.BaseExpression:
        return arg.args[0].value

    def _replace_arg(self, arg):
        if m.matches(arg, self.FLOAT_ARGUMENT):
            return self._replace_float_arg(arg)
        elif m.matches(arg, self.FLOAT_CALL):
            return self._replace_float_call(arg)

    def leave_BinaryOperation(
        self, original_node: cst.BinaryOperation, updated_node: cst.BinaryOperation
    ) -> cst.BinaryOperation:
        if m.matches(
            updated_node,
            m.BinaryOperation(operator=self.TARGET_OPERATOR, left=self.TARGET_ARGUMENT),
        ):
            # left arg
            updated_node = updated_node.with_changes(
                left=self._replace_arg(updated_node.left)
            )

        if m.matches(
            updated_node,
            m.BinaryOperation(operator=self.TARGET_OPERATOR, right=self.TARGET_ARGUMENT),
        ):
            # right arg
            updated_node = updated_node.with_changes(
                right=self._replace_arg(updated_node.right)
            )

        return updated_node

    def leave_AugAssign(
        self, original_node: cst.AugAssign, updated_node: cst.AugAssign
    ) -> cst.AugAssign:
        if m.matches(
            updated_node,
            m.AugAssign(operator=self.TARGET_OPERATOR, value=self.TARGET_ARGUMENT),
        ):
            return updated_node.with_changes(value=self._replace_arg(updated_node.value))

        return updated_node


def main():
    runner(RemoveFloatConversion)


if __name__ == "__main__":
    main()
