import re
from typing import List

import attr

from .parser import split_source_into_blocks

immutable = attr.s(auto_attribs=True, slots=True, frozen=True, kw_only=True)


def unindent(code: str, level: int = 0, spacing: int = 4) -> str:
    return re.sub(rf"^ {{0,{level * spacing}}}", "", code, flags=re.MULTILINE)


def indent(code: str, level: int = 0, spacing: int = 4) -> str:
    return re.sub(r"^", " " * spacing * level, code, flags=re.MULTILINE)


@immutable
class CodeBlock:
    raw: str
    kind: str = "other"  # NOTE: def, class or other
    name: str = None

    @classmethod
    def collect_from_source(cls, code: str) -> List["CodeBlock"]:

        pat = re.compile(r"^(?P<kind>def|class) (?P<name>\w+)")

        blocks = []
        for bk in split_source_into_blocks(code):

            m = re.match(pat, bk)
            data = m.groupdict() if m else {}

            blocks.append(cls(raw=bk, **data))

        return blocks

    @property
    def children(self, spacing: int = 4) -> List["CodeBlock"]:
        if self.kind != "class":
            return []

        else:
            newline_idx = self.raw.find("\n")

            return self.collect_from_source(
                unindent(
                    self.raw[newline_idx + 1 :], level=1, spacing=spacing  # NOQA: E203
                )
            )
