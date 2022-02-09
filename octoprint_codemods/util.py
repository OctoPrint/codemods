import argparse
import difflib
import os
import re
import sys
from abc import ABCMeta
from contextlib import ExitStack
from typing import Callable, ClassVar, Iterable, List, Optional, Tuple, Type, Union, cast

import libcst as cst
from libcst._batched_visitor import _get_visitor_methods, _VisitorMethodCollection
from libcst.metadata import PositionProvider


class BatchedCSTTranformer(cst.CSTTransformer):
    """
    Internal visitor class to perform batched traversal over a tree.
    """

    visitor_methods: _VisitorMethodCollection

    def __init__(
        self,
        visitor_methods: _VisitorMethodCollection,
    ) -> None:
        super().__init__()
        self.visitor_methods = visitor_methods

    def on_visit(self, node: cst.CSTNode) -> bool:
        """
        Call appropriate visit methods on node before visiting children.
        """
        type_name = type(node).__name__

        for v in self.visitor_methods.get(f"visit_{type_name}", []):
            v(node)

        return True

    def on_leave(
        self, original_node: cst.CSTNode, updated_node: cst.CSTNode
    ) -> Union[cst.CSTNodeT, cst.RemovalSentinel]:
        """
        Call appropriate leave methods on node after visiting children.
        """
        type_name = type(original_node).__name__

        for v in self.visitor_methods.get(f"leave_{type_name}", []):
            updated_node = v(original_node, updated_node)

        return updated_node

    def on_visit_attribute(self, node: "cst.CSTNode", attribute: str) -> None:
        """
        Call appropriate visit attribute methods on node before visiting
        attribute's children.
        """
        type_name = type(node).__name__

        for v in self.visitor_methods.get(f"visit_{type_name}_{attribute}", []):
            v(node)

    def on_leave_attribute(self, original_node: "cst.CSTNode", attribute: str) -> None:
        """
        Call appropriate leave attribute methods on node after visiting
        attribute's children.
        """
        type_name = type(original_node).__name__

        for v in self.visitor_methods.get(f"leave_{type_name}_{attribute}", []):
            v(original_node)


def transform_batched(
    node: cst.CSTNodeT,
    batchable_transformers: Iterable[
        Union[cst.BatchableCSTVisitor, BatchedCSTTranformer]
    ],
) -> cst.CSTNodeT:
    transformer_methods = _get_visitor_methods(batchable_transformers)
    batched_transformer = BatchedCSTTranformer(transformer_methods)
    return cast(cst.CSTNodeT, node.visit(batched_transformer))


class CodeInspectorMeta(ABCMeta):
    registry = {}

    def __new__(cls, name: str, bases: Tuple[Type, ...], attrs: dict) -> Type:
        new_cls = super().__new__(cls, name, bases, attrs)
        command = attrs.get("COMMAND")
        if command:
            CodeInspectorMeta.registry[command] = new_cls
        return new_cls

    @classmethod
    def lookup(cls, command: str) -> Type:
        return cls.registry.get(command)

    @classmethod
    def all(cls) -> List[str]:
        return list(cls.registry.keys())


class CodeInspector(cst.MetadataDependent, metaclass=CodeInspectorMeta):
    METADATA_DEPENDENCIES = (PositionProvider,)
    COMMAND: ClassVar[str]
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


class CodeMod(CodeInspector, cst.CSTTransformer, cst.BatchableCSTVisitor):
    pass


class CodeCheck(CodeInspector, cst.CSTVisitor, cst.BatchableCSTVisitor):
    pass


class TransformError(Exception):
    """Error raise while encountering a known error while attempting to transform the tree"""


