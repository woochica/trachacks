#!/usr/bin/env python# -*- coding: utf-8 -*-from setuptools import find_packages, setupsetup(    name = 'Tracbacks',    version = '0.1',    packages = find_packages(exclude=['*.tests*']),    url = "http://trac-hacks.org/wiki/TracBacksPlugin",    license = 'GPLv3+',    entry_points = """        [trac.plugins]        tracbacks = tracbacks    """,)