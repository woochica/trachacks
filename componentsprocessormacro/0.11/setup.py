#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

VERSION = '0.11'
PACKAGE = 'componentsprocessor'

setup(
    name='ComponentsProcessorMacro',
    version=VERSION,
    description="Lists components based on a name.",
    url='http://trac-hacks.org/wiki/ComponentsProcessorMacro',
    author='Terry Brown',
    author_email='terry_n_brown@yahoo.com',
    keywords='trac plugin',
    license="?",
    packages=[PACKAGE],
    include_package_data=True,
    package_data={},
    install_requires=[],
    zip_safe=False,
    entry_points={
        'trac.plugins': '%s = %s.macro' % (PACKAGE, PACKAGE),
    },
)
