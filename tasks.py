import configparser
import os
import re

from invoke import task


@task(help=dict(tomlfile="Path of pyproject.toml"))
def sync_meta(c, tomlfile=None):
    """Sync project metadata with pyproject.toml"""

    project_root = os.path.dirname(__file__)

    tomlfile = tomlfile or os.path.join(project_root, "pyproject.toml")
    parser = configparser.ConfigParser()
    parser.read(tomlfile)
    version = re.sub(r"[\'\"]", "", parser.get("tool.poetry", "version"))
    name = re.sub(r"[\'\"]", "", parser.get("tool.poetry", "name"))
    versionfile = os.path.join(project_root, 'src', name, "_version.py")

    c.run(f"echo '__version__ = \"{version}\"' > {versionfile}")
