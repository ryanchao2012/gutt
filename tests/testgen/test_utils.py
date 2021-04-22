def test_blacken():
    from testgen.utils import blacken

    assert blacken


def test_collect_classes_and_functions():
    from testgen.utils import collect_classes_and_functions

    assert collect_classes_and_functions


def test_expand_sys_path():
    from testgen.utils import expand_sys_path

    assert expand_sys_path


def test_load_module_by_name():
    from testgen.utils import load_module_by_name

    assert load_module_by_name


def test_makefile():
    from testgen.utils import makefile

    assert makefile


def test_qualname():
    from testgen.utils import qualname

    assert qualname


def test_pairwise():
    from testgen.utils import pairwise

    assert pairwise


def test__collect_from_package():
    from testgen.utils import _collect_from_package

    assert _collect_from_package


def test__collect_from_module():
    from testgen.utils import _collect_from_module

    assert _collect_from_module


def test__writefile():
    from testgen.utils import _writefile

    assert _writefile
