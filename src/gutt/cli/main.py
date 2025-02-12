import dataclasses
import os
import re
from collections import OrderedDict

import click
import libcst
from libcst import ClassDef, FunctionDef, IndentedBlock, Module, SimpleStatementLine

from gutt.model import Code, ModuleIO
from gutt.template import Template as T
from gutt.utils import blacking, expand_sys_path, makefile, populate_init


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
    "--template-class",
    "-t",
    default="gutt.template.Template",
    help='Assign template class to generate test template, default: "gutt.template.Template".',
)
@click.option(
    "--dryrun",
    "-dr",
    is_flag=True,
    help="Run in dryrun mode.",
)
@click.option(
    "--flatten",
    is_flag=True,
    help="Flatten the nested structure of the test module to the single folder.",
)
def main(ctx, modname, path, exclude, output, template_class, dryrun, flatten):
    head = "" if flatten else modname.split(".")[0]
    with expand_sys_path(*path):
        module: ModuleIO = ModuleIO.from_name(modname, output, head)
        Template = T.load(template_class)

        if module is None:
            raise InvalidModule(modname)

        for mod in module.iter_submodules(head):
            code_added = 0

            if isinstance(exclude, str) and re.search(exclude, mod.name):
                click.secho("ignoring module: ", nl=False, fg="bright_white")
                click.secho(mod.name, fg="bright_black")
                continue

            try:
                with open(mod.src, "r") as f:
                    src_mod = libcst.parse_module(f.read())

            except Exception as error:
                msg = f'{type(error)}: {error}. src: "{mod.src}"'
                click.secho(msg, fg="bright_yellow")
                continue

            src_codes = OrderedDict()

            for el in src_mod.body:
                if not isinstance(el, (FunctionDef, ClassDef)):
                    continue

                qname = f"{mod.name}.{el.name.value}"

                if isinstance(exclude, str) and re.search(exclude, qname):
                    click.secho("excluding: ", nl=False, fg="bright_white")
                    click.secho(qname, fg="bright_black")

                    continue

                src_codes.update({qname: Code(module=mod, cst=el)})

                click.echo("\033[K", nl=False)
                click.secho("collecting: ", nl=False, fg="bright_white")
                click.secho(f"{qname}", fg="bright_cyan")

            if len(src_codes) == 0:
                continue

            try:
                with open(mod.dst, "r") as f:
                    test_mod = libcst.parse_module(f.read())

                # NOTE: let module's and class's body mutable
                test_mod = dataclasses.replace(test_mod, body=list(test_mod.body))
                for i, stmt in enumerate(test_mod.body):
                    if isinstance(stmt, ClassDef):
                        test_mod.body[i] = dataclasses.replace(
                            stmt,
                            body=dataclasses.replace(
                                stmt.body, body=list(stmt.body.body)
                            ),
                            # IndentedBlock(body=list(stmt.body.body))
                        )

                click.secho("loading: ", nl=False, fg="bright_white")
                click.secho(f"{mod.dst}", fg="bright_green")

            except FileNotFoundError:
                test_mod = Module(body=[])

            except Exception as error:
                msg = f'{type(error)}: {error}. dst: "{mod.dst}"'
                click.secho(msg, fg="bright_yellow")
                continue

            test_codes = OrderedDict()

            for i, el in enumerate(test_mod.body):
                if isinstance(el, (ClassDef, FunctionDef)):
                    test_pfx = (
                        Template.function_layout.prefix
                        if isinstance(el, FunctionDef)
                        else Template.class_layout.prefix
                    )

                    org_name = re.sub(rf"^{test_pfx}(.+)", r"\1", el.name.value)
                    key = f"{mod.name}.{org_name}"

                else:
                    key = f"#{i}"

                test_codes.update({key: Code(module=mod, cst=el)})

            for key, tcode in test_codes.items():
                if key not in src_codes:
                    continue

                scode = src_codes.pop(key)

                if not isinstance(scode.cst, ClassDef):
                    continue

                test_pfx = Template.class_layout.method_layout.prefix
                tmethods = OrderedDict()
                for j, el in enumerate(tcode.cst.body.body):
                    key = el.name.value if isinstance(el, FunctionDef) else f"#{j}"

                    tmethods.update({key: el})

                for el in scode.cst.body.body:
                    # TODO: allow private methods?
                    if (not isinstance(el, FunctionDef)) or el.name.value.startswith(
                        "__"
                    ):
                        continue

                    tname = f"{test_pfx}{el.name.value}"

                    if tname not in tmethods:
                        f: FunctionDef = Template.class_layout.method_layout(
                            Code(module=scode.module, cst=el)
                        ).build()

                        click.echo("\033[K", nl=False)
                        click.secho(
                            "adding method: ",
                            nl=False,
                            fg="bright_white",
                        )
                        click.secho(
                            f"{scode.cst.name.value}:{el.name.value}",
                            fg="bright_cyan",
                        )

                        tcode.cst.body.body.append(f)

                        code_added += 1

            for key, scode in src_codes.items():
                Layout = (
                    Template.function_layout
                    if isinstance(scode.cst, FunctionDef)
                    else Template.class_layout
                )

                what = "function" if isinstance(scode.cst, FunctionDef) else "class"

                obj = Layout(scode).build()
                click.echo("\033[K", nl=False)
                click.secho(f"adding {what}: ", nl=False, fg="bright_white")
                click.secho(f"{obj.name.value}", fg="bright_cyan")

                test_mod.body.append(obj)
                code_added += 1

            if code_added > 0:
                code = test_mod.code
                try:
                    source = blacking(code)
                except Exception as error:
                    msg = f'{type(error).__name__}: {error}. src: "{mod.src}"'
                    click.secho(msg, fg="bright_red")
                    click.secho(code, fg="bright_yellow")
                    continue

                if dryrun:
                    click.secho("(dryrun)", nl=False, fg="bright_yellow")
                    click.secho(f" writing: {mod.dst}", fg="bright_black")

                else:
                    makefile(mod.dst, source, overwrite=True)

                    click.secho("writing: ", nl=False, fg="bright_white")
                    click.secho(f"{mod.dst}", fg="bright_green")

            else:
                click.secho("all templates populated, skip.", fg="bright_black")

    populate_init(output)
