import os
import re
from collections import OrderedDict
from pathlib import Path

import click
from asttrs import ClassDef, FunctionDef, Module
from gutt.model import Code, ModuleIO
from gutt.template import Template
from gutt.utils import expand_sys_path, makefile


class InvalidModule(Exception):
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
    "--version",
    "-V",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
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
    help="Giving regex pattern to match the implementation to be excluded by its qualname.",
)
@click.option(
    "--output",
    "-o",
    default="tests/_gutt",
    help='Output root directory for populating test files, default: "tests/_gutt".',
)
@click.option(
    "--template",
    "-t",
    # default="tests/_gutt",
    # help='Output root directory for populating test files, default: "tests/_gutt".',
)
def main(ctx, modname, path, exclude, output, template):

    with expand_sys_path(*path):
        module: ModuleIO = ModuleIO.from_name(modname, output)

        if module is None:
            raise InvalidModule(modname)

        for mod in module.submodules:

            try:
                src_mod = Module.from_file(mod.src)

            except Exception as error:
                # TODO: warning
                print("!!!", type(error), error, mod.src)
                continue

            # TODO: exclude
            src_codes = OrderedDict(
                (f"{mod.name}.{el.name}", Code(module=mod, ast=el))
                for el in src_mod.body
                if isinstance(el, (FunctionDef, ClassDef))
            )

            if len(src_codes) == 0:
                continue

            try:
                test_mod = Module.from_file(mod.dst)

            except FileNotFoundError:
                test_mod = Module()

            except Exception as error:
                # TODO: warning
                print("!!!", type(error), error, mod.dst)
                continue

            test_codes = OrderedDict()

            for i, el in enumerate(test_mod.body):
                if isinstance(el, (ClassDef, FunctionDef)):
                    test_pfx = (
                        Template.function_layout.prefix
                        if isinstance(el, FunctionDef)
                        else Template.class_layout.prefix
                    )

                    org_name = re.sub(rf"^{test_pfx}(.+)", r"\1", el.name)
                    key = f"{mod.name}.{org_name}"

                else:
                    key = f"#{i}"

                test_codes.update({key: Code(module=mod, ast=el)})

            body = []

            for key, tcode in test_codes.items():

                if key in src_codes:

                    scode = src_codes.pop(key)

                    if isinstance(scode, ClassDef):
                        # TODO: check the differences
                        # tcode = ...
                        pass

                body.append(tcode.ast)

            for key, scode in src_codes.items():

                Layout = (
                    Template.function_layout
                    if isinstance(scode.ast, FunctionDef)
                    else Template.class_layout
                )

                # TODO: append imp to output module body with defined template
                body.append(Layout(scode).build())

            test_mod = Module(body=body)

            print("#", mod.dst)
            # test_mod.show()
            makefile(mod.dst)
            test_mod.to_file(mod.dst)

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


def _echo_collect(name: str, i: int = 1):
    click.echo("\033[K", nl=False)
    click.secho(f"collecting {i} item: ", nl=False, fg="bright_white")
    click.secho(f"{name}\r", nl=False, fg="bright_cyan")
