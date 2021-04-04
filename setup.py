
# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

readme = ''

setup(
    long_description=readme,
    name='testgen',
    version='0.1.1',
    description='Auto generate templates for unit tests based on source code',
    python_requires='==3.*,>=3.7.0',
    author='ryanchao2012',
    author_email='ryanchao2012@gmail.com',
    license='MIT',
    entry_points={"console_scripts": ["testgen = testgen.cli.main:main"]},
    packages=['testgen', 'testgen.cli'],
    package_dir={"": "."},
    package_data={},
    install_requires=['click==7.*,>=7.1.2'],
)