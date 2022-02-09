import libcst as cst
import libcst.matchers as m

from .util import CodeCheck, runner

"""
libcst based visitor to check for 'from past.builtins import ...' imports
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class CheckPastBuiltinsImports(CodeCheck):
    COMMAND: str = "detect_past_builtins_imports"
    DESCRIPTION: str = "Detects 'from past... import ...', 'import past...'"

    def leave_Import(self, node: cst.Import) -> None:
        if m.matches(
            node,
            m.Import(
                names=[
                    m.ZeroOrMore(),
                    m.OneOf(
                        m.ImportAlias(name=m.Name("past")),
                        m.ImportAlias(name=m.Attribute(value=m.Name("past"))),
                    ),
                    m.ZeroOrMore(),
                ]
            ),
        ):
            self._report_node(node)
            self.count += 1

    def leave_ImportFrom(self, node: cst.ImportFrom) -> None:
        if m.matches(
            node.module,
            m.OneOf(m.Name("past"), m.Attribute(value=m.Name("past"))),
        ):
            self._report_node(node)
            self.count += 1


def main():
    runner(CheckPastBuiltinsImports, output=None)


if __name__ == "__main__":
    main()
