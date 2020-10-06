import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Union
import argparse

import libcst as cst
from libcst import CSTVisitorT
import libcst.matchers as m

"""
libcst based transformer to change dict(**args) to literal {...} constructs.

Tool call heavily based on https://github.com/seatgeek/tornado-async-transformer
"""

__author__ = "Gina Häußge <gina@octoprint.org>"
__license__ = "MIT"

class DictConstructorToLiteral(cst.CSTTransformer):
	DESCRIPTION: str = "Converts dict(**args) to literal {...} constructs."

	def __init__(self) -> None:
		super().__init__()
		self.arg_stack = []
		self.count = 0

	def visit_Arg(self, node: cst.Arg) -> bool:
		self.arg_stack.append(node)
		return True
	
	def leave_Arg(self, node: cst.Arg, updated_node: cst.Arg) -> cst.Arg:
		self.arg_stack.pop()
		return updated_node

	def leave_Call(self, node: cst.Call, updated_node: cst.Call) -> Union[cst.Call, cst.Dict]:
		if m.matches(updated_node.func, m.Name("dict")) and all(map(lambda x: x.keyword is not None, updated_node.args)):
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
								last_line_value = last_line_value[:-len("dict")-alignment]
							last_line = last_line.with_changes(value=last_line_value)
							whitespace = whitespace.with_changes(last_line=last_line)
							comma = arg.comma.with_changes(whitespace_after=whitespace)
						else:
							comma = arg.comma
					else:
						comma = arg.comma
				
				elements.append(cst.DictElement(key=cst.SimpleString('"' + arg.keyword.value.replace('"', '\\"') + '"'), 
				                                value=arg.value, 
				                                comma=comma))

			self.count += 1
			new_node = cst.Dict(elements)
			return new_node
		return updated_node


class TransformError(Exception):
	"""Error raise while encountering a known error while attempting to transform the tree"""


def transform_file(visitor: CSTVisitorT, filename: str, write_before: bool, write_after: bool, write_result: bool) -> None:
    with open(filename, "r") as python_file:
        python_source = python_file.read()

    try:
        source_tree = cst.parse_module(python_source)
    except Exception as e:
        print("{} failed parse: {}".format(filename, str(e)))
        return

    if write_before:
        with open(filename + ".cst.before", "w") as cst_file:
            cst_file.write(str(source_tree))

    try:
        visited_tree = source_tree.visit(visitor)
    except TransformError as e:
        print("{} failed transform: {}".format(filename, str(e)))
        return

    if not visited_tree.deep_equals(source_tree):
        if write_result:
            with open(filename, "w") as python_file:
                python_file.write(visited_tree.code)

    if write_after:
        with open(filename + ".cst.after", "w") as cst_file:
            cst_file.write(str(visited_tree))


def collect_files(base: str, ignored: List[str]) -> Tuple[str, ...]:
    """
    Collect all python files under a base directory.
    """

    def is_python_file(path: str) -> bool:
        return bool(os.path.isfile(path) and re.search(r"\.pyi?$", path))

    def is_ignored(path: str, ignored: List[str]) -> bool:
        path = path.replace("\\", "/")
        return any(map(lambda x: path.startswith(x), ignored))

    if is_python_file(base) and not is_ignored(base, ignored):
        return (base,)
    
    if os.path.isdir(base):
        python_files: List[str] = []
        for root, dirs, filenames in os.walk(base):
            full_filenames = (f"{root}/{filename}" for filename in filenames)
            python_files += [
                full_filename
                for full_filename in full_filenames
                if is_python_file(full_filename) and not is_ignored(full_filename, ignored)
            ]
        return tuple(python_files)

    return tuple()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Codemod for converting dict(...) to {...}"
    )
    parser.add_argument(
        "bases",
        type=str,
        nargs="+",
        help="Files and directories (recursive) including python files to be modified.",
    )
    parser.add_argument(
        "--before",
        action="store_true",
        help="Write the CST of the original file to file.cst.before"
    )
    parser.add_argument(
        "--after",
        action="store_true",
        help="Write the CST of the transformed file to file.cst.after"
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Only perform a dry run without writing back the transformed file"
    )
    parser.add_argument(
        "--ignore",
        type=str,
        default=[],
        action="append",
        help="Paths to ignore, add multiple as required"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    python_files: List[str] = []
    for base in args.bases:
        python_files += collect_files(base, ignored=args.ignore)

    for python_file in python_files:
        print("Processing {}... ".format(python_file.replace("\\", "/")), end='')
        transformer = DictConstructorToLiteral()
        transform_file(transformer,
                       python_file, 
                       write_before=args.before, 
                       write_after=args.after, 
                       write_result=not args.dryrun)
        print("{} replacements done".format(transformer.count))


if __name__ == "__main__":
    main()
