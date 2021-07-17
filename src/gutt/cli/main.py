import inspect
import os
import re
from pathlib import Path
from types import FunctionType

import click
from gutt.parser import load_module_from_pyfile
from gutt.template import populate_testclass, populate_testfunc
from gutt.utils import (
    blacking,
    collect_classes_and_functions,
    expand_sys_path,
    isorting,
    load_module_by_name,
    makefile,
    qualname,
)

from ..code import CodeBlock, indent


class InvalidModuleName(Exception):
    pass


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    from gutt import __version__

    click.echo(f"Version: {__version__}")

    ctx.exit()


@click.command()
@click.pass_context
@click.option(
    "--version", is_flag=True, callback=print_version, expose_value=False, is_eager=True
)
@click.option(
    "--modname", "-m", help="Target module name for generating test templates"
)
@click.option(
    "--path",
    "-p",
    multiple=True,
    default=[os.getcwd()],
    help='Insert into "sys.path" to search modules, could assign with multiple values',
)
@click.option(
    "--exclude",
    "-e",
    help="Giving regex pattern to match the implementation to be excluded by its qualname",
)
@click.option(
    "--output",
    "-o",
    default="tests/_gutt",
    help="Output root directory for populating test files, default: tests/_gutt",
)
def main(ctx, modname, path, exclude, output):

    # TODO: ugly workaround

    if not (modname and isinstance(modname, str)):

        raise InvalidModuleName(f'got: "{modname}"')

    module = load_module_by_name(modname)

    ispkg = hasattr(module, "__path__")

    mod_impl_mappings = {}

    with expand_sys_path(*path):
        for obj in collect_classes_and_functions(module):

            obj_name = qualname(obj)
            if isinstance(exclude, str) and re.search(exclude, obj_name):
                print(f"Exclude {obj_name} since it matches with pattern: {exclude}")

                continue

            _modname = obj.__module__

            if _modname not in mod_impl_mappings:
                mod_impl_mappings[_modname] = []

            if obj not in mod_impl_mappings[_modname]:
                mod_impl_mappings[_modname].append(obj)
                print(f"Collect {obj_name}")

    for _modname, imps in mod_impl_mappings.items():

        if ispkg:
            _modname = re.sub(rf"^{modname}\.", "", _modname)
            pfx, name = _modname.rsplit(".", 1) if "." in _modname else ("", _modname)
            pfx = os.path.join(modname.replace(".", "_"), pfx.replace(".", "/"))
        else:
            name = _modname.replace(".", "_")
            pfx = ""

        filename = f"test_{name}.py"

        fullpath = os.path.join(output, pfx, filename)

        makefile(fullpath)

        _module = load_module_from_pyfile(f"tests_{name}", fullpath)

        try:
            source = inspect.getsource(_module)
            print(f"Load existing codes from {fullpath}")
        except OSError:
            source = ""

        blocks = CodeBlock.collect_from_source(source)

        implemented = {
            bk.name: i for i, bk in enumerate(blocks) if bk.kind in ("def", "class")
        }

        code_added = 0

        for obj in imps:
            fullname = qualname(obj)
            name = obj.__name__

            if isinstance(obj, FunctionType) and f"test_{name}" not in implemented:

                blocks.append(
                    CodeBlock(
                        raw=populate_testfunc(obj), name=f"test_{name}", kind="def"
                    )
                )

                code_added += 1

                print(f"Add test function for {fullname}")

            elif isinstance(obj, type):

                ut_name = f"Test{name}"

                if ut_name not in implemented:
                    blocks.append(
                        CodeBlock(
                            raw=populate_testclass(obj), name=ut_name, kind="class"
                        )
                    )

                    code_added += 1

                    print(f"Add test class for {fullname}")

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
                                or isinstance(
                                    v, (FunctionType, classmethod, staticmethod)
                                )
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

                            print(f"Add test function for method {k} of {fullname}")

                    if methods_to_add:

                        code = "\n".join([block.raw] + methods_to_add)

                        blocks[implemented[ut_name]] = CodeBlock(
                            raw=code, kind="class", name=ut_name
                        )

                        code_added += 1

        if code_added > 0:
            new_source = "\n".join([b.raw for b in blocks])
            formatted = isorting(blacking(new_source))

            makefile(fullpath, formatted, overwrite=True)
            print(f"Generate codes to {fullpath}")
        else:
            print("All test templates exist, skip code generation")

    output_root = Path(output)
    paths = {output_root}
    for path in output_root.glob("**/*.py"):
        if path.name == "__init__.py":
            continue

        parent = path.parent

        while parent > output_root:

            if not parent.joinpath("__init__.py").exists():
                paths.add(parent)

            parent = parent.parent

    for p in paths:
        makefile(os.path.join(str(p), "__init__.py"))
