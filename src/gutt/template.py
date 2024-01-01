import dataclasses
from typing import List as LIST

from libcst import (
    Assert,
    BaseSuite,
    ClassDef,
    CSTNode,
    Decorator,
    FunctionDef,
    ImportAlias,
    ImportFrom,
    IndentedBlock,
    Name,
    Param,
    Parameters,
    Pass,
    SimpleStatementLine,
    parse_expression,
)

from .model import Code
from .utils import load_module_by_name


class Layout:
    """TODO: What is this"""

    prefix = "Test"
    ref = CSTNode

    def __init__(self, code: Code):
        self._code = code

    def build(self) -> CSTNode:
        fields = {f.name for f in dataclasses.fields(self.ref)}

        params = {fd: getattr(self, fd) for fd in fields if hasattr(self, fd)}

        return self.ref(**params)


class FunctionLayout(Layout):
    prefix = "test_"
    ref = FunctionDef

    @property
    def name(self) -> Name:
        return Name(value=f"{self.prefix}{self._code.cst.name.value}")

    @property
    def params(self) -> Parameters:
        return Parameters()

    @property
    def body(self) -> BaseSuite:
        return IndentedBlock(
            body=[
                SimpleStatementLine(
                    body=[
                        ImportFrom(
                            module=parse_expression(self._code.module.name),
                            names=[
                                ImportAlias(name=Name(value=self._code.cst.name.value))
                            ],
                        )
                    ]
                ),
                SimpleStatementLine(body=[Pass()]),
            ]
        )


class MethodLayout(FunctionLayout):
    @property
    def body(self) -> BaseSuite:
        return IndentedBlock(body=[SimpleStatementLine(body=[Pass()])])

    @property
    def params(self) -> Parameters:
        return Parameters(params=[Param(Name(value="self"))])


class ClassLayout(Layout):
    prefix = "Test"
    ref = ClassDef
    method_layout = MethodLayout

    @property
    def setups_teardowns(self) -> LIST[FunctionDef]:
        """TODO: what is this"""

        cls_params = Parameters(params=[Param(Name(value="cls"))])
        cls_deco = Decorator(decorator=Name(value="classmethod"))
        setup_class = FunctionDef(
            name=Name(value="setup_class"),
            body=IndentedBlock(
                body=[
                    SimpleStatementLine(
                        body=[
                            ImportFrom(
                                module=parse_expression(self._code.module.name),
                                names=[
                                    ImportAlias(
                                        name=Name(value=self._code.cst.name.value)
                                    )
                                ],
                            )
                        ]
                    ),
                    SimpleStatementLine(
                        body=[
                            Assert(test=Name(value=self._code.cst.name.value)),
                        ]
                    ),
                ]
            ),
            params=cls_params,
            decorators=[cls_deco],
        )

        teardown_class = FunctionDef(
            name=Name(value="teardown_class"),
            params=cls_params,
            body=IndentedBlock(body=[SimpleStatementLine(body=[Pass()])]),
            decorators=[cls_deco],
        )

        self_params = Parameters(
            params=[Param(Name(value="self")), Param(Name(value="method"))]
        )

        setup_method = FunctionDef(
            name=Name(value="setup_method"),
            params=self_params,
            body=IndentedBlock(body=[SimpleStatementLine(body=[Pass()])]),
        )

        teardown_method = FunctionDef(
            name=Name(value="teardown_method"),
            params=self_params,
            body=IndentedBlock(body=[SimpleStatementLine(body=[Pass()])]),
        )

        return [setup_class, teardown_class, setup_method, teardown_method]

    @property
    def methods(self) -> LIST[FunctionDef]:
        methods = []
        for stmt in self._code.cst.body.body:
            if (isinstance(stmt, FunctionDef)) and (
                not stmt.name.value.startswith("__")
            ):
                methods.append(self.method_layout(self._code.evolve(cst=stmt)).build())

        return methods

    @property
    def name(self) -> Name:
        return Name(value=f"{self.prefix}{self._code.cst.name.value}")

    @property
    def body(self) -> BaseSuite:
        return IndentedBlock(body=self.setups_teardowns + self.methods)


class Template:
    """TODO: what"""

    class_layout = ClassLayout
    function_layout = FunctionLayout

    @classmethod
    def load(cls, name: str) -> "Template":
        """TODO: what?"""

        modname, qname = name.rsplit(".", 1)

        mod = load_module_by_name(modname)

        return getattr(mod, qname)


class AssertFalseFunctionLayout(FunctionLayout):
    @property
    def body(self) -> BaseSuite:
        return IndentedBlock(
            body=[
                SimpleStatementLine(
                    body=[
                        ImportFrom(
                            module=parse_expression(self._code.module.name),
                            names=[
                                ImportAlias(name=Name(value=self._code.cst.name.value))
                            ],
                        )
                    ]
                ),
                SimpleStatementLine(
                    body=[
                        Assert(test=Name(value="False")),
                    ]
                ),
            ]
        )


class AssertSelfFunctionLayout(FunctionLayout):
    @property
    def body(self) -> BaseSuite:
        return IndentedBlock(
            body=[
                SimpleStatementLine(
                    body=[
                        ImportFrom(
                            module=parse_expression(self._code.module.name),
                            names=[
                                ImportAlias(name=Name(value=self._code.cst.name.value))
                            ],
                        )
                    ]
                ),
                SimpleStatementLine(
                    body=[
                        Assert(test=Name(value=self._code.cst.name.value)),
                    ]
                ),
            ]
        )


class AssertFalseMethodLayout(MethodLayout):
    @property
    def body(self):
        return IndentedBlock(
            body=[SimpleStatementLine(body[Assert(test=Name(value="False"))])]
        )


class AssertFalseClassLayout(ClassLayout):
    method_layout = AssertFalseMethodLayout


class AssertFalseTemplate(Template):
    function_layout = AssertFalseFunctionLayout
    class_layout = AssertFalseClassLayout


class AssertSelfTemplate(Template):
    function_layout = AssertSelfFunctionLayout


PassTemplate = Template
