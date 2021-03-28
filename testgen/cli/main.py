import inspect
import os
from types import FunctionType

import click
from testgen.utils import (
    blacken,
    collect_classes_and_functions_from_module,
    load_module_from_pyfile,
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
    "--output",
    "-o",
    default="tests/testgen",
    help="Output directory for populating test files, default: tests/testgen",
)
def main(ctx, module, output):

    if not (module and isinstance(module, str)):

        raise InvalidModuleName(f'got: "{module}"')

    mappings = {}
    for obj in collect_classes_and_functions_from_module(module):

        mod = obj.__module__

        if mod not in mappings:
            mappings[mod] = []

        if obj not in mappings[mod]:
            mappings[mod].append(obj)

    for mod, imps in mappings.items():

        pfx, name = mod.rsplit(".", 1)
        filename = f"test_{name}.py"
        fullpath = os.path.join(output, pfx.replace(".", "/"), filename)

        if not os.path.isfile(fullpath):
            dirname = os.path.dirname(fullpath)

            if not os.path.isdir(dirname):
                os.makedirs(dirname)

            with open(fullpath, "w"):
                pass

        module = load_module_from_pyfile(f"tests_{name}", fullpath)

        try:
            source = inspect.getsource(module)
        except OSError:
            source = ""

        skeletons_to_add = []

        for obj in imps:

            name = obj.__name__

            if isinstance(obj, FunctionType) and f"\ndef test_{name}(" not in source:
                # f"\ndef test_{name}():\n{' '*4}from {mod} import {name}\n{' '*4}assert {name}\n"

                skeletons_to_add.append(populate_testfunc(obj))

            elif isinstance(obj, type) and f"\nclass Test{name}:" not in source:
                skeletons_to_add.append(populate_testclass(obj))

        if skeletons_to_add:
            new_source = "\n".join([source] + skeletons_to_add)

            formatted = blacken(new_source)

            with open(fullpath, "w") as f:
                f.write(formatted)
