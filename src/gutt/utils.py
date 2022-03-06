import os
import pathlib
import pkgutil
import subprocess as sp
import sys
import tempfile
from contextlib import contextmanager
from importlib._bootstrap_external import SourceFileLoader
from types import ModuleType
from typing import Union


def load_module_by_name(modname: str) -> ModuleType:
    loader: SourceFileLoader = pkgutil.get_loader(modname)
    return loader.load_module(modname)


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


@contextmanager
def catch_module_from_sys(modname: str):

    m = sys.modules.pop(modname, None)

    yield

    if m is not None:
        sys.modules[modname] = m


def populate_init(folder: str):

    root = pathlib.Path(folder)
    paths = {root}

    for path in root.glob("**/*.py"):
        if path.name == "__init__.py":
            continue

        parent = path.parent

        while parent > root:

            if not parent.joinpath("__init__.py").exists():
                paths.add(parent)

            parent = parent.parent

    for p in paths:
        makefile(os.path.join(str(p), "__init__.py"))
