import inspect
import os
import re
import time
from pathlib import Path
from types import FunctionType, ModuleType

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


class InvalidModule(Exception):
    pass


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    from gutt import __version__

    click.echo(f"Version: {__version__}")

    ctx.exit()


def collect_items_from_module(module: ModuleType, exclude=None, sleep_interval=0.01):
    mod_impl_mappings = {}
    items = 0
    should_nl = True

    for obj in collect_classes_and_functions(module):

        obj_name = qualname(obj)
        if isinstance(exclude, str) and re.search(exclude, obj_name):
            if should_nl:
                click.echo()
                should_nl = False
            click.secho("excluding ", nl=False, fg="bright_white")
            click.secho(obj_name, fg="bright_black")

            continue

        _modname = obj.__module__

        if _modname not in mod_impl_mappings:
            mod_impl_mappings[_modname] = []

        if obj not in mod_impl_mappings[_modname]:
            items += 1
            mod_impl_mappings[_modname].append(obj)
            click.secho(f"collecting {items} items: ", nl=False, fg="bright_white")
            click.secho(f"{obj_name}\r", nl=False, fg="bright_cyan")
            time.sleep(sleep_interval)
            should_nl = True

    click.echo()

    return mod_impl_mappings


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

    try:
        module = load_module_by_name(modname)
    except Exception:
        raise InvalidModule(f'got: "{modname}"')

    ispkg = hasattr(module, "__path__")

    with expand_sys_path(*path):
        mod_impl_mappings = collect_items_from_module(module, exclude=exclude)

    for mod, imps in mod_impl_mappings.items():

        if ispkg:
            mod = re.sub(rf"^{modname}\.", "", mod)
            pfx, name = mod.rsplit(".", 1) if "." in mod else ("", mod)
            pfx = os.path.join(modname.replace(".", "_"), pfx.replace(".", "/"))
        else:
            name = mod.replace(".", "_")
            pfx = ""

        filename = f"test_{name}.py"

        fullpath = os.path.join(output, pfx, filename)

        makefile(fullpath)

        _module = load_module_from_pyfile(f"test_{name}", fullpath)

        try:
            source = inspect.getsource(_module)
            click.secho("loading existing codes from ", nl=False, fg="bright_white")
            click.secho(f"{fullpath}", fg="bright_green")
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

                # print(f"Add test function for {fullname}")

                click.secho("adding test function: ", nl=False, fg="bright_white")
                click.secho(f"{fullname}\r", nl=False, fg="bright_cyan")

            elif isinstance(obj, type):

                ut_name = f"Test{name}"

                if ut_name not in implemented:
                    blocks.append(
                        CodeBlock(
                            raw=populate_testclass(obj), name=ut_name, kind="class"
                        )
                    )

                    code_added += 1

                    # print(f"Add test class for {fullname}")
                    click.secho("adding test class: ", nl=False, fg="bright_white")
                    click.secho(f"{fullname}\r", nl=False, fg="bright_cyan")

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

                            click.secho(
                                "adding test method: ", nl=False, fg="bright_white"
                            )
                            click.secho(f"{fullname}\r", nl=False, fg="bright_cyan")

                    if methods_to_add:

                        code = "\n".join([block.raw] + methods_to_add)

                        blocks[implemented[ut_name]] = CodeBlock(
                            raw=code, kind="class", name=ut_name
                        )

                        code_added += 1

            time.sleep(0.01)

        if code_added > 0:
            click.echo()
            new_source = "\n".join([b.raw for b in blocks])
            formatted = isorting(blacking(new_source))

            makefile(fullpath, formatted, overwrite=True)
            click.secho("writing codes to ", nl=False, fg="bright_white")
            click.secho(f"{fullpath}", fg="bright_green")

        else:
            click.secho("all templates populated, skip", fg="bright_black")

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
