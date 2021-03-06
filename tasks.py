import configparser
import os

from invoke import task

import gutt

PACKAGE_NAME = gutt.__name__
PACKAGE_VERSION = gutt.__version__


@task(
    help=dict(
        tomlfile="Iput config file to load, default: pyproject.toml",
        metafile=f"Output python file to write meta data, default: src/{PACKAGE_NAME}/_meta.py",
    )
)
def sync_meta(c, tomlfile=None, metafile=None):
    """Sync project metadata with pyproject.toml"""

    project_root = os.path.dirname(__file__)

    tomlfile = tomlfile or os.path.join(project_root, "pyproject.toml")
    parser = configparser.ConfigParser()
    parser.read(tomlfile)

    meta: dict = parser._sections["tool.poetry"]
    metafile = metafile or os.path.join(project_root, "src", PACKAGE_NAME, "_meta.py")

    header = '# NOTE: This file is auto-generated by "inv sync_meta"\n\n'
    content = header + "\n".join(f"{k} = {v}" for k, v in meta.items()) + "\n"

    with open(metafile, "w") as f:
        f.write(content)
