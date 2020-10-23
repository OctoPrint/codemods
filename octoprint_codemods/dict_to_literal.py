from typing import Union

import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to change dict(**args) to literal {...} constructs.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class DictConstructorToLiteral(CodeMod):
    DESCRIPTION: str = "Converts dict(**args) to literal {...} constructs."

    def leave_Call(
        self, node: cst.Call, updated_node: cst.Call
    ) -> Union[cst.Call, cst.Dict]:
        if m.matches(updated_node.func, m.Name("dict")) and all(
            map(lambda x: x.keyword is not None, updated_node.args)
        ):
            elements = [
                cst.DictElement(
                    key=cst.SimpleString(
                        '"' + arg.keyword.value.replace('"', '\\"') + '"'
                    ),
                    value=arg.value,
                )
                for arg in updated_node.args
            ]
            new_node = cst.Dict(elements)

            self.count += 1
            return new_node
        return updated_node


def main():
    runner(DictConstructorToLiteral)


if __name__ == "__main__":
    main()
