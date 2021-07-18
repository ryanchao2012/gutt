![](https://github.com/ryanchao2012/gutt/actions/workflows/gutt-run-unittests.yml/badge.svg)
![](https://img.shields.io/pypi/v/gutt.svg)
![](https://img.shields.io/pypi/pyversions/gutt)
![](https://img.shields.io/github/license/ryanchao2012/gutt)

# gutt
Auto Generate Unit Test Templates


## Install

```
$ pip install gutt
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

`gutt` can generate unit testing templates for all implementations in just one line:

```
$ gutt -m my_awesome_package -o mytests
```

The output layout:

```
mytests
├── __init__.py
└── my_awesome_package
    ├── __init__.py
    └── test_module1.py

```

The unit test templates inside `test_module1.py`

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

Each module in source codes maps to a testing module(`module1.py --> test_module1.py`), and each function, each class and all methods inside that class maps to corresponding test templates. 

- `gutt` will skip code generation if the test templates for the functions already exist.
- `gutt` won't delete the corresponding test templates if the source codes get deleted or renamed.
- For new added codes: modules, functions or methods inside class, just re-run `gutt` to generate new test templates for them.


Run unit test with `pytest`, for example:

```
$ pytest --doctest-modules --cov=my_awesome_package mytests

=============================== test session starts ===============================
platform linux -- Python 3.8.8, pytest-4.6.11, py-1.10.0, pluggy-0.13.1
rootdir: /home/ryan/Workspace/my_awesome_package
plugins: mock-1.13.0, cov-2.11.1
collected 5 items                                                                 

mytests/my_awesome_package/test_module1.py .....                            [100%]

----------- coverage: platform linux, python 3.8.8-final-0 -----------
Name                             Stmts   Miss  Cover
----------------------------------------------------
my_awesome_package/__init__.py       0      0   100%
my_awesome_package/module1.py       13      5    62%
----------------------------------------------------
TOTAL                               13      5    62%


============================ 5 passed in 0.07 seconds =============================
```