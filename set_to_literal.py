from typing import Union

import libcst as cst
import libcst.matchers as m

from util import CodeMod, runner

"""
libcst based transformer to change set(*args) to literal {...} constructs where possible.

Tool call heavily based on https://github.com/seatgeek/tornado-async-transformer

Whitespace for alignment is not properly used in all cases yet, patches welcome.
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"


class SetConstructorToLiteral(CodeMod):
	DESCRIPTION: str = "Converts set(*args) to literal {...} constructs."

	def __init__(self) -> None:
		super().__init__()
		self.arg_stack = []

	def visit_Arg(self, node: cst.Arg) -> bool:
		self.arg_stack.append(node)
		return True

	def leave_Arg(self, node: cst.Arg, updated_node: cst.Arg) -> cst.Arg:
		self.arg_stack.pop()
		return updated_node

	def leave_Call(self, node: cst.Call, updated_node: cst.Call) -> Union[cst.Call, cst.Set, cst.SetComp]:
		if m.matches(updated_node.func, m.Name("set")) and updated_node.args:
			if len(updated_node.args) == 1 and isinstance(updated_node.args[0].value, cst.GeneratorExp):
				# generator
				generator = updated_node.args[0].value

				new_node = cst.SetComp(elt=generator.elt,
				                       for_in=generator.for_in)

				self.count += 1
				return new_node

			elif len(updated_node.args) > 1:
				# simple set
				elements = []
				for arg in updated_node.args:
					alignment = 0
					if self.arg_stack:
						# inside argument, so check whitespace from that
						outer_arg = self.arg_stack[-1]
						if isinstance(outer_arg.equal, cst.AssignEqual):
							arg_align = '='
							if isinstance(outer_arg.equal.whitespace_before, cst.SimpleWhitespace):
								arg_align = outer_arg.equal.whitespace_before.value + arg_align
							if isinstance(outer_arg.equal.whitespace_after, cst.SimpleWhitespace):
								arg_align += outer_arg.equal.whitespace_after.value
							alignment = len(arg_align)

					comma = None
					if arg.comma is not None:
						if isinstance(arg.comma, cst.Comma):
							if isinstance(arg.comma.whitespace_after, cst.ParenthesizedWhitespace):
								whitespace = arg.comma.whitespace_after
								last_line = whitespace.last_line
								last_line_value = last_line.value
								if all(map(lambda x: x == ' ', last_line_value)):
									last_line_value = last_line_value[:-len("dict") - alignment]
								last_line = last_line.with_changes(value=last_line_value)
								whitespace = whitespace.with_changes(last_line=last_line)
								comma = arg.comma.with_changes(whitespace_after=whitespace)
							else:
								comma = arg.comma
						else:
							comma = arg.comma

					elements.append(cst.Element(value=arg.value,
					                            comma=comma))

				new_node = cst.Set(elements)

				self.count += 1
				return new_node

		return updated_node

if __name__ == "__main__":
	runner(SetConstructorToLiteral)
