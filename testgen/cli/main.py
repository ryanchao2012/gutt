import inspect
import os
from types import FunctionType

import click
from testgen.utils import (
    blacken,
    collect_classes_and_functions,
    expand_sys_path,
    load_module_from_pyfile,
    makefile,
    populate_testclass,
    populate_testfunc,
)


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

        codes_to_add = []

        for obj in imps:

            name = obj.__name__

            if isinstance(obj, FunctionType) and f"\ndef test_{name}(" not in source:

                codes_to_add.append(populate_testfunc(obj))

            elif isinstance(obj, type) and f"\nclass Test{name}:" not in source:
                codes_to_add.append(populate_testclass(obj))

        if codes_to_add:
            new_source = "\n".join([source] + codes_to_add)

            formatted = blacken(new_source)

            makefile(fullpath, formatted, overwrite=True)

    for dirpath, _, _ in os.walk(output):
        makefile(os.path.join(dirpath, "__init__.py"))
