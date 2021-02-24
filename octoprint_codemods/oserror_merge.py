from typing import Union

import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to change 'EnvironmentError' and friends to 'OSError'.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class OsErrorMerge(CodeMod):
    DESCRIPTION: str = "Converts 'EnvironmentError' and friends to 'OSError'."

    TO_REPLACE = m.OneOf(
        m.Name("EnvironmentError"),
        m.Name("IOError"),
        m.Name("WindowsError"),
        m.Attribute(value=m.Name("socket"), attr=m.Name("error")),
        m.Attribute(value=m.Name("select"), attr=m.Name("error")),
        m.Attribute(value=m.Name("mmap"), attr=m.Name("error")),
    )
    REPLACEMENT = cst.Name("OSError")

    def replace_tuple(self, node: cst.Tuple) -> Union[cst.Tuple, cst.Name]:
        elements = node.elements
        filtered = list(
            [x for x in elements if not m.matches(x, m.Element(value=self.TO_REPLACE))]
        )
        if filtered:
            node = node.with_changes(
                elements=filtered + [cst.Element(self.REPLACEMENT.deep_clone())]
            )
        else:
            node = self.REPLACEMENT.deep_clone()
        return node

    def leave_ExceptHandler(
        self, original_node: cst.ExceptHandler, updated_node: cst.ExceptHandler
    ) -> cst.ExceptHandler:
        if m.matches(
            updated_node.type,
            m.Tuple(
                elements=[
                    m.ZeroOrMore(),
                    m.Element(value=self.TO_REPLACE),
                    m.ZeroOrMore(),
                ]
            ),
        ):
            self._report_node(original_node)
            self.count += 1
            updated_node = updated_node.with_changes(
                type=self.replace_tuple(updated_node.type)
            )
        elif m.matches(updated_node.type, self.TO_REPLACE):
            self._report_node(original_node)
            self.count += 1
            updated_node = updated_node.with_changes(type=self.REPLACEMENT.deep_clone())
        return updated_node


def main():
    runner(OsErrorMerge)


if __name__ == "__main__":
    main()
