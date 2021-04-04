import importlib
import inspect
import os
import pathlib
import pkgutil
import subprocess as sp
import sys
import tempfile
from contextlib import contextmanager
from importlib._bootstrap_external import SourceFileLoader
from types import FunctionType, ModuleType
from typing import Generator, Union


def qualname(obj: Union[FunctionType, ModuleType, type], level: int = -1) -> str:
    """Return the qualname of a class, a function or a module.

    >>> class Foo:
    ...     pass

    >>> def bar():
    ...     pass

    >>> qualname(Foo)
    'testgen.utils.Foo'

    >>> qualname(bar)
    'testgen.utils.bar'
    """

    if isinstance(obj, FunctionType) or isinstance(obj, type):
        name = f"{obj.__module__}.{obj.__qualname__}"

    elif isinstance(obj, ModuleType):
        name = f"{obj.__name__}"

    else:
        name = ""

    return ".".join(name.split(".")[-level:]) if level > 0 else name


def collect_classes_and_functions(
    modname: str,
) -> Generator[Union[FunctionType, type], None, None]:

    loader: SourceFileLoader = pkgutil.get_loader(modname)
    module = loader.load_module(modname)

    cached = set()

    impls = (
        _collect_from_package(module)
        if hasattr(
            module, "__path__"
        )  # By definition, if a module has a __path__ attribute, it is a package.
        else _collect_from_module(module)
    )

    for obj in impls:
        name = qualname(obj)
        if obj.__module__.startswith(modname) and (name not in cached):
            cached.add(name)
            yield obj


def _collect_from_package(
    package: ModuleType,
) -> Generator[Union[FunctionType, type], None, None]:

    for finder, name, _ in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        mod = finder.find_module(name).load_module(name)

        for obj in _collect_from_module(mod):
            yield obj


def _collect_from_module(
    module: ModuleType,
) -> Generator[Union[FunctionType, type], None, None]:
    for _, obj in module.__dict__.items():
        if isinstance(obj, (type, FunctionType)):

            yield obj


def blacken(source_code: str):

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(source_code)
        fname = f.name

    p = sp.Popen(f"cat {fname}".split(), stdout=sp.PIPE)

    out = sp.check_output("black -q -".split(), stdin=p.stdout)

    p.wait()

    try:
        pathlib.Path(fname).unlink()
    except FileNotFoundError:
        pass

    return out.decode()


def load_module_from_pyfile(modname: str, fullpath: str) -> ModuleType:

    spec = importlib.util.spec_from_file_location(modname, fullpath)

    return spec.loader.load_module(modname)


def indent(code: str, level=0, spacing=4) -> str:
    return " " * spacing * level + code


def populate_testclass(cls: type) -> str:
    """"""

    module = cls.__module__
    name = cls.__name__
    skeleton = [
        f"class Test{name}:",
        "",
        indent("@classmethod", level=1),
        indent("def setup_class(cls):", level=1),
        indent(f"from {module} import {name}", level=2),
        indent(f"assert {name}", level=2),
        "",
        indent("@classmethod", level=1),
        indent("def teardown_class(cls):", level=1),
        indent("pass", level=2),
        "",
        indent("def setup_method(self, method):", level=1),
        indent("pass", level=2),
        "",
        indent("def teardown_method(self, method):", level=1),
        indent("pass", level=2),
        "",
    ]

    for k, v in cls.__dict__.items():
        if (
            inspect.ismethod(v) or isinstance(v, (FunctionType, classmethod))
        ) and not k.startswith("__"):
            skeleton.extend(
                [indent(f"def test_{k}(self):", level=1), indent("pass", level=2), ""]
            )

    return "\n".join(skeleton)


def populate_testfunc(func: FunctionType) -> str:

    module = func.__module__
    name = func.__name__
    skeleton = [
        f"def test_{name}():",
        indent(f"from {module} import {name}", level=1),
        "",
        indent(f"assert {name}", level=1),
    ]

    return "\n".join(skeleton)


@contextmanager
def expand_sys_path(*paths: str):

    num = len(paths)

    for p in paths[::-1]:
        if p and isinstance(p, str):

            sys.path.insert(0, p)

    yield

    for _ in range(num):
        sys.path.pop(0)


def makefile(fullpath: str, content: Union[str, bytes] = "", overwrite: bool = False):

    if not os.path.isfile(fullpath):

        dirpath = os.path.dirname(fullpath)

        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)

        _writefile(fullpath, content)

    elif overwrite:

        _writefile(fullpath, content)


def _writefile(
    fullpath: str,
    content: Union[str, bytes] = "",
):

    if not isinstance(content, (str, bytes)):
        raise TypeError(f"content must be str or bytes, got: {type(content)}")

    with open(fullpath, "wb" if isinstance(content, bytes) else "w") as f:
        f.write(content)
