import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to change 'class Foo(object):' to 'class Foo:'.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class Py3ClassInheritance(CodeMod):
    DESCRIPTION: str = "Converts 'class Foo(object):' to 'class Foo:'."

    def leave_ClassDef(
        self, node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        filtered_bases = list(
            filter(
                lambda arg: not m.matches(arg, m.Arg(value=m.Name("object"))),
                updated_node.bases,
            )
        )
        if len(filtered_bases) != len(updated_node.bases):
            self._report_node(node)
            self.count += 1

            lpar = updated_node.lpar
            rpar = updated_node.rpar
            if len(filtered_bases) == 0 and len(updated_node.keywords) == 0:
                lpar = rpar = None

            return updated_node.with_changes(bases=filtered_bases, lpar=lpar, rpar=rpar)
        return updated_node


def main():
    runner(Py3ClassInheritance)


if __name__ == "__main__":
    main()
