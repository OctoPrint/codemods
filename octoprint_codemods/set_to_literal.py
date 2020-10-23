from typing import Union, cast

import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to change set(*args) to literal {...} constructs where possible.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class SetConstructorToLiteral(CodeMod):
    DESCRIPTION: str = "Converts set(*args) to literal {...} constructs."

    def leave_Call(
        self, node: cst.Call, updated_node: cst.Call
    ) -> Union[cst.Call, cst.Set, cst.SetComp]:
        if m.matches(
            updated_node, m.Call(func=m.Name("set"), args=[m.Arg(value=m.GeneratorExp())])
        ):
            # generator
            generator = cast(cst.GeneratorExp, updated_node.args[0].value)

            new_node = cst.SetComp(elt=generator.elt, for_in=generator.for_in)

            self.count += 1
            return new_node

        elif m.matches(updated_node, m.Call(func=m.Name("set"), args=[m.AtLeastN(n=2)])):
            # simple set
            elements = [cst.Element(value=arg.value) for arg in updated_node.args]
            new_node = cst.Set(elements)

            self.count += 1
            return new_node

        return updated_node


def main():
    runner(SetConstructorToLiteral)


if __name__ == "__main__":
    main()
