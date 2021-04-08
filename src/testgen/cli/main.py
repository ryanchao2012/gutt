import inspect
import os
from types import FunctionType

import click
from testgen.parser import load_module_from_pyfile
from testgen.template import populate_testclass, populate_testfunc
from testgen.utils import (
    blacken,
    collect_classes_and_functions,
    expand_sys_path,
    makefile,
)

from ..code import CodeBlock, indent


class InvalidModuleName(Exception):
    pass


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    from testgen import __version__

    click.echo(f"Version: {__version__}")

    ctx.exit()


@click.command()
@click.pass_context
@click.option(
    "--version", is_flag=True, callback=print_version, expose_value=False, is_eager=True
)
@click.option("--module", "-m", help="Target module for generating test templates")
@click.option(
    "--path",
    "-p",
    multiple=True,
    default=[os.getcwd()],
    help='Insert into "sys.path" to search modules, could assign with multiple values',
)
@click.option(
    "--output",
    "-o",
    default="tests/testgen",
    help="Output root directory for populating test files, default: tests/testgen",
)
def main(ctx, module, path, output):

    # TODO: ugly workaround, very ugly

    if not (module and isinstance(module, str)):

        raise InvalidModuleName(f'got: "{module}"')

    mod_impl_mappings = {}

    with expand_sys_path(*path):
        for obj in collect_classes_and_functions(module):

            mod = obj.__module__

            if mod not in mod_impl_mappings:
                mod_impl_mappings[mod] = []

            if obj not in mod_impl_mappings[mod]:
                mod_impl_mappings[mod].append(obj)

    for mod, imps in mod_impl_mappings.items():

        pfx, name = mod.rsplit(".", 1)
        filename = f"test_{name}.py"
        fullpath = os.path.join(output, pfx.replace(".", "/"), filename)

        makefile(fullpath)

        module = load_module_from_pyfile(f"tests_{name}", fullpath)

        try:
            source = inspect.getsource(module)
        except OSError:
            source = ""

        blocks = CodeBlock.collect_from_source(source)

        implemented = {
            bk.name: i for i, bk in enumerate(blocks) if bk.kind in ("def", "class")
        }

        code_added = 0

        for obj in imps:

            name = obj.__name__

            if isinstance(obj, FunctionType) and f"test_{name}" not in implemented:

                blocks.append(
                    CodeBlock(
                        raw=populate_testfunc(obj), name=f"test_{name}", kind="def"
                    )
                )

                code_added += 1

            elif isinstance(obj, type):

                ut_name = f"Test{name}"

                if ut_name not in implemented:
                    blocks.append(
                        CodeBlock(
                            raw=populate_testclass(obj), name=ut_name, kind="class"
                        )
                    )

                    code_added += 1

                else:
                    block = blocks[implemented[ut_name]]

                    methods_implemented = {
                        bk.name: i
                        for i, bk in enumerate(block.children)
                        if bk.kind in ("def",)
                    }
                    methods_to_add = []

                    for k, v in obj.__dict__.items():
                        method_name = f"test_{k}"
                        if (
                            (
                                inspect.ismethod(v)
                                or isinstance(v, (FunctionType, classmethod))
                            )
                            and (not k.startswith("__"))
                            and (method_name not in methods_implemented)
                        ):

                            code = "\n".join(
                                [
                                    indent(f"def {method_name}(self):", level=1),
                                    indent("pass", level=2),
                                    "",
                                ]
                            )

                            methods_to_add.append(code)

                    if methods_to_add:

                        code = "\n".join([block.raw] + methods_to_add)

                        blocks[implemented[ut_name]] = CodeBlock(
                            raw=code, kind="class", name=ut_name
                        )

                        code_added += 1

        if code_added > 0:
            new_source = "\n".join([b.raw for b in blocks])
            formatted = blacken(new_source)

            makefile(fullpath, formatted, overwrite=True)

    for dirpath, _, _ in os.walk(output.split(os.path.sep)[0]):
        makefile(os.path.join(dirpath, "__init__.py"))
