#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2013 Joao Alexandre de Toledo <tracrelease@toledosp.com.br>
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup


setup(name='TracReleasePlugin',
        version='0.2',
        packages = ['tracrelease', 'tracrelease.db'],
        description="Release Control",
        author='Joao Alexandre de Toledo',
        author_email='tracrelease@toledosp.com.br',
        url='http://trac-hacks.org/wiki/TracReleasePlugin',
        keywords='trac plugin',
        license="BSD 3-Clause",
        packages=['tracrelease', 'tracrelease.db'],
        package_data={'tracrelease' : ['templates/*.html', 'htdocs/*']},
        include_package_data=True,
        zip_safe=False,
        install_requires = [''],
        entry_points = {
            'trac.plugins': [
                'TracRelease.core = tracrelease.core',
                'TracRelease.setup = tracrelease.init'
            ]
        },
    )