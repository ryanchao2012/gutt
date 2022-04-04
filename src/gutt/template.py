from typing import List as LIST

import attr
from asttrs import (
    AST,
    Assert,
    ClassDef,
    Constant,
    FunctionDef,
    ImportFrom,
    Load,
    Name,
    Pass,
    alias,
    arg,
    arguments,
    stmt,
)

from gutt.model import Code

from .utils import load_module_by_name


class Layout:

    prefix = "Test"
    ref = AST

    def __init__(self, src: Code):

        self._src = src

    def build(self) -> AST:

        fields = {f.name for f in attr.fields(self.ref)}

        params = {fd: getattr(self, fd) for fd in fields if hasattr(self, fd)}

        return self.ref(**params)


class FunctionLayout(Layout):

    prefix = "test_"
    ref = FunctionDef

    @property
    def name(self):
        return f"{self.prefix}{self._src.ast.name}"

    @property
    def args(self):
        return arguments()

    @property
    def body(self):
        return [
            ImportFrom(
                module=self._src.module.name, names=[alias(name=self._src.ast.name)]
            ),
            Pass(),
        ]


class MethodLayout(FunctionLayout):
    @property
    def body(self):
        return [Pass()]

    @property
    def args(self):
        return arguments(args=[arg(arg="self")])


class ClassLayout(Layout):

    prefix = "Test"
    ref = ClassDef
    method_layout = MethodLayout

    @property
    def setups_teardowns(self):
        cls_args = arguments(args=[arg(arg="cls")])
        cls_deco = Name(id="classmethod", ctx=Load())

        setup_class = FunctionDef(
            name="setup_class",
            body=[
                ImportFrom(
                    module=self._src.module.name,
                    names=[alias(name=self._src.ast.name)],
                    level=0,
                ),
                Assert(test=Name(id=self._src.ast.name, ctx=Load())),
            ],
            args=cls_args,
            decorator_list=[cls_deco],
        )
        teardown_class = FunctionDef(
            name="teardown_class",
            args=cls_args,
            body=[Pass()],
            decorator_list=[cls_deco],
        )

        self_args = arguments(args=[arg(arg="self"), arg(arg="method")])

        setup_method = FunctionDef(name="setup_method", args=self_args, body=[Pass()])
        teardown_method = FunctionDef(
            name="teardown_method", args=self_args, body=[Pass()]
        )

        return [setup_class, teardown_class, setup_method, teardown_method]

    @property
    def methods(self):
        methods = []
        for m in self._src.ast.body:
            if (isinstance(m, FunctionDef)) and (not m.name.startswith("__")):
                methods.append(self.method_layout(self._src.evolve(ast=m)).build())

        return methods

    @property
    def name(self) -> str:
        return f"{self.prefix}{self._src.ast.name}"

    @property
    def body(self) -> LIST[stmt]:
        return self.setups_teardowns + self.methods


class Template:

    class_layout = ClassLayout
    function_layout = FunctionLayout

    @classmethod
    def load(cls, name: str):

        modname, qname = name.rsplit(".", 1)

        mod = load_module_by_name(modname)

        return getattr(mod, qname)


class AssertFalseFunctionLayout(FunctionLayout):
    @property
    def body(self):
        return [
            ImportFrom(
                module=self._src.module.name,
                names=[alias(name=self._src.ast.name)],
                level=0,
            ),
            Assert(test=Constant(value=False)),
        ]


class AssertSelfFunctionLayout(FunctionLayout):
    @property
    def body(self):
        return [
            ImportFrom(
                module=self._src.module.name,
                names=[alias(name=self._src.ast.name)],
                level=0,
            ),
            Assert(test=Name(id=self._src.ast.name, ctx=Load())),
        ]


class AssertFalseMethodLayout(MethodLayout):
    @property
    def body(self):
        return [Assert(test=Constant(value=False))]


class AssertFalseClassLayout(ClassLayout):

    method_layout = AssertFalseMethodLayout


class AssertFalseTemplate(Template):

    function_layout = AssertFalseFunctionLayout
    class_layout = AssertFalseClassLayout


class AssertSelfTemplate(Template):
    function_layout = AssertSelfFunctionLayout


PassTemplate = Template
