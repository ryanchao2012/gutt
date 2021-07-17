def test_collect_classes_and_functions():
    from gutt.utils import collect_classes_and_functions

    assert collect_classes_and_functions


def test_expand_sys_path():
    from gutt.utils import expand_sys_path

    assert expand_sys_path


def test_load_module_by_name():
    from gutt.utils import load_module_by_name

    assert load_module_by_name


def test_makefile():
    from gutt.utils import makefile

    assert makefile


def test_qualname():
    from gutt.utils import qualname

    assert qualname


def test_pairwise():
    from gutt.utils import pairwise

    assert pairwise


def test__collect_from_package():
    from gutt.utils import _collect_from_package

    assert _collect_from_package


def test__collect_from_module():
    from gutt.utils import _collect_from_module

    assert _collect_from_module


def test__writefile():
    from gutt.utils import _writefile

    assert _writefile


def test_blacking():
    from gutt.utils import blacking

    assert blacking


def test_isorting():
    from gutt.utils import isorting

    assert isorting


def test_escape_any_commandline_parser():
    from gutt.utils import escape_any_commandline_parser

    assert escape_any_commandline_parser
