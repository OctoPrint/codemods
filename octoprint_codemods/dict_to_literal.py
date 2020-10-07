from typing import Union

import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to change dict(**args) to literal {...} constructs.

Tool call heavily based on https://github.com/seatgeek/tornado-async-transformer

Whitespace for alignment is not properly used in all cases yet, patches welcome.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class DictConstructorToLiteral(CodeMod):
    DESCRIPTION: str = "Converts dict(**args) to literal {...} constructs."

    def __init__(self) -> None:
        super().__init__()
        self.arg_stack = []

    def visit_Arg(self, node: cst.Arg) -> bool:
        self.arg_stack.append(node)
        return True

    def leave_Arg(self, node: cst.Arg, updated_node: cst.Arg) -> cst.Arg:
        self.arg_stack.pop()
        return updated_node

    def leave_Call(
        self, node: cst.Call, updated_node: cst.Call
    ) -> Union[cst.Call, cst.Dict]:
        if m.matches(updated_node.func, m.Name("dict")) and all(
            map(lambda x: x.keyword is not None, updated_node.args)
        ):
            elements = []
            for arg in updated_node.args:
                alignment = 0
                if self.arg_stack:
                    # inside argument, so check whitespace from that
                    outer_arg = self.arg_stack[-1]
                    if isinstance(outer_arg.equal, cst.AssignEqual):
                        arg_align = "="
                        if isinstance(
                            outer_arg.equal.whitespace_before, cst.SimpleWhitespace
                        ):
                            arg_align = (
                                outer_arg.equal.whitespace_before.value + arg_align
                            )
                        if isinstance(
                            outer_arg.equal.whitespace_after, cst.SimpleWhitespace
                        ):
                            arg_align += outer_arg.equal.whitespace_after.value
                        alignment = len(arg_align)

                comma = None
                if arg.comma is not None:
                    if isinstance(arg.comma, cst.Comma):
                        if isinstance(
                            arg.comma.whitespace_after, cst.ParenthesizedWhitespace
                        ):
                            whitespace = arg.comma.whitespace_after
                            last_line = whitespace.last_line
                            last_line_value = last_line.value
                            if all(map(lambda x: x == " ", last_line_value)):
                                last_line_value = last_line_value[
                                    : -len("dict") - alignment
                                ]
                            last_line = last_line.with_changes(value=last_line_value)
                            whitespace = whitespace.with_changes(last_line=last_line)
                            comma = arg.comma.with_changes(whitespace_after=whitespace)
                        else:
                            comma = arg.comma
                    else:
                        comma = arg.comma

                elements.append(
                    cst.DictElement(
                        key=cst.SimpleString(
                            '"' + arg.keyword.value.replace('"', '\\"') + '"'
                        ),
                        value=arg.value,
                        comma=comma,
                    )
                )

            self.count += 1
            new_node = cst.Dict(elements)
            return new_node
        return updated_node


def main():
    runner(DictConstructorToLiteral)


if __name__ == "__main__":
    main()
