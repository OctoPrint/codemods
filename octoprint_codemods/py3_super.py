import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to change 'super(cls, self).member' to 'super().member'.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class Py3Super(CodeMod):
    DESCRIPTION: str = "Converts 'super(cls, self).member' to 'super().member'."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.classes = []

    def reset(self, *args, **kwargs) -> None:
        self.classes = []
        return super().reset(*args, **kwargs)

    def visit_ClassDef(self, node: cst.ClassDef) -> cst.ClassDef:
        self.classes.append(node.name.value)
        return super().visit_ClassDef(node)

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        self.classes.pop()
        return super().leave_ClassDef(original_node, updated_node)

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if self.classes:
            current_class = self.classes[-1]
            if m.matches(
                updated_node,
                m.Call(
                    func=m.Name("super"),
                    args=[
                        m.Arg(value=m.Name(current_class)),
                        m.Arg(value=m.Name("self")),
                    ],
                ),
            ):
                updated_node = updated_node.with_changes(args=[])
                self._report_node(original_node)
                self.count += 1
        return updated_node


def main():
    runner(Py3Super)


if __name__ == "__main__":
    main()
