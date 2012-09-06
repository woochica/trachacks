#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name='Lineno', version='1.1',
    author = 'Adamansky Anton',
    author_email = 'anton@adamansky.com',
    description = 'Prints line numbered code listings',
    license = 'Apache License, Version 2.0',
    url = 'http://trac-hacks.org/wiki/LinenoMacro',
    packages=['lineno'],
    package_data={ 'lineno' : [ 'htdocs/css/*.css' ] },
    entry_points = """
        [trac.plugins]
        lineno = lineno.LinenoMacro
    """,
)
