# TestGen
Auto generate unit test templates based on source code

## Install

```
$ pip install testgen
```


## Basic Usage

Assume you have a package, and its layout:

```
my_awesome_package
├── __init__.py
└── module1.py
```

some codes inside `my_awesome_package/module1.py`:

```python

import sys

MY_CONST = 123

def funcion1():
    pass


def function2():
    pass


class MyObject:
    def method1(self):
        pass

    @classmethod
    def classmethod1(cls):
        pass

    @staticmethod
    def staticmethod1():
        pass

```

We can generate unit testing templates for all implementations by just one line:

```
$ testgen -m my_awesome_package -o mytests
```

The output layout:

```
mytests
├── __init__.py
└── my_awesome_package
    ├── __init__.py
    └── test_module1.py

```

The testing templates inside `test_module1.py`

```python
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

```

Each module maps to a testing module(`module1.py --> test_module1.py`), and each function, each class and all methods inside that class maps to corresponding testing templates. 

- `testgen` will skip code generation if the testing templates for the functions already exist.
- `testgen` won't delete the corresponding testing templates if the source codes get deleted or renamed.
-  For new added codes: modules, functions or methods inside class, just re-run `testgen` to generate new testing templates for them.
