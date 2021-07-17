import importlib
import re
from types import ModuleType
from typing import Generator


def load_module_from_pyfile(modname: str, fullpath: str) -> ModuleType:

    spec = importlib.util.spec_from_file_location(modname, fullpath)

    return spec.loader.load_module(modname)


def split_source_into_blocks(source: str) -> Generator[str, None, None]:
    head_index = 0

    pat = re.compile(r"(?=^)[^\s#\'\"\)]+", re.MULTILINE)

    for m in re.finditer(pat, source):
        if m.start() > head_index:
            yield source[head_index : m.start()]  # NOQA: E203

        head_index = m.start()

    yield source[head_index:]
