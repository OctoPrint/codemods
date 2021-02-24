from typing import Union, cast

import libcst as cst
import libcst.matchers as m

from .util import CodeMod, runner

"""
libcst based transformer to convert 'r"abc".encode("utf-8")' to 'rb"abc"' and '"abc".encode("utf-8")' to '"abc".encode()'.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class StringEncoding(CodeMod):
    DESCRIPTION: str = """Converts 'r"abc".encode("utf-8")' to 'rb"abc"' and '"abc".encode("utf-8")' to '"abc".encode()'."""

    DEFAULT_ENCODING: str = "utf-8"

    def leave_Call(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> Union[cst.Call, cst.SimpleString]:
        if m.matches(
            updated_node,
            m.Call(
                func=m.Attribute(
                    value=m.SimpleString(),
                    attr=m.Name("encode"),
                ),
                args=[m.ZeroOrOne(m.Arg(value=m.SimpleString()))],
            ),
        ):
            string = cast(cst.SimpleString, updated_node.func.value)
            encoding = self.DEFAULT_ENCODING
            if updated_node.args:
                encoding = cast(
                    cst.SimpleString, updated_node.args[0].value
                ).evaluated_value

            if encoding == self.DEFAULT_ENCODING:
                if all(ord(c) < 128 for c in string.evaluated_value):
                    # ASCII only string, prefix b and be done
                    new_string = (
                        string.prefix
                        + "b"
                        + string.quote
                        + string.raw_value
                        + string.quote
                    )

                    self._report_node(original_node)
                    updated_node = string.with_changes(value=new_string)
                    self.count += 1

                elif updated_node.args:
                    # utf-8 defined, that's redundant
                    self._report_node(original_node)
                    updated_node = updated_node.with_changes(args=[])
                    self.count += 1

        return updated_node


def main():
    runner(StringEncoding)


if __name__ == "__main__":
    main()
