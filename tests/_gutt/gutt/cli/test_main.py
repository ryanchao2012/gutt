class TestInvalidModule:
    @classmethod
    def setup_class(cls):
        from gutt.cli.main import InvalidModule

        assert InvalidModule

    @classmethod
    def teardown_class(cls):
        pass

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass


def test_print_version():
    from gutt.cli.main import print_version

    assert print_version


def test_main():
    from gutt.cli.main import main

    assert main
