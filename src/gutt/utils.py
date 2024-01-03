import json
import os
import pathlib
import pkgutil
import subprocess as sp
import sys
import tempfile
from contextlib import contextmanager
from importlib._bootstrap_external import SourceFileLoader
from types import ModuleType
from typing import Dict, Union

import attr
import cattr

immutable = attr.s(auto_attribs=True, slots=True, frozen=True, kw_only=True)


@immutable
class Serializable:
    def to_dict(self, recurse=True, **kwargs):
        return attr.asdict(self, recurse=recurse, **kwargs)

    @classmethod
    def from_dict(cls, data: Dict):
        return cattr.structure_attrs_fromdict(data, cls)

    @classmethod
    def from_json(cls, json_str: str):
        return cls.from_dict(json.loads(json_str))

    def to_json(self, ensure_ascii=False, **kwargs):
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, **kwargs)

    def evolve(self, **kwargs):
        return attr.evolve(self, **kwargs)

    def mutate_from_other(self, other: "Serializable", excludes=[]):
        self_fields = [f2.name for f2 in attr.fields(self.__class__)]

        valid_fields = [
            f1.name
            for f1 in attr.fields(other.__class__)
            if (getattr(other, f1.name, None) is not None)
            and (f1.name not in excludes)
            and (f1.name in self_fields)
        ]

        data = other.to_dict(filter=lambda att, value: att.name in valid_fields)

        return self.evolve(**data)


def load_module_by_name(modname: str) -> ModuleType:
    loader: SourceFileLoader = pkgutil.get_loader(modname)
    return loader.load_module(modname)


def blacking(source_code: str):
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(source_code)
        fname = f.name

    p = sp.Popen(["cat", fname], stdout=sp.PIPE)

    out = sp.check_output([sys.executable, "-m", "black", "-q", "-"], stdin=p.stdout)

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

    p = sp.Popen(["cat", fname], stdout=sp.PIPE)

    out = sp.check_output([sys.executable, "-m", "isort", "-q", "-"], stdin=p.stdout)

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