def process_file(
    visitors: Iterable[Union[CodeMod, CodeCheck]],
    filename: str,
    write_before: bool = False,
    write_after: bool = False,
    write_result: bool = True,
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

    mod = False
    for v in visitors:
        v.reset(filename=filename, module=module)
        mod = mod or isinstance(v, CodeMod)

    try:
        with ExitStack() as stack:
            # Resolve dependencies of visitors
            for v in visitors:
                stack.enter_context(v.resolve(source_tree))

            visited_tree = transform_batched(source_tree.module, visitors)

    except TransformError as e:
        print("{} failed transform: {}".format(filename, str(e)))
        return

    if mod:
        if v.count:
            if write_result:
                with open(filename, "w") as python_file:
                    python_file.write(visited_tree.code)

        if write_after:
            with open(filename + ".cst.after", "w") as cst_file:
                cst_file.write(str(visited_tree))

    return visited_tree.code


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
        for root, _, filenames in os.walk(base):
            full_filenames = (f"{root}/{filename}" for filename in filenames)
            python_files += [
                full_filename
                for full_filename in full_filenames
                if is_python_file(full_filename)
                and not is_ignored(full_filename, ignored)
            ]
        return tuple(python_files)

    return tuple()


def parse_args(
    description: str, add_parser_args: Optional[Callable] = None
) -> argparse.Namespace:
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
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode: first path is input file, second path is file with expected output.",
    )
    if add_parser_args:
        add_parser_args(parser)
    return parser.parse_args()


def test_runner(
    mods: Iterable[CodeMod], input_path: str, expected_path: str, diff: bool = True
) -> bool:
    with open(expected_path, "r") as python_file:
        expected = python_file.read()
    actual = process_file(
        mods,
        input_path,
        write_result=False,
    )

    if actual != expected:
        if diff:
            to_lines = lambda x: list(map(lambda l: l + "\n", x.split("\n")))

            expected_lines = to_lines(expected)
            actual_lines = to_lines(actual)

            diff = difflib.unified_diff(
                expected_lines,
                actual_lines,
                fromfile=expected_path,
                tofile="generated output",
            )
            sys.stderr.writelines(diff)
        return False
    return True


def run(
    inspectors: Iterable[Union[CodeMod, CodeCheck]], args: argparse.Namespace, output: str
) -> int:
    if args.test:
        # test mode
        if len(args.bases) < 2:
            print("Usage: <codemod> --test <input file> <file with expected output>")
            sys.exit(-1)

        input_file = args.bases[0]
        output_file = args.bases[1]

        if test_runner(inspectors, input_file, output_file):
            print("✨ Test successful, contents identical")
            sys.exit(0)
        else:
            print("❌ Contents differ")
            sys.exit(-1)

    # production mode
    python_files: List[str] = []
    for base in args.bases:
        python_files += collect_files(base, ignored=args.ignore)

    count = 0
    for python_file in python_files:
        process_file(
            inspectors,
            python_file,
            write_before=args.before,
            write_after=args.after,
            write_result=not args.dryrun,
        )

        file_count = sum([inspector.count for inspector in inspectors])
        if output and (args.verbose or file_count):
            print(output.format(file=python_file.replace("\\", "/"), count=file_count))
        count += file_count

    sys.exit(count)


def _load_all():
    import importlib
    import pkgutil

    path = os.path.dirname(__file__)
    for _, module_name, _ in pkgutil.walk_packages(
        [
            path,
        ]
    ):
        importlib.import_module(f"octoprint_codemods.{module_name}")


def batch_runner(
    output: Union[str, None] = "{file}: {count} replacements done",
) -> None:
    _load_all()

    def batch_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--check",
            "--mod",
            type=str,
            default=[],
            action="append",
            help="Names of checks/mods to run",
        )

    args = parse_args("multi_runner", add_parser_args=batch_args)

    classes = []
    for name in args.check:
        cls = CodeInspectorMeta.lookup(name)
        if cls:
            classes.append(cls)
        else:
            print(f"No check or mod found for {name}, skipping")

    inspectors = []
    for cls in classes:
        inspector = cls(args)

        if isinstance(inspector, CodeMod):
            inspector = cast(CodeMod, inspector)
        elif isinstance(inspector, CodeCheck):
            inspector = cast(CodeCheck, inspector)
        else:
            continue

        inspectors.append(inspector)

    run(inspectors, args, output)


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

    run(
        [
            inspector,
        ],
        args,
        output,
    )
