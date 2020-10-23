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
            # set(a for a in collection) => {a for a in collection}
            generator = cast(cst.GeneratorExp, updated_node.args[0].value)

            new_node = cst.SetComp(elt=generator.elt, for_in=generator.for_in)

            self.count += 1
            return new_node

        elif m.matches(
            updated_node,
            m.Call(
                func=m.Name("set"),
                args=[m.Arg(value=m.List(elements=[m.AtLeastN(n=1)]))],
            ),
        ):
            # set([1, 2, 3, ...]) => {1, 2, 3, ...}
            seq = cast(cst.List, updated_node.args[0].value)
            new_node = cst.Set(elements=seq.elements)

            self.count += 1
            return new_node

        return updated_node


def main():
    runner(SetConstructorToLiteral)


if __name__ == "__main__":
    main()
