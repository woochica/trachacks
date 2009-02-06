#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'Latex',
    version = '0.1',

    packages = ['latex'],
    include_package_data = True,

    install_requires = ['trac>=0.11'],

    author = "Jean-Guilhem Rouel",
    author_email = "jean-guilhem.rouel@ercim.org",
    description = "Latex support in wiki pages",
    long_description = "This macro renders Latex code in wiki pages as PNG images.",
    license = "GPLv2",
    keywords = "trac 0.11 latex macro",
    url = "http://trac-hacks.org/wiki/LatexMacro",

    entry_points = {
        'trac.plugins': [
            'latex.latexmacro = latex.latexmacro'
        ],
    },

    zip_safe = True
)
