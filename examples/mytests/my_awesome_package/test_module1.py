def test_funcion1():
    from my_awesome_package.module1 import funcion1

    assert funcion1


def test_function2():
    from my_awesome_package.module1 import function2

    assert function2


class TestMyObject:
    @classmethod
    def setup_class(cls):
        from my_awesome_package.module1 import MyObject

        assert MyObject

    @classmethod
    def teardown_class(cls):
        pass

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    def test_method1(self):
        pass

    def test_classmethod1(self):
        pass

    def test_staticmethod1(self):
        pass
