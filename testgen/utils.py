import importlib
import inspect
import pathlib
import pkgutil
import subprocess as sp
import tempfile
from importlib._bootstrap_external import SourceFileLoader
from types import FunctionType, ModuleType
from typing import List, Union


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


def collect_classes_and_functions_from_module(
    modname: str,
) -> List[Union[FunctionType, type]]:

    cached = set()
    loader: SourceFileLoader = pkgutil.get_loader(modname)
    module = loader.load_module(modname)

    for finder, name, ispkg in pkgutil.walk_packages(
        module.__path__, module.__name__ + "."
    ):
        mod = finder.find_module(name).load_module(name)

        for name, obj in mod.__dict__.items():
            if (
                isinstance(obj, (type, FunctionType))
                and obj.__module__.startswith(modname)
                and (qualname(obj) not in cached)
            ):

                cached.add(qualname(obj))

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
