#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='FieldTooltip',
    version='0.5',
    license="""Modified BSD, except including libraries follows:
    - jQuery clueTip Plugin: the MIT License
     - hoverIntent jQuery Plug-in: the MIT or GPL License
    - jQuery Tools - Tooltip: "NO COPYRIGHTS OR LICENSES. DO WHAT YOU LIKE."
    - PowerTip: the MIT license
    - jQuery plugin: Tooltip: the MIT or GPL License
    """,
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/FieldTooltipPlugin',
    description='tooltip help for ticket fields',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    package_data={
        'fieldtooltip': ['htdocs/*/*']
        },
    entry_points={
        'trac.plugins': 'FieldTooltip = fieldtooltip'
        },
    )
