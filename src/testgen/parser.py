import importlib
import re
from types import ModuleType
from typing import List


def load_module_from_pyfile(modname: str, fullpath: str) -> ModuleType:

    spec = importlib.util.spec_from_file_location(modname, fullpath)

    return spec.loader.load_module(modname)


def split_source_into_blocks(source: str) -> List[str]:
    head_index = 0
    blocks = []

    pat = re.compile(r"(?=^)[^\s#\'\"]+", re.MULTILINE)

    for m in re.finditer(pat, source):
        if m.start() > head_index:
            blocks.append(source[head_index : m.start()])  # NOQA: E203
        head_index = m.start()

    blocks.append(source[head_index:])

    return blocks
