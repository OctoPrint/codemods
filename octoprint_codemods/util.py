import argparse
import os
import re
import sys
from typing import Callable, ClassVar, List, Tuple, Type, Union, cast

import libcst as cst
from libcst import MetadataDependent
from libcst.metadata import PositionProvider


class CodeInspector(MetadataDependent):
    METADATA_DEPENDENCIES = (PositionProvider,)
    DESCRIPTION: ClassVar[str]

    args: argparse.Namespace
    count: int
    filename: str
    module: cst.Module

    @classmethod
    def add_parser_args(cls, parser):
        pass

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.reset()

    def reset(
        self,
        filename: Union[str, None] = None,
        module: Union[cst.Module, None] = None,
    ) -> None:
        self.count = 0
        self.filename = filename.replace("\\", "/") if filename else filename
        self.module = module

    def _report_node(
        self,
        node: cst.CSTNode,
        output: str = "{filename}:{pos.line}:{pos.column}:\n{code}",
    ) -> None:
        if self.get_metadata(PositionProvider, node):
            pos = self.get_metadata(PositionProvider, node).start
            print(
                output.format(
                    node=node,
                    pos=pos,
                    code="\n".join(
                        map(
                            lambda x: "  " + x,
                            (
                                self.module.code_for_node(node) if self.module else ""
                            ).split("\n"),
                        )
                    ),
                    filename=self.filename if self.filename else "",
                )
            )


class CodeMod(CodeInspector, cst.CSTTransformer):
    pass


class CodeCheck(CodeInspector, cst.CSTVisitor):
    pass


class TransformError(Exception):
    """Error raise while encountering a known error while attempting to transform the tree"""


def process_file(
    visitor: Union[CodeMod, CodeCheck],
    filename: str,
    write_before: bool,
    write_after: bool,
    write_result: bool,
) -> None:
    try:
        with open(filename, "r") as python_file:
            python_source = python_file.read()
    except Exception as exc:
        print("Could not read file {}, skipping: {}".format(filename, str(exc)))

    try:
        module = cst.parse_module(python_source)
        source_tree = cst.MetadataWrapper(module)
    except Exception as e:
        print("{} failed parse: {}".format(filename, str(e)))
        return

    if write_before:
        with open(filename + ".cst.before", "w") as cst_file:
            cst_file.write(str(source_tree))

    visitor.reset(filename=filename, module=module)
    try:
        visited_tree = source_tree.visit(visitor)
    except TransformError as e:
        print("{} failed transform: {}".format(filename, str(e)))
        return

    if isinstance(visitor, CodeMod):
        if visitor.count:
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
                if is_python_file(full_filename)
                and not is_ignored(full_filename, ignored)
            ]
        return tuple(python_files)

    return tuple()


def parse_args(description: str, add_parser_args: Callable) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "bases",
        type=str,
        nargs="+",
        help="Files and directories (recursive) including python files to be modified.",
    )
    parser.add_argument(
        "--before",
        action="store_true",
        help="Write the CST of the original file to file.cst.before",
    )
    parser.add_argument(
        "--after",
        action="store_true",
        help="Write the CST of the transformed file to file.cst.after",
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Only perform a dry run without writing back the transformed file",
    )
    parser.add_argument(
        "--ignore",
        type=str,
        default=[],
        action="append",
        help="Paths to ignore, add multiple as required",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Generate output for all processed files, not juse for those with replacements",
    )
    add_parser_args(parser)
    return parser.parse_args()


def runner(
    cls: Type[CodeInspector],
    output: Union[str, None] = "{file}: {count} replacements done",
) -> None:
    args = parse_args(cls.DESCRIPTION, cls.add_parser_args)

    inspector = cls(args)

    if isinstance(inspector, CodeMod):
        inspector = cast(CodeMod, inspector)
    elif isinstance(inspector, CodeCheck):
        inspector = cast(CodeCheck, inspector)
    else:
        print("Unknown inspector type: {}".format(inspector))
        sys.exit(-1)

    python_files: List[str] = []
    for base in args.bases:
        python_files += collect_files(base, ignored=args.ignore)

    count = 0
    for python_file in python_files:
        process_file(
            inspector,
            python_file,
            write_before=args.before,
            write_after=args.after,
            write_result=not args.dryrun,
        )
        if output and (args.verbose or inspector.count):
            print(
                output.format(file=python_file.replace("\\", "/"), count=inspector.count)
            )
        count += inspector.count

    sys.exit(count)
