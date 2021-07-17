import os
import pathlib
import pkgutil
import subprocess as sp
import sys
import tempfile
from contextlib import contextmanager
from importlib._bootstrap_external import SourceFileLoader
from itertools import tee
from types import FunctionType, ModuleType
from typing import Generator, Union


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""

    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def qualname(obj: Union[FunctionType, ModuleType, type], level: int = -1) -> str:
    """Return the qualname of a class, a function or a module.

    >>> class Foo:
    ...     pass

    >>> def bar():
    ...     pass

    >>> qualname(Foo)
    'gutt.utils.Foo'

    >>> qualname(bar)
    'gutt.utils.bar'
    """

    if isinstance(obj, FunctionType) or isinstance(obj, type):
        name = f"{obj.__module__}.{obj.__qualname__}"

    elif isinstance(obj, ModuleType):
        name = f"{obj.__name__}"

    else:
        name = ""

    return ".".join(name.split(".")[-level:]) if level > 0 else name


def load_module_by_name(modname: str) -> ModuleType:
    loader: SourceFileLoader = pkgutil.get_loader(modname)
    return loader.load_module(modname)


def collect_classes_and_functions(
    module: ModuleType,
) -> Generator[Union[FunctionType, type], None, None]:

    modname = qualname(module)
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

    for obj in _collect_from_module(package):
        yield obj

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


def blacking(source_code: str):

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


def isorting(source_code: str):

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(source_code)
        fname = f.name

    p = sp.Popen(f"cat {fname}".split(), stdout=sp.PIPE)

    out = sp.check_output("isort -q -".split(), stdin=p.stdout)

    p.wait()

    try:
        pathlib.Path(fname).unlink()
    except FileNotFoundError:
        pass

    return out.decode()


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


def _writefile(fullpath: str, content: Union[str, bytes] = ""):

    if not isinstance(content, (str, bytes)):
        raise TypeError(f"content must be str or bytes, got: {type(content)}")

    with open(fullpath, "wb" if isinstance(content, bytes) else "w") as f:
        f.write(content)
