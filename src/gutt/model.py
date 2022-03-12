import os
import re
from importlib.util import find_spec
from pathlib import Path
from typing import Generator, Optional, Union

from asttrs import ClassDef, FunctionDef, Lambda, Serializable, immutable

from .utils import catch_module_from_sys


@immutable
class ModuleIO(Serializable):
    name: str
    outdir: str
    src: str
    dst: str

    @classmethod
    def from_name(
        cls, modname: str, outdir: str, head: str = None
    ) -> Optional["ModuleIO"]:

        with catch_module_from_sys(modname):
            try:
                spec = find_spec(modname)
            except Exception:
                return None

        if (spec is None) or (spec.origin is None) or (not os.path.isfile(spec.origin)):
            return None

        outdir = os.path.normpath(outdir)
        head = head or modname

        src = spec.origin
        if src.endswith("__init__.py"):
            pfx = modname
            base = "__init__"
        else:
            pfx, base = modname.rsplit(".", 1) if "." in modname else ("", modname)

        pfx = re.sub(rf"^{head}\.?", "", pfx)

        dst = os.path.join(
            outdir,
            head.replace(".", "_"),
            pfx.replace(".", os.path.sep),
            f"test_{base}.py",
        )

        return cls(name=modname, outdir=outdir, src=src, dst=dst)

    @property
    def submodules(self) -> Generator["ModuleIO", None, None]:
        if self.ispkg:
            prefix = os.path.dirname(self.src)

            for p in Path(prefix).glob("**/*.py"):

                path = str(p)
                if path.endswith("__init__.py"):
                    path = os.path.dirname(path)

                suffix = re.sub(rf"^{prefix}", "", path)
                sub = os.path.splitext(suffix)[0]

                name = self.name + sub.replace(os.path.sep, ".")

                mod = self.from_name(name, self.outdir, head=self.name)

                if mod:
                    yield mod

        else:

            yield self

    @property
    def ispkg(self):

        return self.src.endswith("__init__.py")


@immutable
class Code(Serializable):
    module: Optional[ModuleIO] = None
    ast: Union[FunctionDef, Lambda, ClassDef]
