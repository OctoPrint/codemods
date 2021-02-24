from typing import Union, cast

import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to convert 'dict((x.a, x.b) for x in y)' to '{x.a: x.b for x in y}'.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class DictComprehensionToLiteral(CodeMod):
    DESCRIPTION: str = (
        "Converts 'dict((x.a, x.b) for x in y)' to '{x.a: x.b for x in y}'."
    )

    def leave_Call(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> Union[cst.Call, cst.DictComp]:
        if m.matches(
            updated_node,
            m.Call(
                func=m.Name("dict"),
                args=[
                    m.Arg(
                        m.GeneratorExp(
                            elt=m.Tuple(elements=[m.DoNotCare(), m.DoNotCare()])
                        )
                    )
                ],
            ),
        ):
            exp = cast(cst.GeneratorExp, updated_node.args[0].value)
            t = cast(cst.Tuple, exp.elt)
            key = t.elements[0].value
            value = t.elements[1].value

            self.count += 1
            return cst.DictComp(key=key, value=value, for_in=exp.for_in)

        return updated_node


def main():
    runner(DictComprehensionToLiteral)


if __name__ == "__main__":
    main()
