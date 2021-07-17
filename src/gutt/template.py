import inspect
from types import FunctionType

from .code import indent


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
            inspect.ismethod(v)
            or isinstance(v, (FunctionType, classmethod, staticmethod))
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
