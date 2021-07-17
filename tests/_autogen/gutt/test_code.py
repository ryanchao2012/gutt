class TestCodeBlock:
    @classmethod
    def setup_class(cls):
        from gutt.code import CodeBlock

        assert CodeBlock

    @classmethod
    def teardown_class(cls):
        pass

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    def test_collect_from_source(self):
        pass


def test_indent():
    from gutt.code import indent

    assert indent


def test_unindent():
    from gutt.code import unindent

    assert unindent
